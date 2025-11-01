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
        Recupera sessão existente ou cria nova

        Args:
            phone: Telefone do usuário

        Returns:
            Estado da conversa
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
                    return state
                else:
                    # Nova sessão
                    logger.info(f"🆕 Nova sessão criada: {phone}")
                    return create_initial_state(phone)

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
            if hasattr(msg, "tool_calls"):
                msg_dict["tool_calls"] = msg.tool_calls
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
                msg = AIMessage(content=content)
                if "tool_calls" in msg_dict:
                    msg.tool_calls = msg_dict["tool_calls"]
                messages.append(msg)
            elif msg_type == "SystemMessage":
                messages.append(SystemMessage(content=content))
            elif msg_type == "ToolMessage":
                msg = ToolMessage(content=content, tool_call_id="")
                if "name" in msg_dict:
                    msg.name = msg_dict["name"]
                messages.append(msg)

        # Reconstrói estado completo
        state = {k: v for k, v in state_json.items() if k != "messages"}
        state["messages"] = messages

        return state

    async def close(self):
        """Fecha conexões"""
        # Supabase client não precisa de close explícito
        logger.info("🔌 SessionManager encerrado")
