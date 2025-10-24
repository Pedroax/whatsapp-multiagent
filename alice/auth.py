"""
Sistema de Autenticação e Autorização
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Header
from supabase import create_client, Client
import bcrypt
import jwt
import secrets
from loguru import logger
from config import settings


# Configurações JWT
JWT_SECRET = "sua-chave-secreta-super-segura-aqui-mudar-em-producao"  # TODO: Mover para .env
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class AuthService:
    """Serviço de autenticação"""

    def __init__(self):
        self.supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)

    def hash_password(self, password: str) -> str:
        """Gera hash bcrypt da senha"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica se senha bate com hash"""
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def generate_token(self, usuario_id: str, email: str, role: str, departamento: Optional[str]) -> str:
        """Gera token JWT"""
        payload = {
            "usuario_id": usuario_id,
            "email": email,
            "role": role,
            "departamento": departamento,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica e decodifica token JWT"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Faz login e retorna token + dados do usuário

        Returns:
            {
                "token": "jwt_token_here",
                "usuario": {...dados do usuario...}
            }
        """
        try:
            # Buscar usuário por email
            result = self.supabase.table("usuarios")\
                .select("*")\
                .eq("email", email)\
                .eq("status", "ativo")\
                .single()\
                .execute()

            if not result.data:
                raise HTTPException(status_code=401, detail="Email ou senha incorretos")

            usuario = result.data

            # Verificar senha
            if not self.verify_password(password, usuario["senha_hash"]):
                raise HTTPException(status_code=401, detail="Email ou senha incorretos")

            # Gerar token JWT
            token = self.generate_token(
                usuario_id=usuario["id"],
                email=usuario["email"],
                role=usuario["role"],
                departamento=usuario.get("departamento_slug")
            )

            # Atualizar último acesso
            self.supabase.table("usuarios").update({
                "ultimo_acesso": datetime.utcnow().isoformat()
            }).eq("id", usuario["id"]).execute()

            # Salvar sessão
            self.supabase.table("sessoes").insert({
                "usuario_id": usuario["id"],
                "token": token,
                "expira_em": (datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)).isoformat()
            }).execute()

            logger.info(f"✅ Login bem-sucedido: {email} ({usuario['role']})")

            # Remover senha_hash da resposta
            usuario.pop("senha_hash", None)

            return {
                "token": token,
                "usuario": usuario
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro no login: {e}")
            raise HTTPException(status_code=500, detail="Erro ao fazer login")

    async def get_current_user(self, authorization: str = Header(None)) -> Dict[str, Any]:
        """
        Middleware para pegar usuário atual do token

        Usage:
            @app.get("/rota-protegida")
            async def rota(usuario = Depends(auth_service.get_current_user)):
                print(usuario["email"])
        """
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token não fornecido")

        token = authorization.replace("Bearer ", "")

        # Verificar token
        payload = self.verify_token(token)

        # Buscar usuário completo
        result = self.supabase.table("usuarios")\
            .select("*")\
            .eq("id", payload["usuario_id"])\
            .eq("status", "ativo")\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        usuario = result.data
        usuario.pop("senha_hash", None)

        return usuario

    async def logout(self, token: str):
        """Remove sessão do banco"""
        try:
            self.supabase.table("sessoes").delete().eq("token", token).execute()
            logger.info("✅ Logout realizado")
        except Exception as e:
            logger.error(f"❌ Erro no logout: {e}")


# Instância global
auth_service = AuthService()


# Dependency para rotas protegidas
async def require_auth(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    Dependency que requer autenticação

    Usage:
        @app.get("/rota-protegida")
        async def rota(usuario = Depends(require_auth)):
            return {"usuario": usuario["email"]}
    """
    return await auth_service.get_current_user(authorization)


# Dependency para super admin apenas
async def require_super_admin(usuario: Dict = Depends(require_auth)) -> Dict[str, Any]:
    """Requer que usuário seja super admin"""
    if usuario["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Acesso negado: Super Admin necessário")
    return usuario
