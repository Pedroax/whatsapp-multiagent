"""Cliente para Evolution API"""
import httpx
import base64
from typing import Optional, Dict, Any
from loguru import logger
from config import settings


class EvolutionAPI:
    """Cliente para Evolution API (WhatsApp)"""

    def __init__(self):
        self.base_url = settings.evolution_api_url.rstrip('/')
        self.api_key = settings.evolution_api_key
        self.instance = settings.evolution_instance_name

        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

        logger.info(f"✅ Evolution API configurada: {self.base_url}")

    async def send_text(
        self,
        phone: str,
        message: str,
        delay: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto

        Args:
            phone: Número com DDI (ex: 5561999999999)
            message: Texto da mensagem
            delay: Delay em milissegundos (opcional)

        Returns:
            Resposta da API
        """
        url = f"{self.base_url}/message/sendText/{self.instance}"

        payload = {
            "number": phone,
            "text": message
        }

        if delay:
            payload["delay"] = delay

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200 or response.status_code == 201:
                    logger.success(f"✅ Mensagem enviada para {phone}")
                    return response.json()
                else:
                    logger.error(
                        f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}"
                    )
                    return {
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"💥 Erro ao enviar mensagem: {str(e)}")
            return {"error": str(e)}

    async def send_typing(self, phone: str, duration: int = 3000) -> Dict[str, Any]:
        """
        Simula digitação (typing indicator)

        Args:
            phone: Número do destinatário
            duration: Duração em milissegundos

        Returns:
            Resposta da API
        """
        url = f"{self.base_url}/chat/sendPresence/{self.instance}"

        payload = {
            "number": phone,
            "presence": "composing",
            "delay": duration
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code in [200, 201]:
                    logger.debug(f"⌨️ Typing enviado para {phone}")
                    return response.json()
                else:
                    logger.warning(f"⚠️ Erro ao enviar typing: {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"💥 Erro ao enviar typing: {str(e)}")
            return {"error": str(e)}

    async def send_with_typing(
        self,
        phone: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Envia mensagem com simulação de digitação

        Args:
            phone: Número do destinatário
            message: Texto da mensagem

        Returns:
            Resposta do envio
        """
        # Calcula duração do typing baseado no tamanho da mensagem
        typing_duration = min(len(message) * 50, 5000)  # Max 5s

        # Envia typing (não aguarda resposta)
        await self.send_typing(phone, typing_duration)

        # Aguarda um pouco e envia mensagem
        import asyncio
        await asyncio.sleep(typing_duration / 1000)

        return await self.send_text(phone, message)

    async def get_instance_info(self) -> Dict[str, Any]:
        """Recupera informações da instância"""
        url = f"{self.base_url}/instance/connectionState/{self.instance}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"ℹ️ Estado da instância: {data.get('state')}")
                    return data
                else:
                    logger.error(f"❌ Erro ao obter info: {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"💥 Erro ao obter info: {str(e)}")
            return {"error": str(e)}

    async def download_media(self, message_key_dict: Dict[str, Any], media_url: str = "") -> Optional[bytes]:
        """
        Baixa mídia do WhatsApp (áudio, imagem, documento)

        Args:
            message_key_dict: Dict com id e remoteJid da mensagem
            media_url: URL direta da mídia (se disponível)

        Returns:
            Bytes da mídia ou None em caso de erro
        """
        # Método 1: Se tem URL, tenta baixar diretamente
        if media_url and media_url.startswith("http"):
            try:
                logger.debug(f"🔽 Tentando baixar mídia via URL: {media_url[:100]}...")
                async with httpx.AsyncClient() as client:
                    response = await client.get(media_url, timeout=30.0)
                    if response.status_code == 200:
                        logger.success(f"✅ Mídia baixada via URL: {len(response.content)} bytes")
                        return response.content
            except Exception as e:
                logger.warning(f"⚠️ Falha ao baixar via URL, tentando API: {str(e)}")

        # Método 2: Usa endpoint da Evolution API
        url = f"{self.base_url}/chat/getBase64FromMediaMessage/{self.instance}"

        payload = {
            "message": {
                "key": message_key_dict
            },
            "convertToMp4": False
        }

        try:
            logger.debug(f"🔽 Baixando mídia via Evolution API: {message_key_dict.get('id')}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )

                logger.debug(f"📥 Status download: {response.status_code}")

                if response.status_code in [200, 201]:
                    data = response.json()
                    base64_media = data.get("base64")

                    if base64_media:
                        # Remove prefixo data:...;base64, se existir
                        if "," in base64_media:
                            base64_media = base64_media.split(",")[1]

                        media_bytes = base64.b64decode(base64_media)
                        logger.success(f"✅ Mídia baixada via API: {len(media_bytes)} bytes")
                        return media_bytes
                    else:
                        logger.error("❌ Campo 'base64' não encontrado na resposta")
                        logger.debug(f"Response: {data}")
                        return None
                else:
                    logger.error(f"❌ Erro HTTP {response.status_code}: {response.text[:500]}")
                    return None

        except Exception as e:
            logger.error(f"💥 Erro ao baixar mídia: {str(e)}")
            return None
