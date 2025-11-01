"""Gerenciador de sessões de conversa"""
from typing import Dict, Optional
import json
from datetime import datetime, timedelta
from loguru import logger
from supabase import create_client, Client
from config import settings
from alice.state import ConversationState, create_initial_state


class SessionManager:
    """Gerencia sessões de conversa (Supabase Postgres ou memória)"""

    def __init__(self, use_supabase: bool = True):
        """
        Args:
            use_supabase: Se True, usa Supabase Postgres; se False, usa memória
        """
        self.use_supabase = use_supabase
        self.sessions: Dict[str, ConversationState] = {}  # Fallback em memória
        self.supabase: Optional[Client] = None

        if use_supabase:
            try:
                self.supabase = create_client(
                    settings.supabase_url,
                    settings.supabase_service_key
                )
                logger.info("✅ SessionManager conectado ao Supabase Postgres")
            except Exception as e:
                logger.warning(f"⚠️ Supabase indisponível, usando memória: {e}")
                self.use_supabase = False

    async def get_session(self, phone: str) -> ConversationState:
        """
        Recupera sessão existente ou cria nova COM MEMÓRIA DE LONGO PRAZO

        Args:
            phone: Telefone do usuário

        Returns:
            Estado da conversa com contexto histórico
        """
        if self.use_supabase and self.supabase:
            try:
                # Busca sessão no Supabase
                response = self.supabase.table("chat_sessions").select("*").eq("phone", phone).execute()

                if response.data and len(response.data) > 0:
                    # Sessão encontrada - deserializa o JSONB
                    session_data = response.data[0]
                    state = self._deserialize_state(session_data["state"])
                    logger.info(f"📂 Sessão recuperada do Supabase: {phone}")
                else:
                    # Nova sessão - mas vamos buscar histórico antigo
                    logger.info(f"🆕 Nova sessão criada: {phone}")
                    state = create_initial_state(phone)

                # 🧠 MEMÓRIA DE LONGO PRAZO: Buscar dados históricos APENAS SE for nova sessão
                # Se a sessão já existe no Redis, NÃO carrega histórico (já está no state)
                if not (response.data and len(response.data) > 0):
                    # Só carrega histórico se for NOVA sessão (não tinha no Redis)
                    historical_data = await self._load_historical_context(phone)

                    if historical_data:
                        # Adicionar contexto histórico ao state APENAS se o cliente tiver interações FECHADAS
                        # Não conta conversa atual ainda aberta
                        if historical_data.get("total_interacoes", 0) > 0:
                            state["nome_cliente"] = historical_data.get("nome_cliente")
                            state["cnpj"] = historical_data.get("cnpj")
                            state["codigo_cliente"] = historical_data.get("codigo_cliente")
                            state["codigo_empresa"] = historical_data.get("codigo_empresa")
                            state["nome_empresa"] = historical_data.get("nome_empresa")
                            state["historico_interacoes"] = historical_data.get("total_interacoes", 0)
                            state["ultimo_pedido"] = historical_data.get("ultimo_pedido")

                            logger.success(
                                f"🧠 Memória carregada para {phone}: "
                                f"Nome={historical_data.get('nome_cliente')}, "
                                f"Interações={historical_data.get('total_interacoes', 0)}"
                            )

                return state

            except Exception as e:
                logger.error(f"❌ Erro ao recuperar sessão do Supabase: {e}")
                # Fallback para memória
                return self.sessions.get(phone, create_initial_state(phone))
        else:
            # Usa memória
            if phone not in self.sessions:
                logger.info(f"🆕 Nova sessão criada (memória): {phone}")
                self.sessions[phone] = create_initial_state(phone)

            return self.sessions[phone]

    async def save_session(self, phone: str, state: ConversationState) -> None:
        """
        Salva sessão

        Args:
            phone: Telefone do usuário
            state: Estado atualizado
        """
        if self.use_supabase and self.supabase:
            try:
                # Serializa estado para JSONB
                state_json = self._serialize_state(state)

                # Calcula expiração (24 horas)
                expires_at = (datetime.now() + timedelta(hours=24)).isoformat()

                # Upsert no Supabase (insert ou update)
                # IMPORTANTE: on_conflict="phone" garante que atualiza se já existir
                self.supabase.table("chat_sessions").upsert({
                    "phone": phone,
                    "state": state_json,
                    "expires_at": expires_at,
                    "last_message_at": datetime.now().isoformat()
                }, on_conflict="phone").execute()

                logger.debug(f"💾 Sessão salva no Supabase: {phone}")

            except Exception as e:
                logger.error(f"❌ Erro ao salvar sessão no Supabase: {e}")
                # Fallback para memória
                self.sessions[phone] = state
        else:
            # Salva em memória
            self.sessions[phone] = state
            logger.debug(f"💾 Sessão salva (memória): {phone}")

    async def delete_session(self, phone: str) -> None:
        """
        Deleta sessão

        Args:
            phone: Telefone do usuário
        """
        if self.use_supabase and self.supabase:
            try:
                self.supabase.table("chat_sessions").delete().eq("phone", phone).execute()
                logger.info(f"🗑️ Sessão deletada do Supabase: {phone}")
            except Exception as e:
                logger.error(f"❌ Erro ao deletar sessão do Supabase: {e}")

        # Remove da memória também
        if phone in self.sessions:
            del self.sessions[phone]
            logger.info(f"🗑️ Sessão deletada (memória): {phone}")

    def _serialize_state(self, state: ConversationState) -> dict:
        """
        Serializa ConversationState para JSON (JSONB do Postgres)

        Args:
            state: Estado da conversa

        Returns:
            Dict serializável para JSON
        """
        # Converte mensagens do LangChain para formato serializável
        messages_serialized = []
        for msg in state.get("messages", []):
            msg_dict = {
                "type": msg.__class__.__name__,
                "content": msg.content
            }
            if hasattr(msg, "name"):
                msg_dict["name"] = msg.name
            # NÃO serializa tool_calls - causam erro na deserialização
            # As tool calls já foram executadas e não precisam ser persistidas
            messages_serialized.append(msg_dict)

        # Cria cópia do state para serialização
        serializable_state = {
            k: v for k, v in state.items() if k != "messages"
        }
        serializable_state["messages"] = messages_serialized

        return serializable_state

    def _deserialize_state(self, state_json: dict) -> ConversationState:
        """
        Deserializa JSON (JSONB) para ConversationState

        Args:
            state_json: Estado em formato JSON

        Returns:
            ConversationState reconstruído
        """
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        # Reconstrói mensagens
        messages = []
        for msg_dict in state_json.get("messages", []):
            msg_type = msg_dict.get("type")
            content = msg_dict.get("content")

            if msg_type == "HumanMessage":
                messages.append(HumanMessage(content=content))
            elif msg_type == "AIMessage":
                # IMPORTANTE: Remove tool_calls das AIMessages persistidas
                # Tool calls causam erro quando deserializadas porque o tool_call_id
                # das ToolMessages correspondentes fica quebrado
                msg = AIMessage(content=content)
                # NÃO adiciona tool_calls de volta - elas já foram executadas
                messages.append(msg)
            elif msg_type == "SystemMessage":
                messages.append(SystemMessage(content=content))
            # SKIP ToolMessages - elas causam erro de tool_call_id inválido
            # ToolMessages são intermediárias e não precisam ser persistidas

        # Reconstrói estado completo
        state = {k: v for k, v in state_json.items() if k != "messages"}
        state["messages"] = messages

        return state

    async def _load_historical_context(self, phone: str) -> Optional[dict]:
        """
        Carrega contexto histórico do cliente de conversas anteriores

        Busca informações como:
        - Nome do cliente
        - CNPJ usado anteriormente
        - Códigos de cliente/empresa
        - Número de interações anteriores
        - Último pedido

        Args:
            phone: Telefone do cliente

        Returns:
            Dict com dados históricos ou None
        """
        if not self.supabase:
            return None

        try:
            # Buscar APENAS conversas FECHADAS anteriores (não conta conversa aberta atual)
            # Isso evita alucinação onde IA reconhece cliente na primeira conversa
            conversas_result = self.supabase.table("conversas")\
                .select("id, nome_lead, status, created_at, updated_at")\
                .eq("phone", phone)\
                .eq("status", "fechada")\
                .order("updated_at", desc=True)\
                .limit(10)\
                .execute()

            if not conversas_result.data or len(conversas_result.data) == 0:
                # Nenhuma conversa FECHADA anterior = cliente novo!
                return None

            total_interacoes = len(conversas_result.data)
            conversa_ids = [c["id"] for c in conversas_result.data]
            nome_cliente = conversas_result.data[0].get("nome_lead")  # Pega o mais recente

            # Buscar mensagens dessas conversas para extrair CNPJ e outras informações
            mensagens_result = self.supabase.table("mensagens")\
                .select("conteudo, remetente")\
                .in_("conversa_id", conversa_ids)\
                .order("enviada_em", desc=False)\
                .limit(100)\
                .execute()

            # Extrair CNPJ e códigos das mensagens (se a IA salvou)
            cnpj = None
            codigo_cliente = None
            codigo_empresa = None
            nome_empresa = None

            if mensagens_result.data:
                for msg in mensagens_result.data:
                    conteudo = msg.get("conteudo", "")

                    # Tentar extrair CNPJ (14 dígitos seguidos)
                    import re
                    cnpj_match = re.search(r'\b\d{14}\b', conteudo)
                    if cnpj_match and not cnpj:
                        cnpj = cnpj_match.group()

            # Buscar pedidos anteriores
            pedidos_result = self.supabase.table("pedidos")\
                .select("numero_pedido, valor_total, created_at")\
                .eq("telefone", phone)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            ultimo_pedido = None
            if pedidos_result.data and len(pedidos_result.data) > 0:
                ultimo_pedido = {
                    "numero": pedidos_result.data[0].get("numero_pedido"),
                    "valor": pedidos_result.data[0].get("valor_total"),
                    "data": pedidos_result.data[0].get("created_at")
                }

            historical_data = {
                "nome_cliente": nome_cliente,
                "cnpj": cnpj,
                "codigo_cliente": codigo_cliente,
                "codigo_empresa": codigo_empresa,
                "nome_empresa": nome_empresa,
                "total_interacoes": total_interacoes,
                "ultimo_pedido": ultimo_pedido
            }

            return historical_data

        except Exception as e:
            logger.error(f"❌ Erro ao carregar contexto histórico: {e}")
            return None

    async def close(self):
        """Fecha conexões"""
        # Supabase client não precisa de close explícito
        logger.info("🔌 SessionManager encerrado")
