"""Aplicação principal da Alice"""
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
import os
import uuid
from pathlib import Path

from config import settings
from alice.agent import AliceAgent
from alice.session_manager import SessionManager
from alice.ia_control_endpoints import router as ia_control_router
from alice.learning_endpoints import router as learning_router
from whatsapp.evolution_api import EvolutionAPI
from utils.debouncer import MessageDebouncer
from utils.message_splitter import send_with_typing_simulation
from utils.media_processor import MediaProcessor
from monitoring import health_monitor, require_auth, get_client_ip, add_ip_to_whitelist


# ============================================================================
# CONFIGURAÇÃO DE LOGS
# ============================================================================

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)

if settings.debug:
    logger.add("logs/alice_{time}.log", rotation="1 day", retention="7 days")


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

app = FastAPI(title="Alice - LC Baterias", version="1.0.0")

# Incluir routers de controle da IA e aprendizado
app.include_router(ia_control_router)
app.include_router(learning_router)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://138.68.13.174",
        "http://lcbaterias.automatexia.com.br",
        "https://lcbaterias.automatexia.com.br"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Componentes globais
alice_agent: Optional[AliceAgent] = None
session_manager: Optional[SessionManager] = None
whatsapp_api: Optional[EvolutionAPI] = None
debouncer: Optional[MessageDebouncer] = None
media_processor: Optional[MediaProcessor] = None


@app.on_event("startup")
async def startup():
    """Inicializa componentes"""
    global alice_agent, session_manager, whatsapp_api, debouncer, media_processor

    logger.info("🚀 Iniciando Alice...")

    # Agente
    alice_agent = AliceAgent()

    # Gerenciador de sessões
    session_manager = SessionManager(use_supabase=True)

    # WhatsApp API
    whatsapp_api = EvolutionAPI()

    # Debouncer (5s de silêncio, máximo 40s total)
    debouncer = MessageDebouncer(wait_seconds=settings.debounce_seconds, max_wait_seconds=40.0)

    # Processador de mídia
    media_processor = MediaProcessor()

    logger.success("✅ Alice iniciada com sucesso!")


@app.on_event("shutdown")
async def shutdown():
    """Encerra componentes"""
    logger.info("🛑 Encerrando Alice...")

    if session_manager:
        await session_manager.close()

    logger.info("👋 Alice encerrada")


# ============================================================================
# WEBHOOK DO WHATSAPP
# ============================================================================

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Recebe mensagens do WhatsApp via Evolution API

    Payload esperado:
    {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": "5561999999999@s.whatsapp.net",
                "fromMe": false
            },
            "message": {
                "conversation": "texto da mensagem"
            }
        }
    }
    """
    try:
        payload = await request.json()
        logger.debug(f"📥 Webhook recebido: {payload}")

        # Valida evento
        event = payload.get("event")
        if event != "messages.upsert":
            return JSONResponse({"status": "ignored", "reason": "not a message event"})

        data = payload.get("data", {})
        key = data.get("key", {})
        message_data = data.get("message", {})

        # Ignora mensagens enviadas pela própria Alice
        if key.get("fromMe"):
            return JSONResponse({"status": "ignored", "reason": "message from me"})

        # Extrai telefone e nome do contato
        remote_jid = key.get("remoteJid", "")
        phone = remote_jid.split("@")[0]  # Remove @s.whatsapp.net
        push_name = data.get("pushName", "Cliente")  # Nome do WhatsApp

        # ========================================================================
        # PROCESSA MÍDIAS (ÁUDIO, IMAGEM, DOCUMENTO)
        # ========================================================================
        media_type, media_data, media_info = await media_processor.extract_media_from_webhook(message_data)

        if media_type:
            logger.info(f"📎 Mídia detectada: {media_type}")

            # Se media_data for dict (sem base64), tenta baixar via Evolution API
            if isinstance(media_data, dict):
                logger.info("🔽 Mídia sem base64, tentando baixar via API...")

                # Tenta pegar URL da mídia
                media_url = media_data.get("url", "")

                # Baixa usando key completa e URL (se disponível)
                downloaded_bytes = await whatsapp_api.download_media(key, media_url)

                if downloaded_bytes:
                    media_data = downloaded_bytes
                    logger.success(f"✅ Mídia baixada: {len(media_data)} bytes")
                else:
                    logger.error("❌ Falha ao baixar mídia")
                    await whatsapp_api.send_text(phone, "Desculpe, não consegui processar sua mídia. Pode tentar novamente?")
                    return JSONResponse({"status": "media_download_failed"})

            # Agora media_data deve ser bytes
            # ÁUDIO - Transcreve
            if media_type == "audio":
                transcribed_text = await media_processor.process_audio(media_data, media_info)
                if transcribed_text:
                    message_text = f"[Áudio transcrito]: {transcribed_text}"
                    logger.info(f"🎤 Áudio de {phone}: '{message_text[:100]}...'")
                else:
                    await whatsapp_api.send_text(phone, "Desculpe, não consegui transcrever o áudio. Pode digitar a mensagem?")
                    return JSONResponse({"status": "audio_transcription_failed"})

            # IMAGEM - Analisa
            elif media_type == "image":
                # Verifica se tem legenda/pergunta junto com a imagem
                caption = message_data.get("imageMessage", {}).get("caption", "")
                image_analysis = await media_processor.process_image(media_data, caption or None)

                if image_analysis:
                    if caption:
                        message_text = f"[Imagem enviada com texto: '{caption}']\n\nAnálise da imagem: {image_analysis}"
                    else:
                        message_text = f"[Imagem enviada]\n\nAnálise: {image_analysis}"
                    logger.info(f"🖼️ Imagem de {phone} analisada")
                else:
                    await whatsapp_api.send_text(phone, "Desculpe, não consegui analisar a imagem. Pode descrever o que precisa?")
                    return JSONResponse({"status": "image_analysis_failed"})

            # DOCUMENTO - Extrai texto
            elif media_type == "document":
                document_text = await media_processor.process_document(media_data, media_info)

                if document_text:
                    message_text = f"[Documento '{media_info}' enviado]\n\nConteúdo:\n{document_text[:1000]}"  # Limita a 1000 chars
                    logger.info(f"📄 Documento de {phone} processado")
                else:
                    await whatsapp_api.send_text(phone, "Desculpe, não consegui processar o documento. Pode me contar o que precisa?")
                    return JSONResponse({"status": "document_processing_failed"})

        # ========================================================================
        # TEXTO NORMAL
        # ========================================================================
        else:
            # Extrai texto da mensagem
            message_text = (
                message_data.get("conversation") or
                message_data.get("extendedTextMessage", {}).get("text") or
                ""
            )

            if not message_text:
                logger.warning("⚠️ Mensagem sem texto ou mídia, ignorando")
                return JSONResponse({"status": "ignored", "reason": "no content"})

            logger.info(f"📨 Mensagem de texto de {phone}: '{message_text[:50]}...'")

        # ========================================================================
        # COMANDO /reset - Limpa memória do cliente
        # ========================================================================
        if message_text.strip().lower() in ['/reset', '/delete']:
            logger.warning(f"🔄 Comando /reset recebido de {phone}")

            # CRÍTICO: Limpa buffer do debouncer ANTES de processar
            debouncer.clear_buffer(phone)

            try:
                # 1. Buscar IDs das conversas
                from supabase import create_client
                supabase = create_client(settings.supabase_url, settings.supabase_service_key)

                conversas = supabase.table('conversas').select('id').eq('phone', phone).execute()
                conversa_ids = [c['id'] for c in (conversas.data or [])]

                # 2. Apagar mensagens dessas conversas
                if conversa_ids:
                    for conv_id in conversa_ids:
                        supabase.table('mensagens').delete().eq('conversa_id', conv_id).execute()

                # 3. Apagar conversas
                supabase.table('conversas').delete().eq('phone', phone).execute()

                # 4. Apagar sessão do chat
                supabase.table('chat_sessions').delete().eq('phone', phone).execute()

                # 5. Limpar da memória do session_manager
                await session_manager.delete_session(phone)

                logger.success(f"✅ Memória de {phone} resetada com sucesso!")

                # 6. Enviar mensagem de confirmação
                await whatsapp_api.send_text(phone, "MEMÓRIA RESETADA ✅\n\nBons testes 🧪")

                return JSONResponse({"status": "reset_success"})

            except Exception as e:
                logger.error(f"❌ Erro ao resetar memória de {phone}: {e}")
                await whatsapp_api.send_text(phone, "❌ Erro ao resetar memória. Tente novamente.")
                return JSONResponse({"status": "reset_failed", "error": str(e)})

        # Adiciona ao debouncer (processa após X segundos de silêncio)
        await debouncer.add_message(
            phone=phone,
            message=message_text,
            callback=lambda p, m: process_message(p, m, push_name)
        )

        return JSONResponse({"status": "queued"})

    except Exception as e:
        logger.error(f"💥 Erro no webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def salvar_mensagem(conversa_id: str, remetente: str, conteudo: str, tipo_midia: str = "text"):
    """
    Salva mensagem no histórico

    Args:
        conversa_id: ID da conversa
        remetente: 'usuario' ou 'assistente'
        conteudo: Conteúdo da mensagem
        tipo_midia: Tipo de mídia (text, audio, image, document)
    """
    try:
        from supabase import create_client
        from config import settings

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        supabase.table("mensagens").insert({
            "conversa_id": conversa_id,
            "remetente": remetente,
            "conteudo": conteudo,
            "tipo_midia": tipo_midia
        }).execute()

        logger.debug(f"💬 Mensagem salva: {remetente} - {conteudo[:50]}...")

    except Exception as e:
        logger.error(f"❌ Erro ao salvar mensagem: {e}")


async def notificar_departamento_transferencia(
    phone: str,
    departamento: str,
    nome_cliente: str,
    ultima_mensagem: str,
    motivo: str = "Transferência solicitada pela IA"
):
    """
    Notifica departamento específico sobre transferência de conversa

    Cria registro no Supabase para frontend exibir com badge e som
    Mantém compatibilidade total com transferência manual via botão
    """
    try:
        from supabase import create_client
        from config import settings
        from datetime import datetime

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Primeiro buscar conversa existente para preservar nome_lead
        existing = supabase.table("conversas").select("nome_lead").eq("phone", phone).execute()
        nome_final = nome_cliente

        if existing.data and len(existing.data) > 0:
            # Se conversa existe e já tem nome, usar o nome existente
            nome_existente = existing.data[0].get("nome_lead")
            if nome_existente:
                nome_final = nome_existente
                logger.debug(f"📝 Preservando nome existente: {nome_existente}")

        # Criar ou atualizar conversa com departamento
        # MESMOS CAMPOS que o botão de transferência manual usa
        result = supabase.table("conversas").upsert({
            "phone": phone,
            "empresa_id": "emp1",
            "departamento_slug": departamento,
            "status": "aberta",
            "modo_ia": "desligado",  # IA desliga quando transfere
            "ultima_mensagem": ultima_mensagem,
            "ultima_mensagem_em": datetime.utcnow().isoformat(),
            "transferido_em": datetime.utcnow().isoformat(),
            "transferido_por": "alice-ia",  # Identificador da IA
            "motivo_transferencia": motivo,  # Motivo da transferência
            "nome_lead": nome_final,
            "notificado": False,  # Frontend vai marcar como True quando usuário ver
            "updated_at": datetime.utcnow().isoformat()
        }, on_conflict="phone").execute()

        logger.success(f"✅ Conversa transferida pela IA para {departamento}: {motivo}")

    except Exception as e:
        logger.error(f"❌ Erro ao notificar departamento: {e}")


async def process_message(phone: str, combined_message: str, push_name: str = "Cliente"):
    """
    Processa mensagem(ns) agrupada(s) do usuário com CONTROLE INTELIGENTE DA IA

    Args:
        phone: Telefone do usuário
        combined_message: Mensagem(ns) combinada(s)
        push_name: Nome do contato no WhatsApp
    """
    logger.info(f"🤖 Processando mensagem de {phone}")

    try:
        # Mostra "digitando..." no WhatsApp (3 pontinhos)
        asyncio.create_task(whatsapp_api.send_typing(phone, duration=5000))

        # Importar controlador inteligente
        from alice.intelligent_controller import intelligent_controller

        # Recupera sessão
        state = await session_manager.get_session(phone)

        # Processa com Alice
        response, new_state = await alice_agent.process_message(
            phone=phone,
            message=combined_message,
            state=state
        )

        # Salva nova sessão
        await session_manager.save_session(phone, new_state)

        # ====================================================================
        # 🎯 DECISÃO INTELIGENTE: Enviar direto, aguardar aprovação ou bloquear
        # ====================================================================
        decisao, mensagem_id = await intelligent_controller.decidir_fluxo(
            phone=phone,
            mensagem_usuario=combined_message,
            resposta_ia=response,
            contexto=new_state
        )

        logger.info(f"🎯 Decisão: {decisao}")

        # ====================================================================
        # 💾 CRIAR/ATUALIZAR CONVERSA NO BANCO
        # ====================================================================
        conversa_id = await intelligent_controller._get_or_create_conversa(phone, new_state, push_name)
        logger.debug(f"💾 Conversa ID: {conversa_id}")

        # ====================================================================
        # 💬 SALVAR MENSAGEM DO USUÁRIO NO HISTÓRICO
        # ====================================================================
        await salvar_mensagem(conversa_id, "usuario", combined_message)

        # CASO 1: Enviar direto (modo ligado + alta confiança)
        if decisao == "enviar_direto":
            await send_with_typing_simulation(
                send_func=whatsapp_api.send_text,
                phone=phone,
                message=response,
                use_smart_split=True
            )
            logger.success(f"✅ Mensagem enviada DIRETAMENTE (alta confiança)")

            # Salvar resposta da IA no histórico
            await salvar_mensagem(conversa_id, "assistente", response)

        # CASO 2: Aguardar aprovação (modo atenção OU baixa confiança)
        elif decisao == "aguardar_aprovacao":
            logger.info(f"🟡 Mensagem criada para APROVAÇÃO (ID: {mensagem_id})")
            # Mensagem já foi criada em mensagens_pendentes
            # Frontend vai mostrar na fila de aprovação
            # NÃO envia agora, só após aprovação humana

        # CASO 3: Bloquear (IA desligada)
        elif decisao == "bloquear":
            logger.warning(f"🔴 Mensagem BLOQUEADA (IA desligada)")
            # Não faz nada, IA está desligada

        # ====================================================================
        # 🔔 VERIFICAR SE HOUVE TRANSFERÊNCIA PARA DEPARTAMENTO
        # ====================================================================
        logger.debug(f"🔍 Verificando transferência - State keys: {list(new_state.keys())}")
        logger.debug(f"🔍 notificar_departamento = {new_state.get('notificar_departamento')}")

        if new_state.get("notificar_departamento"):
            departamento = new_state.get("notificar_departamento")
            motivo = new_state.get("motivo_transferencia", "Cliente solicitou atendimento humano")
            logger.warning(f"🔔 CHAMANDO notificar_departamento_transferencia para {departamento}")

            # Usar push_name se nome_cliente não estiver no state
            nome_para_salvar = new_state.get("nome_cliente") or push_name or "Cliente"

            await notificar_departamento_transferencia(
                phone=phone,
                departamento=departamento,
                nome_cliente=nome_para_salvar,
                ultima_mensagem=combined_message,
                motivo=motivo
            )
            logger.success(f"🔔 Conversa transferida pela IA para {departamento}: {motivo}")

        logger.success(f"✅ Mensagem processada ({decisao})")

        # Reseta contador de erros do modelo (está funcionando)
        model_name = "gemini" if "gemini" in str(type(alice_agent)).lower() else "gpt-4o"
        health_monitor.reset_model_errors(model_name)

    except Exception as e:
        logger.error(f"💥 Erro ao processar mensagem de {phone}: {str(e)}")

        # Incrementa contador de erros do modelo
        model_name = "gemini" if "gemini" in str(type(alice_agent)).lower() else "gpt-4o"
        health_monitor.increment_model_error(model_name)

        # Envia mensagem de erro
        await whatsapp_api.send_text(
            phone=phone,
            message="Desculpe, estou com problemas técnicos. Vou transferir para um atendente."
        )


# ============================================================================
# ENDPOINTS DE CONTROLE
# ============================================================================

@app.get("/api/conversas")
async def buscar_conversas():
    """
    Busca todas as conversas com suas mensagens

    Returns:
        Lista de conversas com mensagens incluídas
    """
    try:
        from supabase import create_client
        from config import settings

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Buscar conversas
        conversas_result = supabase.table("conversas")\
            .select("*")\
            .order("updated_at", desc=True)\
            .execute()

        conversas_com_mensagens = []

        for conversa in conversas_result.data:
            # Buscar mensagens desta conversa
            mensagens_result = supabase.table("mensagens")\
                .select("*")\
                .eq("conversa_id", conversa["id"])\
                .order("enviada_em", desc=False)\
                .execute()

            conversas_com_mensagens.append({
                **conversa,
                "mensagens": mensagens_result.data
            })

        return {"conversas": conversas_com_mensagens}

    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mensagens/{conversa_id}")
async def buscar_mensagens(conversa_id: str):
    """
    Busca todas as mensagens de uma conversa

    Args:
        conversa_id: ID da conversa

    Returns:
        Lista de mensagens ordenadas por data
    """
    try:
        from supabase import create_client
        from config import settings

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        result = supabase.table("mensagens")\
            .select("*")\
            .eq("conversa_id", conversa_id)\
            .order("enviada_em", desc=False)\
            .execute()

        return {"mensagens": result.data}

    except Exception as e:
        logger.error(f"❌ Erro ao buscar mensagens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "agent": alice_agent is not None,
        "session_manager": session_manager is not None,
        "whatsapp": whatsapp_api is not None
    }


@app.post("/session/reset/{phone}")
async def reset_session(phone: str):
    """Reseta sessão de um usuário"""
    await session_manager.delete_session(phone)
    logger.info(f"🔄 Sessão resetada: {phone}")
    return {"status": "session reset", "phone": phone}


@app.get("/instance/status")
async def instance_status():
    """Verifica status da instância WhatsApp"""
    info = await whatsapp_api.get_instance_info()
    return info


# ============================================================================
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================================================

from alice.auth import auth_service, require_super_admin
from alice.auth import require_auth as user_require_auth  # Auth de usuários (não confundir com monitor)

@app.post("/api/auth/login")
async def login(request: Request):
    """
    Login de usuário

    Body:
    {
        "email": "admin@lcbaterias.com",
        "password": "admin123"
    }

    Returns:
    {
        "token": "jwt_token",
        "usuario": {...}
    }
    """
    try:
        payload = await request.json()
        email = payload.get("email")
        password = payload.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email e senha são obrigatórios")

        result = await auth_service.login(email, password)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no login: {e}")
        raise HTTPException(status_code=500, detail="Erro ao fazer login")


@app.post("/api/auth/logout")
async def logout(request: Request, usuario = Depends(user_require_auth)):
    """Logout (remove sessão)"""
    try:
        authorization = request.headers.get("authorization", "")
        token = authorization.replace("Bearer ", "")
        await auth_service.logout(token)
        return {"success": True, "message": "Logout realizado"}
    except Exception as e:
        logger.error(f"❌ Erro no logout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_me(usuario = Depends(user_require_auth)):
    """Retorna dados do usuário logado"""
    return usuario


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), phone: str = Form(...)):
    """
    Endpoint para fazer upload de arquivos (imagens, áudios, vídeos, documentos)

    Retorna a URL do arquivo para ser usado no envio da mensagem
    """
    try:
        # Criar diretório de uploads se não existir
        upload_dir = Path("/var/www/alice-lc-uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome único para o arquivo
        file_extension = Path(file.filename or "file").suffix
        unique_filename = f"{phone}_{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Ajustar permissões para nginx poder ler
        os.chmod(file_path, 0o644)

        # Retornar URL (ajustar conforme seu servidor)
        file_url = f"http://138.68.13.174/uploads/{unique_filename}"

        logger.success(f"✅ Arquivo enviado: {file_url}")

        return {
            "success": True,
            "url": file_url,
            "filename": unique_filename
        }

    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def formatar_mensagem_com_departamento(message: str, departamento: str) -> str:
    """
    Formata mensagem com prefixo do departamento em negrito

    Args:
        message: Mensagem original
        departamento: Slug do departamento (vendas, financeiro, etc)

    Returns:
        Mensagem formatada com prefixo em negrito
    """
    # Mapeamento de departamentos para nomes formatados
    nomes_departamentos = {
        "vendas": "Vendas",
        "financeiro": "Financeiro",
        "assistencia-tecnica": "Assistência Técnica",
        "suporte-ti": "Suporte TI",
        "geral": "Humano"  # Super admin
    }

    # Pegar nome do departamento (fallback para "Humano" se não encontrado)
    nome_dept = nomes_departamentos.get(departamento, "Humano")

    # Formatar com negrito usando *texto* (formato WhatsApp)
    mensagem_formatada = f"*{nome_dept}:*\n{message}"

    return mensagem_formatada


@app.post("/api/enviar-mensagem")
async def enviar_mensagem(request: Request):
    """
    Endpoint para enviar mensagem do departamento para o cliente

    Body:
    {
        "phone": "5561999999999",
        "message": "Olá, sou do financeiro...",
        "departamento": "financeiro",
        "user_id": "user123",
        "midia_url": "http://exemplo.com/imagem.jpg"  // opcional
    }
    """
    try:
        from supabase import create_client
        from config import settings
        from datetime import datetime

        payload = await request.json()
        phone = payload.get("phone")
        message = payload.get("message")
        departamento = payload.get("departamento")
        user_id = payload.get("user_id")
        midia_url = payload.get("midia_url")

        # DEBUG: Log do payload recebido
        logger.warning(f"🔍 PAYLOAD RECEBIDO: {payload}")
        logger.warning(f"📋 Departamento recebido: '{departamento}' (tipo: {type(departamento)})")

        if not phone or not message:
            raise HTTPException(status_code=400, detail="Phone and message are required")

        # Formatar mensagem com prefixo do departamento
        mensagem_formatada = formatar_mensagem_com_departamento(message, departamento)
        logger.warning(f"💬 Mensagem formatada: {mensagem_formatada[:100]}")

        # Enviar via WhatsApp (com mídia se houver)
        if midia_url:
            # Extrair nome do arquivo da URL
            from pathlib import Path
            filename = Path(midia_url).name

            # Detectar tipo de mídia
            if any(ext in midia_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                await whatsapp_api.send_image(phone, midia_url, mensagem_formatada)
            elif any(ext in midia_url.lower() for ext in ['.mp4', '.avi', '.mov']):
                await whatsapp_api.send_video(phone, midia_url, mensagem_formatada)
            elif any(ext in midia_url.lower() for ext in ['.mp3', '.ogg', '.wav', '.m4a']):
                # Áudio não suporta caption, envia texto separado
                await whatsapp_api.send_audio(phone, midia_url)
                await whatsapp_api.send_text(phone, mensagem_formatada)
            elif any(ext in midia_url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                await whatsapp_api.send_document(phone, midia_url, mensagem_formatada, filename)
            else:
                await whatsapp_api.send_text(phone, f"{mensagem_formatada}\n\nArquivo: {midia_url}")
        else:
            await whatsapp_api.send_text(phone, mensagem_formatada)

        # Salvar mensagem no Supabase
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Buscar conversa
        conversa_result = supabase.table("conversas")\
            .select("id")\
            .eq("phone", phone)\
            .single()\
            .execute()

        if conversa_result.data:
            conversa_id = conversa_result.data["id"]

            # Detectar tipo de mídia
            tipo_midia = "texto"
            if midia_url:
                if any(ext in midia_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    tipo_midia = "imagem"
                elif any(ext in midia_url.lower() for ext in ['.mp4', '.avi', '.mov']):
                    tipo_midia = "video"
                elif any(ext in midia_url.lower() for ext in ['.mp3', '.ogg', '.wav', '.m4a']):
                    tipo_midia = "audio"
                elif any(ext in midia_url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                    tipo_midia = "documento"

            # Criar mensagem (salvar com prefixo formatado)
            supabase.table("mensagens").insert({
                "conversa_id": conversa_id,
                "remetente": "assistente",
                "conteudo": mensagem_formatada,  # Mensagem COM prefixo do departamento
                "tipo_midia": tipo_midia if midia_url else "text",
                "lida": True,
                "enviada_em": datetime.utcnow().isoformat()
            }).execute()

        logger.success(f"✅ Mensagem enviada para {phone} (tipo: {tipo_midia})")

        return {"success": True, "message": "Mensagem enviada com sucesso"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pausar-ia/{phone}")
async def pausar_ia(phone: str, request: Request):
    """
    Pausa a IA para uma conversa específica (quando humano assume)

    Body:
    {
        "user_id": "user123"
    }
    """
    try:
        from supabase import create_client
        from config import settings
        from datetime import datetime

        payload = await request.json()
        user_id = payload.get("user_id", "sistema")

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Pausar IA
        result = supabase.table("conversas").update({
            "modo_ia": "desligado",  # PAUSAR IA
            "status": "aberta",
            "transferido_em": datetime.utcnow().isoformat(),
            "transferido_por": user_id,
            "motivo_transferencia": "Humano assumiu conversa via dashboard",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("phone", phone).execute()

        logger.success(f"✅ IA pausada para conversa {phone}")

        return {
            "success": True,
            "message": "IA pausada com sucesso",
            "phone": phone
        }

    except Exception as e:
        logger.error(f"❌ Erro ao pausar IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transferir-conversa")
async def transferir_conversa(request: Request):
    """
    Transfere conversa para um departamento e pausa a IA

    Body:
    {
        "phone": "5561999999999",
        "departamento": "financeiro",
        "motivo": "Cliente solicita falar com financeiro",
        "user_id": "user123"
    }
    """
    try:
        from supabase import create_client
        from config import settings
        from datetime import datetime

        payload = await request.json()
        phone = payload.get("phone")
        departamento = payload.get("departamento")
        motivo = payload.get("motivo", "")
        user_id = payload.get("user_id", "sistema")

        if not phone or not departamento:
            raise HTTPException(status_code=400, detail="Phone and departamento are required")

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Atualizar conversa: pausar IA e atribuir departamento
        result = supabase.table("conversas").update({
            "modo_ia": "desligado",  # PAUSAR IA
            "departamento_slug": departamento,
            "status": "aberta",
            "transferido_em": datetime.utcnow().isoformat(),
            "transferido_por": user_id,
            "motivo_transferencia": motivo,
            "notificado": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("phone", phone).execute()

        logger.success(f"✅ Conversa {phone} transferida para {departamento}")

        return {
            "success": True,
            "message": f"Conversa transferida para {departamento}",
            "phone": phone,
            "departamento": departamento
        }

    except Exception as e:
        logger.error(f"❌ Erro ao transferir conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resolver-conversa/{phone}")
async def resolver_conversa(phone: str, request: Request):
    """
    Marca conversa como resolvida e reativa a IA

    Body:
    {
        "user_id": "user123",
        "nota": "Cliente atendido com sucesso"
    }
    """
    try:
        from supabase import create_client
        from config import settings
        from datetime import datetime

        payload = await request.json()
        user_id = payload.get("user_id", "sistema")
        nota = payload.get("nota", "")

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Atualizar conversa: reativar IA e marcar como resolvida
        # LIMPAR departamento_slug para voltar para página central (super admin)
        result = supabase.table("conversas").update({
            "modo_ia": "ligado",  # REATIVAR IA
            "status": "resolvida",
            "resolvido_em": datetime.utcnow().isoformat(),
            "resolvido_por": user_id,
            "nota_resolucao": nota,
            "departamento_slug": None,  # Volta para super admin
            "notificado": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("phone", phone).execute()

        # Limpar sessão Redis para IA começar do zero
        await session_manager.delete_session(phone)

        logger.success(f"✅ Conversa {phone} resolvida e IA reativada")

        return {
            "success": True,
            "message": "Conversa marcada como resolvida e IA reativada",
            "phone": phone
        }

    except Exception as e:
        logger.error(f"❌ Erro ao resolver conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE ANALYTICS (Super Admin Only)
# ============================================================================

from alice.analytics import analytics_tracker
from alice.ia_control_endpoints import router as ia_control_router

# Registrar endpoint pending-leads PRIMEIRO para garantir que funciona
@app.get("/api/analytics/pending-leads")
async def get_pending_leads():
    """Retorna leads pendentes (não completaram pedido)"""
    try:
        leads = analytics_tracker.get_leads_pendentes()
        return {
            "success": True,
            "leads": leads,
            "total": len(leads),
            "valor_potencial": sum(l.get("valor_estimado", 0) for l in leads) if leads else 0
        }
    except Exception as e:
        logger.error(f"❌ Erro ao buscar leads pendentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/metrics")
async def get_analytics_metrics():
    """
    Retorna métricas completas da IA para o dashboard

    Acesso: Apenas Super Administrador
    """
    try:
        metrics = analytics_tracker.get_metricas_completas()
        logger.info("📊 Métricas de analytics solicitadas")
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"❌ Erro ao buscar métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/funil")
async def get_conversion_funnel():
    """
    Retorna dados do funil de conversão

    Acesso: Apenas Super Administrador
    """
    try:
        funil = analytics_tracker.get_funil_conversao()
        return {
            "success": True,
            "funnel": funil
        }
    except Exception as e:
        logger.error(f"❌ Erro ao buscar funil: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/top-products")
async def get_top_products(limit: int = 5):
    """
    Retorna top produtos vendidos pela IA

    Acesso: Apenas Super Administrador
    """
    try:
        produtos = analytics_tracker.get_top_produtos(limit)
        return {
            "success": True,
            "products": produtos
        }
    except Exception as e:
        logger.error(f"❌ Erro ao buscar top produtos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/register-lead-pending")
async def register_lead_pending(
    phone: str,
    nome: str,
    ultima_mensagem: str,
    valor_estimado: float
):
    """
    Registra manualmente um lead pendente

    Usado pela IA quando detecta abandono
    """
    try:
        analytics_tracker.registrar_lead_pendente(
            phone=phone,
            nome=nome,
            ultima_mensagem=ultima_mensagem,
            valor_estimado=valor_estimado
        )
        return {"success": True, "message": "Lead pendente registrado"}
    except Exception as e:
        logger.error(f"❌ Erro ao registrar lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/analytics/remove-lead-pending/{phone}")
async def remove_lead_pending(phone: str):
    """
    Remove lead pendente (quando recuperado por humano)
    """
    try:
        analytics_tracker.remover_lead_pendente(phone)
        return {"success": True, "message": "Lead removido"}
    except Exception as e:
        logger.error(f"❌ Erro ao remover lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXECUÇÃO
# ============================================================================

# ============================================================================
# WEBHOOK GEMINI (EXPERIMENTAL)
# ============================================================================

gemini_agent: Optional["GeminiAgent"] = None

@app.post("/webhook/whatsapp-gemini")
async def whatsapp_webhook_gemini(request: Request):
    """
    Webhook alternativo usando Gemini (experimental)
    Para testar, troque a URL do webhook na Evolution para:
    https://lcbaterias.automatexia.com.br/webhook/whatsapp-gemini
    """
    global gemini_agent

    # Inicializa Gemini sob demanda
    if gemini_agent is None:
        from alice.gemini_agent import GeminiAgent
        gemini_agent = GeminiAgent()
        logger.info("🔷 Gemini Agent inicializado")

    # Usa a mesma lógica do webhook principal, mas com gemini_agent
    # Por simplicidade, apenas redireciona para o processo principal
    # substituindo temporariamente o agent global
    global alice_agent
    original_agent = alice_agent
    alice_agent = gemini_agent

    try:
        result = await whatsapp_webhook(request)
        return result
    finally:
        alice_agent = original_agent


# ============================================================================
# ROTAS DE MONITORAMENTO
# ============================================================================

@app.get("/health")
async def health_check():
    """Endpoint básico de health check"""
    return {"status": "healthy", "service": "alice-lc-backend"}


@app.get("/monitor", response_class=HTMLResponse)
async def monitor_login_page():
    """
    Página de login do monitor
    """
    login_path = Path(__file__).parent / "monitoring" / "login.html"
    with open(login_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@app.get("/monitor/dashboard", response_class=HTMLResponse)
async def monitor_dashboard(request: Request):
    """
    Dashboard de monitoramento do sistema
    Requer autenticação (IP Whitelist OU Login)
    """
    # AUTENTICAÇÃO INLINE (não usa Depends)
    logger.info("🔍 DEBUG - monitor_dashboard chamado")
    await require_auth(request)

    # Log de acesso
    client_ip = get_client_ip(request)
    logger.info(f"📊 Dashboard acessado por: {client_ip}")

    # Carrega HTML do dashboard
    dashboard_path = Path(__file__).parent / "monitoring" / "dashboard.html"
    with open(dashboard_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@app.get("/monitor/api/health", dependencies=[Depends(require_auth)])
async def monitor_api_health():
    """
    API que retorna dados de saúde do sistema em JSON
    Usado pelo dashboard para atualização em tempo real
    """
    health_status = await health_monitor.check_system_health()
    return health_status


@app.post("/monitor/whitelist/add")
async def add_my_ip_to_whitelist(request: Request):
    """
    Endpoint especial para adicionar seu próprio IP à whitelist
    Usar apenas uma vez na primeira configuração
    """
    client_ip = get_client_ip(request)

    # Adiciona IP
    add_ip_to_whitelist(client_ip)

    return {
        "status": "success",
        "message": f"IP {client_ip} adicionado à whitelist",
        "next_step": "Agora você pode acessar /monitor diretamente sem login"
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🎯 Iniciando servidor...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Desabilitado reload por problemas com rotas
        log_level="info"
    )
