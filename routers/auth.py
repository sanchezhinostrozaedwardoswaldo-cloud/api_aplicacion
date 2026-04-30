from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from database import get_db
from config import settings
from models.operaciones import Usuario
from schemas.auth import LoginRequest, LoginResponse, RefreshRequest, UsuarioMe
from auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            json={"email": data.email, "password": data.password},
            headers={"apikey": settings.SUPABASE_ANON_KEY},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        tokens = r.json()

    user_id = tokens.get("user", {}).get("id")
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    perfil = result.scalar_one_or_none()

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=tokens["expires_in"],
        user=UsuarioMe(
            id=str(perfil.id) if perfil else user_id,
            email=data.email,
            nombre_completo=perfil.nombre_completo if perfil else "",
            rol=perfil.rol if perfil else "chef",
            embarcacion_id=str(perfil.embarcacion_id) if perfil and perfil.embarcacion_id else None,
            telefono=perfil.telefono if perfil else None,
        ),
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh(data: RefreshRequest):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": data.refresh_token},
            headers={"apikey": settings.SUPABASE_ANON_KEY},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Refresh token inválido")
        tokens = r.json()

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=tokens["expires_in"],
        user=None,  # Se puede enriquecer si hace falta
    )


@router.get("/me", response_model=UsuarioMe)
async def me(current_user: Usuario = Depends(get_current_user)):
    return UsuarioMe(
        id=str(current_user.id),
        nombre_completo=current_user.nombre_completo,
        rol=current_user.rol,
        embarcacion_id=str(current_user.embarcacion_id) if current_user.embarcacion_id else None,
        telefono=current_user.telefono,
    )