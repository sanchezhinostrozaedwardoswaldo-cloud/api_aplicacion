import json
from datetime import datetime, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings
from database import get_db
from models.operaciones import Usuario

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    token = credentials.credentials
    try:
        # Intentamos parsear la clave secreta como JSON (por si es un JWK)
        try:
            key = json.loads(settings.SUPABASE_JWT_SECRET)
        except (ValueError, TypeError):
            # Si no es JSON, usamos la cadena tal cual (para HS256)
            key = settings.SUPABASE_JWT_SECRET

        payload = jwt.decode(
            token,
            key,
            algorithms=["HS256", "ES256"],
            audience="authenticated",
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError as e:
        print(f"❌ [Auth] Error decodificando token: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    result = await db.execute(select(Usuario).where(Usuario.id == user_id, Usuario.activo == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.rol not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return user


require_admin = RoleChecker(["admin"])
require_supervisor = RoleChecker(["admin", "supervisor"])
require_chef = RoleChecker(["admin", "chef"])
require_chef_or_bodeguero = RoleChecker(["admin", "chef", "bodeguero"])
require_any = RoleChecker(["admin", "supervisor", "chef", "bodeguero"])