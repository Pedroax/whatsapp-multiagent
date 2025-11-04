"""Otimizador de mensagens para reduzir custos de tokens"""
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from config import settings


class MessageOptimizer:
    """Comprime histórico de mensagens mantendo informações essenciais"""

    def __init__(self):
        """Inicializa otimizador com LLM para resumos"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Modelo mais barato para resumos
            api_key=settings.openai_api_key,
            temperature=0,
            max_tokens=500
        )

        # Configurações
        self.KEEP_RECENT_MESSAGES = 7  # Mantém últimas 7 mensagens completas
        self.SUMMARIZE_THRESHOLD = 10  # Começa a resumir após 10 mensagens

    def optimize_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        Otimiza lista de mensagens:
        - Mantém últimas N mensagens completas
        - Resume mensagens antigas em um único SystemMessage

        Args:
            messages: Lista de mensagens da conversa

        Returns:
            Lista otimizada de mensagens
        """
        # Se menos que threshold, retorna tudo
        if len(messages) < self.SUMMARIZE_THRESHOLD:
            return messages

        # Separa mensagens antigas e recentes
        old_messages = messages[:-self.KEEP_RECENT_MESSAGES]
        recent_messages = messages[-self.KEEP_RECENT_MESSAGES:]

        # Resume mensagens antigas
        try:
            summary = self._summarize_messages(old_messages)

            # Cria nova lista: [resumo] + [mensagens recentes]
            optimized = [SystemMessage(content=f"RESUMO DO HISTÓRICO:\n{summary}")]
            optimized.extend(recent_messages)

            # Log de economia
            tokens_saved = len(old_messages) - 1  # Substituiu N mensagens por 1 resumo
            logger.info(
                f"💰 Otimização: {len(old_messages)} msgs antigas → 1 resumo "
                f"({tokens_saved} msgs economizadas)"
            )

            return optimized

        except Exception as e:
            logger.error(f"❌ Erro ao resumir mensagens: {e}")
            # Em caso de erro, retorna apenas mensagens recentes
            return recent_messages

    def _summarize_messages(self, messages: List[BaseMessage]) -> str:
        """
        Resume lista de mensagens em texto conciso

        Args:
            messages: Mensagens a serem resumidas

        Returns:
            Resumo textual das informações essenciais
        """
        # Converte mensagens em texto simples
        conversation_text = ""
        for msg in messages:
            role = "Cliente" if isinstance(msg, HumanMessage) else "Alice"
            conversation_text += f"{role}: {msg.content}\n"

        # Prompt para resumir
        prompt = f"""Você é um assistente que resume conversas de vendas.

Analise esta conversa entre Alice (vendedora) e o Cliente, e extraia APENAS as informações essenciais em formato de bullet points:

{conversation_text}

Extraia OBRIGATORIAMENTE:
- Nome do cliente (se mencionado)
- CNPJ (se mencionado)
- Produtos mencionados ou consultados com quantidades
- **TROCA DE SUCATA: SIM ou NÃO** (CRÍTICO - sempre mencione)
- Condições de pagamento escolhidas
- Decisões tomadas (escolhas, confirmações)
- Etapa atual do atendimento

⚠️ IMPORTANTE: Se o cliente mencionou sobre troca de sucata (sim/não/com troca/sem troca), SEMPRE inclua "Troca de sucata: SIM" ou "Troca de sucata: NÃO" no resumo.

Seja MUITO conciso. Máximo 7 linhas."""

        # Gera resumo
        response = self.llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()

        return summary

    def should_compress(self, messages: List[BaseMessage]) -> bool:
        """
        Verifica se deve comprimir o histórico

        Args:
            messages: Lista de mensagens atuais

        Returns:
            True se deve comprimir, False caso contrário
        """
        return len(messages) >= self.SUMMARIZE_THRESHOLD
