import asyncio
from typing import Dict, Callable, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MessageDebouncer:
    """
    Sistema de debouncing inteligente para mensagens do WhatsApp.

    Agrupa mensagens enviadas em sequência rápida pelo mesmo usuário,
    processando apenas quando o usuário para de enviar por X segundos.
    """

    def __init__(self, wait_seconds: float = 5.0):
        """
        Args:
            wait_seconds: Segundos de espera após última mensagem antes de processar
        """
        self.wait_seconds = wait_seconds
        self.timers: Dict[str, asyncio.Task] = {}
        self.message_buffer: Dict[str, list] = {}
        self.locks: Dict[str, asyncio.Lock] = {}

    async def add_message(
        self,
        phone: str,
        message: str,
        callback: Callable[[str, str], Any]
    ) -> None:
        """
        Adiciona mensagem ao buffer e gerencia debouncing.

        Args:
            phone: Telefone do usuário
            message: Mensagem recebida
            callback: Função async a ser chamada quando processar (recebe phone, combined_message)
        """
        # Cria lock se não existir
        if phone not in self.locks:
            self.locks[phone] = asyncio.Lock()

        async with self.locks[phone]:
            # Adiciona mensagem ao buffer
            if phone not in self.message_buffer:
                self.message_buffer[phone] = []

            self.message_buffer[phone].append({
                "message": message,
                "timestamp": datetime.now()
            })

            logger.info(
                f"📩 Mensagem adicionada ao buffer [{phone}]: '{message}' "
                f"(total: {len(self.message_buffer[phone])} msgs)"
            )

            # Cancela timer anterior se existir
            if phone in self.timers and not self.timers[phone].done():
                self.timers[phone].cancel()
                logger.info(f"⏱️  Timer anterior cancelado para {phone}")

            # Cria novo timer
            self.timers[phone] = asyncio.create_task(
                self._process_after_delay(phone, callback)
            )

    async def _process_after_delay(
        self,
        phone: str,
        callback: Callable[[str, str], Any]
    ) -> None:
        """
        Aguarda delay e processa mensagens agrupadas.

        Args:
            phone: Telefone do usuário
            callback: Função a ser chamada
        """
        try:
            # Aguarda o tempo de debounce
            logger.info(f"⏳ Aguardando {self.wait_seconds}s de silêncio para {phone}...")
            await asyncio.sleep(self.wait_seconds)

            # Pega todas as mensagens do buffer
            async with self.locks[phone]:
                messages = self.message_buffer.get(phone, [])

                if not messages:
                    logger.warning(f"⚠️  Buffer vazio para {phone}")
                    return

                # Combina todas as mensagens
                combined_message = "\n".join([msg["message"] for msg in messages])

                logger.info(
                    f"✅ Processando {len(messages)} mensagem(ns) agrupada(s) de {phone}:\n"
                    f"   '{combined_message[:100]}...'"
                )

                # Limpa buffer
                self.message_buffer[phone] = []

            # Processa mensagem combinada
            await callback(phone, combined_message)

        except asyncio.CancelledError:
            logger.info(f"❌ Timer cancelado para {phone} (nova mensagem chegou)")
            # Não faz nada, novo timer foi criado
        except Exception as e:
            logger.error(f"💥 Erro ao processar mensagens de {phone}: {str(e)}", exc_info=True)

    def get_buffer_size(self, phone: str) -> int:
        """Retorna quantidade de mensagens no buffer de um usuário"""
        return len(self.message_buffer.get(phone, []))

    def clear_buffer(self, phone: str) -> None:
        """Limpa buffer de um usuário"""
        if phone in self.message_buffer:
            del self.message_buffer[phone]
        if phone in self.timers:
            if not self.timers[phone].done():
                self.timers[phone].cancel()
            del self.timers[phone]
        logger.info(f"🗑️  Buffer limpo para {phone}")


# Singleton global
message_debouncer = MessageDebouncer(wait_seconds=5.0)
