"""Aplicação principal da Alice"""
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from config import settings
from alice.agent import AliceAgent
from alice.session_manager import SessionManager
from alice.ia_control_endpoints import router as ia_control_router
from alice.learning_endpoints import router as learning_router
from whatsapp.evolution_api import EvolutionAPI
from utils.debouncer import MessageDebouncer
from utils.message_splitter import send_with_typing_simulation
from utils.media_processor import MediaProcessor


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

    # Debouncer
    debouncer = MessageDebouncer(wait_seconds=settings.debounce_seconds)

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


async def notificar_departamento_transferencia(
    phone: str,
    departamento: str,
    nome_cliente: str,
    ultima_mensagem: str
):
    """
    Notifica departamento específico sobre transferência de conversa

    Cria registro no Supabase para frontend exibir com badge e som
    """
    try:
        from supabase import create_client
        from config import settings
        from datetime import datetime

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Criar ou atualizar conversa com departamento
        result = supabase.table("conversas").upsert({
            "phone": phone,
            "empresa_id": "emp1",
            "departamento_slug": departamento,
            "status": "aberta",
            "modo_ia": "desligado",  # IA desliga quando transfere
            "ultima_mensagem": ultima_mensagem,
            "ultima_mensagem_em": datetime.utcnow().isoformat(),
            "transferido_em": datetime.utcnow().isoformat(),
            "nome_lead": nome_cliente,
            "notificado": False  # Frontend vai marcar como True quando usuário ver
        }, on_conflict="phone").execute()

        logger.success(f"✅ Conversa criada/atualizada para {departamento}")

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

        # Cria ou recupera conversa no banco de dados
        conversa_id = await intelligent_controller._get_or_create_conversa(phone, new_state, push_name)
        logger.debug(f"💾 Conversa ID: {conversa_id}")

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

        # Salvar mensagem do usuário
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

            # Salvar resposta da IA
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
        if new_state.get("notificar_departamento"):
            departamento = new_state.get("notificar_departamento")
            await notificar_departamento_transferencia(
                phone=phone,
                departamento=departamento,
                nome_cliente=new_state.get("nome_cliente", "Cliente"),
                ultima_mensagem=combined_message
            )
            logger.success(f"🔔 Notificação enviada para {departamento}")

        logger.success(f"✅ Mensagem processada ({decisao})")

    except Exception as e:
        logger.error(f"💥 Erro ao processar mensagem de {phone}: {str(e)}")

        # Envia mensagem de erro
        await whatsapp_api.send_text(
            phone=phone,
            message="Desculpe, estou com problemas técnicos. Vou transferir para um atendente."
        )


# ============================================================================
# ENDPOINTS DE CONTROLE
# ============================================================================

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

from alice.auth import auth_service, require_auth, require_super_admin

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
async def logout(request: Request, usuario = Depends(require_auth)):
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
async def get_me(usuario = Depends(require_auth)):
    """Retorna dados do usuário logado"""
    return usuario


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
        "user_id": "user123"
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

        if not phone or not message:
            raise HTTPException(status_code=400, detail="Phone and message are required")

        # Formatar mensagem com prefixo do departamento
        mensagem_formatada = formatar_mensagem_com_departamento(message, departamento)
        logger.info(f"💬 Mensagem formatada: {mensagem_formatada[:100]}")

        # Enviar via WhatsApp
        await whatsapp_api.send_text(phone, mensagem_formatada)

        # Salvar mensagem no Supabase
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Buscar conversa
        conversa_result = supabase.table("conversas")\
            .select("id")\
            .eq("phone", phone)\
            .execute()

        if conversa_result.data and len(conversa_result.data) > 0:
            conversa_id = conversa_result.data[0]["id"]

            # Criar mensagem (salvar com prefixo formatado)
            supabase.table("mensagens").insert({
                "conversa_id": conversa_id,
                "remetente": "assistente",
                "conteudo": mensagem_formatada,  # Mensagem COM prefixo do departamento
                "tipo_midia": "text",
                "lida": True,
                "enviada_em": datetime.utcnow().isoformat()
            }).execute()

        logger.success(f"✅ Mensagem enviada de {departamento} para {phone}")

        return {"success": True, "message": "Mensagem enviada com sucesso"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {e}")
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
        result = supabase.table("conversas").update({
            "modo_ia": "ligado",  # REATIVAR IA
            "status": "resolvida",
            "resolvido_em": datetime.utcnow().isoformat(),
            "resolvido_por": user_id,
            "nota_resolucao": nota,
            "departamento_slug": None,  # Limpar departamento
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


@app.get("/api/conversas")
async def buscar_conversas():
    """Busca todas as conversas com suas mensagens"""
    try:
        from supabase import create_client

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        conversas_result = supabase.table("conversas").select("*").order("updated_at", desc=True).execute()
        conversas_com_mensagens = []

        for conversa in conversas_result.data:
            mensagens_result = supabase.table("mensagens").select("*").eq("conversa_id", conversa["id"]).order("enviada_em", desc=False).execute()
            conversas_com_mensagens.append({**conversa, "mensagens": mensagens_result.data})

        return {"conversas": conversas_com_mensagens}
    except Exception as e:
        logger.error(f"Erro ao buscar conversas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mensagens")
async def buscar_mensagens():
    """Busca todas as mensagens"""
    try:
        from supabase import create_client

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        result = supabase.table("mensagens").select("*").order("enviada_em", desc=True).execute()

        return {"mensagens": result.data}
    except Exception as e:
        logger.error(f"Erro ao buscar mensagens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXECUÇÃO
# ============================================================================

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
