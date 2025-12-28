"""Aplicação principal da Alice - Clínica Caru Moreno"""
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

app = FastAPI(title="Alice - Clínica Caru Moreno", version="1.0.0")

# Incluir routers de controle da IA e aprendizado
app.include_router(ia_control_router)
app.include_router(learning_router)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TEMPORÁRIO: aceita qualquer origem
    allow_credentials=False,
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
        
        # Fix: Se remoteJid termina com @lid (iPhone), usa remoteJidAlt
        if remote_jid.endswith("@lid"):
            remote_jid_alt = key.get("remoteJidAlt", "")
            if remote_jid_alt:  # Se tiver remoteJidAlt, usa ele
                remote_jid = remote_jid_alt
        
        phone = remote_jid.split("@")[0]  # Remove @s.whatsapp.net ou @lid
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

            # CRITICAL: Fix encoding issues from WhatsApp
            # Remove non-breaking spaces and fix Unicode
            message_text = message_text.replace('\xa0', ' ').strip()

            # Ensure proper UTF-8 encoding
            try:
                message_text = message_text.encode('utf-8').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                # If encoding fails, try to fix common issues
                message_text = message_text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

            logger.info(f"📨 Mensagem de texto de {phone}: '{message_text[:50]}...'")

        # ========================================================================
        # COMANDO /reset ou /delete - Limpa memória completa do cliente
        # ========================================================================
        if message_text.strip().lower() in ['/reset', '/delete', '/limpar']:
            logger.warning(f"🔄 Comando /delete recebido de {phone}")

            # CRÍTICO: Limpa buffer do debouncer ANTES de processar
            debouncer.clear_buffer(phone)

            try:
                # Usa o novo método unificado do SessionManager
                sucesso = await session_manager.delete_all_data(phone)

                if sucesso:
                    logger.success(f"✅ Memória de {phone} resetada com sucesso!")

                    # Enviar mensagem de confirmação amigável
                    await whatsapp_api.send_text(
                        phone,
                        "✅ MEMÓRIA RESETADA!\n\n"
                        "🧹 Seu histórico foi limpo.\n"
                        "🆕 Podemos começar uma nova conversa!"
                    )

                    return JSONResponse({"status": "reset_success"})
                else:
                    raise Exception("Falha ao deletar sessão")

            except Exception as e:
                logger.error(f"❌ Erro ao resetar memória de {phone}: {e}")
                await whatsapp_api.send_text(
                    phone,
                    "❌ Erro ao resetar memória. Tente novamente."
                )
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

        # Verificar se é primeira mensagem (sessão vazia ou sem histórico)
        is_primeira_mensagem = not state or len(state.get("messages", [])) == 0

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
# ENDPOINT DE ENVIO DE MENSAGEM MANUAL (Tela Principal)
# ============================================================================

@app.post("/api/enviar-mensagem")
async def enviar_mensagem(request: Request):
    """
    Endpoint para enviar mensagem manual da tela principal para o cliente

    Body:
    {
        "phone": "5561999999999",
        "message": "Olá, aqui é da clínica..."
    }
    """
    try:
        from supabase import create_client
        from config import settings
        from datetime import datetime

        payload = await request.json()
        phone = payload.get("phone")
        message = payload.get("message")

        if not phone or not message:
            raise HTTPException(status_code=400, detail="Phone and message are required")

        # Formatar mensagem com prefixo "Humano:"
        mensagem_formatada = f"*Humano:*\n{message}"
        logger.info(f"💬 Mensagem manual: {mensagem_formatada[:100]}")

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

            # Criar mensagem
            supabase.table("mensagens").insert({
                "conversa_id": conversa_id,
                "remetente": "assistente",
                "conteudo": mensagem_formatada,
                "tipo_midia": "text",
                "lida": True,
                "enviada_em": datetime.utcnow().isoformat()
            }).execute()

        logger.success(f"✅ Mensagem manual enviada para {phone}")

        return {"success": True, "message": "Mensagem enviada com sucesso"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pausar-ia/{phone}")
async def pausar_ia(phone: str, request: Request):
    """
    Pausa a IA para uma conversa específica
    Usado quando humano assume atendimento manual

    Body:
    {
        "user_id": "user123"
    }
    """
    try:
        from supabase import create_client
        from datetime import datetime

        payload = await request.json()
        user_id = payload.get("user_id", "sistema")

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Atualizar conversa: pausar IA
        result = supabase.table("conversas").update({
            "modo_ia": "pausado",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("phone", phone).execute()

        logger.success(f"✅ IA pausada para conversa {phone} (pausado por: {user_id})")

        return {
            "success": True,
            "message": "IA pausada com sucesso",
            "phone": phone,
            "modo_ia": "pausado"
        }

    except Exception as e:
        logger.error(f"❌ Erro ao pausar IA: {e}")
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
        from datetime import datetime

        payload = await request.json()
        user_id = payload.get("user_id", "sistema")
        nota = payload.get("nota", "")

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Atualizar conversa: reativar IA
        result = supabase.table("conversas").update({
            "modo_ia": "ligado",  # REATIVAR IA
            "status": "aberta",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("phone", phone).execute()

        # Limpar sessão Redis para IA começar do zero
        await session_manager.delete_session(phone)

        logger.success(f"✅ Conversa {phone} resolvida e IA reativada")

        return {
            "success": True,
            "message": "Conversa encerrada e IA reativada",
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
    """Retorna leads pendentes (não completaram agendamento)"""
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
    Retorna top procedimentos agendados pela IA

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
async def buscar_conversas(limit: int = 50):
    """
    Busca conversas com suas mensagens (OTIMIZADO)

    PERFORMANCE:
    - Busca TODAS as mensagens em 1 única query
    - Agrupa mensagens por conversa_id em memória (Python dict)
    - Reduz N+1 queries para apenas 2 queries totais
    """
    try:
        from supabase import create_client
        from collections import defaultdict

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # 🚀 QUERY 1: Buscar conversas (com limit para performance)
        conversas_result = supabase.table("conversas")\
            .select("*")\
            .order("updated_at", desc=True)\
            .limit(limit)\
            .execute()

        if not conversas_result.data:
            return {"conversas": []}

        # Pegar IDs das conversas
        conversa_ids = [c["id"] for c in conversas_result.data]

        # 🚀 QUERY 2: Buscar TODAS as mensagens dessas conversas de uma vez
        mensagens_result = supabase.table("mensagens")\
            .select("*")\
            .in_("conversa_id", conversa_ids)\
            .order("enviada_em", desc=False)\
            .execute()

        # 📦 Agrupar mensagens por conversa_id (em memória - super rápido)
        mensagens_por_conversa = defaultdict(list)
        for msg in mensagens_result.data:
            mensagens_por_conversa[msg["conversa_id"]].append(msg)

        # 🏗️ Montar resposta
        conversas_com_mensagens = []
        for conversa in conversas_result.data:
            conversa_id = conversa["id"]
            mensagens = mensagens_por_conversa.get(conversa_id, [])

            # Última mensagem (para preview)
            ultima_mensagem = None
            if mensagens:
                ultima_msg_data = mensagens[-1]  # Última da lista ordenada
                ultima_mensagem = {
                    "id": ultima_msg_data["id"],
                    "conversa_id": ultima_msg_data["conversa_id"],
                    "conteudo": ultima_msg_data["conteudo"],
                    "tipo": "entrada" if ultima_msg_data["remetente"] == "usuario" else "saida",
                    "created_at": ultima_msg_data["enviada_em"]
                }

            conversas_com_mensagens.append({
                **conversa,
                "mensagens": mensagens,
                "ultima_mensagem": ultima_mensagem,
                "tags": conversa.get("tags") or []  # Tags já vêm da conversa
            })

        logger.info(f"✅ {len(conversas_com_mensagens)} conversas carregadas (limit={limit})")
        return {"conversas": conversas_com_mensagens}

    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversas: {e}")
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


@app.put("/api/conversas/{phone}/qualificacao")
async def atualizar_qualificacao(phone: str, request: Request):
    """
    Atualiza a qualificação do lead (frio/quente) - OTIMIZADO

    Body:
    {
        "qualificacao": "frio" | "quente" | null
    }

    PERFORMANCE:
    - NÃO atualiza updated_at para evitar trigger de real-time desnecessário
    - Apenas atualiza o campo qualificacao
    """
    try:
        from supabase import create_client

        payload = await request.json()
        qualificacao = payload.get("qualificacao")

        # Validar qualificação
        if qualificacao not in ["frio", "quente", None]:
            raise HTTPException(status_code=400, detail="Qualificação deve ser 'frio', 'quente' ou null")

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # ⚡ Atualizar SOMENTE qualificação (não updated_at)
        result = supabase.table("conversas").update({
            "qualificacao": qualificacao
        }).eq("phone", phone).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")

        logger.info(f"✅ Qualificação atualizada: {phone} → {qualificacao}")

        return {
            "success": True,
            "message": "Qualificação atualizada",
            "phone": phone,
            "qualificacao": qualificacao
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar qualificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/conversas/{phone}/pipeline")
async def atualizar_estagio_pipeline(phone: str, request: Request):
    """
    Atualiza o estágio do pipeline do lead

    Estágios disponíveis:
    - novo: Lead novo que acabou de chegar
    - em_contato: Primeira interação acontecendo
    - aguardando_resposta: Lead não respondeu ainda
    - interessado: Demonstrou interesse
    - agendamento_solicitado: Pediu para agendar
    - agendado: Consulta já marcada
    - compareceu: Passou na consulta
    - nao_compareceu: Faltou à consulta
    - convertido: Fechou tratamento
    - perdido: Desistiu/não tem interesse

    Body:
    {
        "estagio": "agendado"
    }
    """
    try:
        from supabase import create_client

        payload = await request.json()
        estagio = payload.get("estagio")

        # Validar estágio
        estagios_validos = [
            "novo", "em_contato", "aguardando_resposta", "interessado",
            "agendamento_solicitado", "agendado", "compareceu",
            "nao_compareceu", "convertido", "perdido"
        ]

        if estagio not in estagios_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Estágio inválido. Use um dos seguintes: {', '.join(estagios_validos)}"
            )

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # ⚡ Atualizar estágio do pipeline
        result = supabase.table("conversas").update({
            "estagio_pipeline": estagio
        }).eq("phone", phone).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")

        logger.info(f"✅ Estágio do pipeline atualizado: {phone} → {estagio}")

        return {
            "success": True,
            "message": "Estágio atualizado",
            "phone": phone,
            "estagio": estagio
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar estágio do pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads")
async def listar_leads(
    periodo: str = "hoje",  # hoje, 7dias, mes, tudo
    qualificacao: str = None,  # frio, quente, null
    pipeline: str = None,  # filtro por estágio do pipeline
    tag: str = None,  # filtro por tag
    data_inicio: str = None,  # formato: YYYY-MM-DD
    data_fim: str = None  # formato: YYYY-MM-DD
):
    """
    Lista todos os leads que falaram com a IA no WhatsApp com filtros

    Filtros:
    - periodo: hoje, 7dias, mes, tudo
    - qualificacao: frio, quente, sem_qualificacao
    - pipeline: filtro por estágio (novo, em_contato, agendado, etc)
    - tag: busca parcial por tag
    - data_inicio e data_fim: intervalo customizado
    """
    try:
        from supabase import create_client
        from datetime import datetime, timedelta

        supabase = create_client(settings.supabase_url, settings.supabase_service_key)

        # Buscar todas as conversas
        query = supabase.table("conversas")\
            .select("*")\
            .order("created_at", desc=True)

        result = query.execute()
        leads = []

        # Aplicar filtros
        hoje = datetime.utcnow().date()

        for conversa in result.data:
            # Filtro de período
            data_conversa = datetime.fromisoformat(conversa['created_at'].replace('Z', '+00:00')).date()

            if periodo == "hoje":
                if data_conversa != hoje:
                    continue
            elif periodo == "7dias":
                if data_conversa < hoje - timedelta(days=7):
                    continue
            elif periodo == "mes":
                if data_conversa.month != hoje.month or data_conversa.year != hoje.year:
                    continue

            # Filtro de intervalo customizado
            if data_inicio:
                inicio = datetime.fromisoformat(data_inicio).date()
                if data_conversa < inicio:
                    continue

            if data_fim:
                fim = datetime.fromisoformat(data_fim).date()
                if data_conversa > fim:
                    continue

            # Filtro de qualificação
            if qualificacao:
                if qualificacao == "sem_qualificacao":
                    if conversa.get('qualificacao'):
                        continue
                elif conversa.get('qualificacao') != qualificacao:
                    continue

            # Filtro de pipeline
            if pipeline:
                if conversa.get('estagio_pipeline') != pipeline:
                    continue

            # Filtro de tag (busca parcial)
            if tag:
                tags_conversa = conversa.get('tags') or []
                tag_encontrada = any(tag.lower() in t.lower() for t in tags_conversa)
                if not tag_encontrada:
                    continue

            # Montar objeto do lead
            leads.append({
                "id": conversa['id'],
                "nome": conversa.get('nome_lead') or 'Sem nome',
                "telefone": conversa['phone'],
                "tags": conversa.get('tags') or [],
                "qualificacao": conversa.get('qualificacao'),
                "estagio_pipeline": conversa.get('estagio_pipeline') or 'novo',
                "status": conversa.get('status'),
                "prioridade": conversa.get('prioridade'),
                "primeira_mensagem": conversa['created_at'],
                "ultima_interacao": conversa.get('updated_at') or conversa['created_at'],
                "total_mensagens": 0  # Pode ser calculado depois se necessário
            })

        logger.info(f"📊 Listando {len(leads)} leads | Filtros: periodo={periodo}, qualificacao={qualificacao}, pipeline={pipeline}, tag={tag}")

        return {
            "success": True,
            "total": len(leads),
            "leads": leads,
            "filtros_aplicados": {
                "periodo": periodo,
                "qualificacao": qualificacao,
                "pipeline": pipeline,
                "tag": tag,
                "data_inicio": data_inicio,
                "data_fim": data_fim
            }
        }

    except Exception as e:
        logger.error(f"❌ Erro ao listar leads: {e}")
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
