"""Instala FFmpeg automaticamente no Windows"""
import os
import sys
import zipfile
import urllib.request
from pathlib import Path
from loguru import logger


def install_ffmpeg_windows():
    """Baixa e instala FFmpeg no Windows"""
    try:
        # Diretório para FFmpeg
        ffmpeg_dir = Path(__file__).parent.parent / "ffmpeg"
        ffmpeg_bin = ffmpeg_dir / "bin"
        ffmpeg_exe = ffmpeg_bin / "ffmpeg.exe"

        # Se já existe, adiciona ao PATH e retorna
        if ffmpeg_exe.exists():
            logger.info(f"✅ FFmpeg já instalado em: {ffmpeg_exe}")
            os.environ["PATH"] = f"{ffmpeg_bin};{os.environ['PATH']}"
            return True

        logger.info("📥 Baixando FFmpeg (pode demorar alguns minutos)...")

        # URL do FFmpeg essentials (menor)
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

        # Baixa
        zip_path = ffmpeg_dir.parent / "ffmpeg.zip"
        ffmpeg_dir.mkdir(exist_ok=True)

        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        logger.info("✅ Download concluído, extraindo...")

        # Extrai
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(ffmpeg_dir.parent)

        # Renomeia pasta (vem com nome ffmpeg-X.X-essentials_build)
        import shutil
        extracted_folders = list(ffmpeg_dir.parent.glob("ffmpeg-*-essentials_build"))
        if extracted_folders:
            if ffmpeg_dir.exists():
                shutil.rmtree(ffmpeg_dir)
            shutil.move(str(extracted_folders[0]), str(ffmpeg_dir))

        # Remove zip
        zip_path.unlink()

        # Adiciona ao PATH
        if ffmpeg_exe.exists():
            os.environ["PATH"] = f"{ffmpeg_bin};{os.environ['PATH']}"
            logger.success(f"✅ FFmpeg instalado com sucesso em: {ffmpeg_exe}")
            return True
        else:
            logger.error("❌ FFmpeg não encontrado após instalação")
            return False

    except Exception as e:
        logger.error(f"💥 Erro ao instalar FFmpeg: {str(e)}")
        return False


if __name__ == "__main__":
    install_ffmpeg_windows()
