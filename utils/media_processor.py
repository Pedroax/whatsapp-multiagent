"""Processadores de mídia (áudio, imagem, documento)"""
import io
import base64
import os
import sys
from typing import Optional, Dict, Any, Tuple
from loguru import logger
from openai import AsyncOpenAI
from config import settings

# Instala FFmpeg automaticamente no Windows (se necessário)
if sys.platform == "win32":
    try:
        from utils.install_ffmpeg import install_ffmpeg_windows
        install_ffmpeg_windows()
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível instalar FFmpeg automaticamente: {e}")


class MediaProcessor:
    """Processa diferentes tipos de mídia recebidos no WhatsApp"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def process_audio(self, audio_bytes: bytes, mimetype: str = "audio/ogg") -> Optional[str]:
        """
        Transcreve áudio usando Whisper da OpenAI

        Args:
            audio_bytes: Bytes do arquivo de áudio
            mimetype: Tipo MIME do áudio

        Returns:
            Texto transcrito ou None em caso de erro
        """
        import tempfile
        import subprocess
        from pathlib import Path

        temp_input = None
        temp_output = None

        try:
            logger.info(f"🎤 Transcrevendo áudio ({len(audio_bytes)} bytes), mimetype: {mimetype}")

            # Para OGG/Opus do WhatsApp, DEVE converter para MP3
            if "ogg" in mimetype.lower():
                logger.debug("🔄 Convertendo OGG/Opus para MP3 com FFmpeg...")

                # Cria arquivos temporários
                temp_input = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
                temp_output = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)

                # Salva OGG original
                temp_input.write(audio_bytes)
                temp_input.close()

                # Caminho do FFmpeg
                ffmpeg_path = Path(__file__).parent.parent / "ffmpeg" / "bin" / "ffmpeg.exe"

                # Converte usando FFmpeg
                cmd = [
                    str(ffmpeg_path),
                    "-i", temp_input.name,
                    "-vn",  # Sem vídeo
                    "-ar", "16000",  # Sample rate 16kHz (ideal para Whisper)
                    "-ac", "1",  # Mono
                    "-b:a", "32k",  # Bitrate
                    "-f", "mp3",
                    temp_output.name,
                    "-y"  # Sobrescrever
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    logger.error(f"❌ Erro FFmpeg: {result.stderr}")
                    return None

                # Lê MP3 convertido
                temp_output.close()
                with open(temp_output.name, "rb") as f:
                    mp3_bytes = f.read()

                audio_file = io.BytesIO(mp3_bytes)
                audio_file.name = "audio.mp3"

                logger.success(f"✅ Convertido para MP3: {len(mp3_bytes)} bytes")

            else:
                # Outros formatos já suportados
                extension_map = {
                    "audio/mpeg": "mp3",
                    "audio/mp4": "m4a",
                    "audio/wav": "wav",
                    "audio/x-m4a": "m4a"
                }
                extension = extension_map.get(mimetype, "mp3")

                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = f"audio.{extension}"

            # Transcreve usando Whisper
            transcription = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt"
            )

            transcribed_text = transcription.text
            logger.success(f"✅ Áudio transcrito: '{transcribed_text[:100]}...'")
            return transcribed_text

        except Exception as e:
            logger.error(f"💥 Erro ao transcrever áudio: {str(e)}")
            return None

        finally:
            # Limpa arquivos temporários
            if temp_input and os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            if temp_output and os.path.exists(temp_output.name):
                os.unlink(temp_output.name)

    async def process_image(self, image_bytes: bytes, user_question: Optional[str] = None) -> Optional[str]:
        """
        Analisa imagem usando GPT-4 Vision

        Args:
            image_bytes: Bytes da imagem
            user_question: Pergunta do usuário sobre a imagem (opcional)

        Returns:
            Descrição/análise da imagem ou None em caso de erro
        """
        try:
            logger.info(f"🖼️ Analisando imagem ({len(image_bytes)} bytes)...")

            # Converte para base64
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            # Monta prompt
            if user_question:
                prompt = f"O usuário enviou esta imagem com a pergunta: '{user_question}'\n\nAnalise a imagem e responda a pergunta."
            else:
                prompt = (
                    "Descreva esta imagem de forma detalhada. "
                    "Se for uma bateria de carro, identifique marca, modelo, amperagem e características visíveis. "
                    "Se for outro tipo de imagem, descreva o conteúdo relevante."
                )

            # Chama GPT-4 Vision
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",  # gpt-4o tem visão integrada
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            analysis = response.choices[0].message.content
            logger.success(f"✅ Imagem analisada: '{analysis[:100]}...'")
            return analysis

        except Exception as e:
            logger.error(f"💥 Erro ao analisar imagem: {str(e)}")
            return None

    async def process_document(self, doc_bytes: bytes, filename: str) -> Optional[str]:
        """
        Extrai texto de documentos (PDF, DOCX, TXT)

        Args:
            doc_bytes: Bytes do documento
            filename: Nome do arquivo (usado para determinar tipo)

        Returns:
            Texto extraído ou None em caso de erro
        """
        try:
            logger.info(f"📄 Processando documento: {filename} ({len(doc_bytes)} bytes)...")

            file_extension = filename.lower().split(".")[-1]

            # TXT - direto
            if file_extension == "txt":
                text = doc_bytes.decode("utf-8", errors="ignore")
                logger.success(f"✅ Texto extraído: {len(text)} caracteres")
                return text

            # PDF
            elif file_extension == "pdf":
                import PyPDF2
                pdf_file = io.BytesIO(doc_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())

                full_text = "\n".join(text_parts)
                logger.success(f"✅ PDF extraído: {len(full_text)} caracteres")
                return full_text

            # DOCX
            elif file_extension in ["docx", "doc"]:
                import docx
                doc_file = io.BytesIO(doc_bytes)
                doc = docx.Document(doc_file)

                text_parts = []
                for paragraph in doc.paragraphs:
                    text_parts.append(paragraph.text)

                full_text = "\n".join(text_parts)
                logger.success(f"✅ DOCX extraído: {len(full_text)} caracteres")
                return full_text

            else:
                logger.warning(f"⚠️ Tipo de documento não suportado: {file_extension}")
                return f"[Documento {filename} recebido, mas tipo não suportado para extração de texto]"

        except Exception as e:
            logger.error(f"💥 Erro ao processar documento: {str(e)}")
            return None

    async def extract_media_from_webhook(self, message_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Extrai mídia do payload do webhook

        Args:
            message_data: Dicionário com dados da mensagem

        Returns:
            Tupla (tipo_midia, media_data, mimetype_ou_filename)
            - Se base64 disponível: retorna bytes decodificados
            - Se não: retorna dict com url/mediaKey para download posterior
            Tipos: "audio", "image", "document", None
        """
        try:
            # Áudio
            if "audioMessage" in message_data:
                audio_data = message_data["audioMessage"]
                logger.debug(f"🎤 Áudio detectado no webhook: {audio_data.keys()}")

                # Base64 pode estar em audioMessage ou no message_data (Evolution API v2)
                base64_audio = audio_data.get("base64") or message_data.get("base64")
                mimetype = audio_data.get("mimetype", "audio/ogg")

                if base64_audio:
                    # Remove prefixo data:audio/...;base64, se existir
                    if "," in base64_audio:
                        base64_audio = base64_audio.split(",")[1]
                    audio_bytes = base64.b64decode(base64_audio)
                    logger.info(f"🎤 Áudio com base64: {mimetype}, {len(audio_bytes)} bytes")
                    return ("audio", audio_bytes, mimetype)
                else:
                    # Sem base64, retorna dados para download
                    logger.warning(f"⚠️ Áudio sem base64. URL: {audio_data.get('url', 'N/A')}")
                    return ("audio", audio_data, mimetype)

            # Imagem
            elif "imageMessage" in message_data:
                image_data = message_data["imageMessage"]
                logger.debug(f"🖼️ Imagem detectada no webhook: {image_data.keys()}")

                # Base64 pode estar em imageMessage ou no message_data
                base64_image = image_data.get("base64") or message_data.get("base64")
                mimetype = image_data.get("mimetype", "image/jpeg")

                if base64_image:
                    if "," in base64_image:
                        base64_image = base64_image.split(",")[1]
                    image_bytes = base64.b64decode(base64_image)
                    logger.info(f"🖼️ Imagem com base64: {mimetype}, {len(image_bytes)} bytes")
                    return ("image", image_bytes, mimetype)
                else:
                    logger.warning(f"⚠️ Imagem sem base64. URL: {image_data.get('url', 'N/A')}")
                    return ("image", image_data, mimetype)

            # Documento
            elif "documentMessage" in message_data:
                doc_data = message_data["documentMessage"]
                filename = doc_data.get("fileName", "document")
                logger.debug(f"📄 Documento detectado no webhook: {filename}")

                # Base64 pode estar em documentMessage ou no message_data
                base64_doc = doc_data.get("base64") or message_data.get("base64")
                mimetype = doc_data.get("mimetype", "application/octet-stream")

                if base64_doc:
                    if "," in base64_doc:
                        base64_doc = base64_doc.split(",")[1]
                    doc_bytes = base64.b64decode(base64_doc)
                    logger.info(f"📄 Documento com base64: {filename}, {len(doc_bytes)} bytes")
                    return ("document", doc_bytes, filename)
                else:
                    logger.warning(f"⚠️ Documento sem base64. URL: {doc_data.get('url', 'N/A')}")
                    return ("document", doc_data, filename)

            return (None, None, None)

        except Exception as e:
            logger.error(f"💥 Erro ao extrair mídia: {str(e)}")
            return (None, None, None)
