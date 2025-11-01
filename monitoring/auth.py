"""Sistema de autenticação híbrido (IP + Login) para dashboard de monitoramento"""
from fastapi import Request, HTTPException, status
from typing import Optional
import secrets
import base64
from loguru import logger
from config import settings


# Lista de IPs permitidos (acesso direto sem login)
ALLOWED_IPS = [
    "127.0.0.1",  # Localhost
    "::1",  # Localhost IPv6
    # Adicione seu IP aqui depois que descobrir
]

# Credenciais de login (fallback)
MONITOR_USERNAME = getattr(settings, "monitor_username", "admin")
MONITOR_PASSWORD = getattr(settings, "monitor_password", "Alice@Monitor2025")


def get_client_ip(request: Request) -> str:
    """
    Extrai IP real do cliente (considerando proxies)

    Args:
        request: Request do FastAPI

    Returns:
        IP do cliente
    """
    # Tenta pegar IP de headers de proxy (nginx, cloudflare, etc)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For pode ter múltiplos IPs, pega o primeiro (cliente real)
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback: IP direto da conexão
    if request.client:
        return request.client.host

    return "unknown"


def check_ip_whitelist(request: Request) -> bool:
    """
    Verifica se IP do cliente está na whitelist

    Args:
        request: Request do FastAPI

    Returns:
        True se IP está permitido, False caso contrário
    """
    client_ip = get_client_ip(request)

    if client_ip in ALLOWED_IPS:
        logger.info(f"✅ Acesso monitor autorizado via IP whitelist: {client_ip}")
        return True

    logger.debug(f"⏸️ IP {client_ip} não está na whitelist")
    return False


def parse_basic_auth(authorization: str) -> Optional[tuple[str, str]]:
    """
    Parse manual do header Authorization Basic

    Args:
        authorization: Header Authorization completo

    Returns:
        Tupla (username, password) ou None se inválido
    """
    try:
        logger.info(f"🔍 DEBUG parse_basic_auth - Input: '{authorization[:100]}'")

        # Remove "Basic " do início
        parts = authorization.split(" ", 1)
        logger.info(f"🔍 DEBUG parse_basic_auth - Split parts: {len(parts)}")

        if len(parts) != 2:
            logger.warning(f"⚠️ DEBUG - Authorization header não tem 2 partes")
            return None

        scheme, credentials = parts
        logger.info(f"🔍 DEBUG parse_basic_auth - Scheme: '{scheme}', Creds length: {len(credentials)}")

        if scheme.lower() != "basic":
            logger.warning(f"⚠️ DEBUG - Scheme não é 'basic': '{scheme}'")
            return None

        # Decodifica base64
        decoded = base64.b64decode(credentials).decode("utf-8")
        logger.info(f"🔍 DEBUG parse_basic_auth - Decoded: '{decoded}'")

        parts = decoded.split(":", 1)
        if len(parts) != 2:
            logger.warning(f"⚠️ DEBUG - Decoded não tem 2 partes (username:password)")
            return None

        username, password = parts
        logger.info(f"✅ DEBUG parse_basic_auth - Parsed successfully: user='{username}', pass length={len(password)}")

        return (username, password)
    except Exception as e:
        logger.error(f"💥 Erro ao parsear Basic Auth: {e}")
        return None


def verify_credentials(username: str, password: str) -> bool:
    """
    Verifica credenciais de login

    Args:
        username: Nome de usuário
        password: Senha

    Returns:
        True se credenciais válidas, False caso contrário
    """
    # DEBUG: Log das credenciais recebidas vs esperadas
    logger.info(f"🔍 DEBUG Auth - Recebido: user='{username}', pass='{password}'")
    logger.info(f"🔍 DEBUG Auth - Esperado: user='{MONITOR_USERNAME}', pass='{MONITOR_PASSWORD}'")
    logger.info(f"🔍 DEBUG Auth - Username match: {username == MONITOR_USERNAME}")
    logger.info(f"🔍 DEBUG Auth - Password match: {password == MONITOR_PASSWORD}")

    # Usa secrets.compare_digest para prevenir timing attacks
    username_match = secrets.compare_digest(
        username.encode("utf-8"),
        MONITOR_USERNAME.encode("utf-8")
    )

    password_match = secrets.compare_digest(
        password.encode("utf-8"),
        MONITOR_PASSWORD.encode("utf-8")
    )

    if username_match and password_match:
        logger.info(f"✅ Acesso monitor autorizado via login: {username}")
        return True

    logger.warning(f"❌ Tentativa de login falhou: user={username}, username_match={username_match}, password_match={password_match}")
    return False


async def require_auth(request: Request) -> bool:
    """
    Middleware de autenticação híbrido: IP Whitelist OU Login

    Fluxo:
    1. Verifica se IP está na whitelist → autoriza direto
    2. Se não, verifica header Authorization
    3. Valida credenciais → autoriza
    4. Se falhar ambos → HTTP 401 Unauthorized

    Args:
        request: Request do FastAPI

    Returns:
        True se autorizado

    Raises:
        HTTPException: 401 se não autorizado
    """
    client_ip = get_client_ip(request)
    logger.info(f"🔍 DEBUG require_auth - IP: {client_ip}")

    # Estratégia 1: IP Whitelist (mais prático)
    if check_ip_whitelist(request):
        logger.info(f"✅ DEBUG - IP na whitelist, acesso liberado")
        return True

    # Estratégia 2: Login (fallback)
    authorization = request.headers.get("Authorization")
    logger.info(f"🔍 DEBUG - Authorization header: {authorization[:50] if authorization else 'None'}...")

    if authorization:
        logger.info(f"🔍 DEBUG - Tentando parsear Basic Auth...")
        parsed = parse_basic_auth(authorization)
        logger.info(f"🔍 DEBUG - Parse result: {parsed is not None}")

        if parsed:
            username, password = parsed
            logger.info(f"🔍 DEBUG - Verificando credenciais para user: {username}")
            if verify_credentials(username, password):
                return True
        else:
            logger.warning(f"⚠️ DEBUG - Falha ao parsear Authorization header")

    # Nenhuma estratégia funcionou: pede login
    logger.warning(f"🚫 Acesso negado ao monitor: IP={client_ip}")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticação necessária",
        headers={"WWW-Authenticate": 'Basic realm="Alice Monitor"'},
    )


def add_ip_to_whitelist(ip: str):
    """
    Adiciona IP à whitelist dinamicamente

    Args:
        ip: Endereço IP a ser adicionado
    """
    if ip not in ALLOWED_IPS:
        ALLOWED_IPS.append(ip)
        logger.success(f"✅ IP {ip} adicionado à whitelist de monitoramento")


def remove_ip_from_whitelist(ip: str):
    """
    Remove IP da whitelist

    Args:
        ip: Endereço IP a ser removido
    """
    if ip in ALLOWED_IPS and ip not in ["127.0.0.1", "::1"]:  # Nunca remove localhost
        ALLOWED_IPS.remove(ip)
        logger.info(f"🗑️ IP {ip} removido da whitelist")
