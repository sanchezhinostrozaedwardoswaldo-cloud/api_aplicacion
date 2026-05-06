from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import httpx
from database import get_db
from config import settings
from auth import require_admin
from models.operaciones import Usuario
from schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut
from exceptions import APIException

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=List[UsuarioOut])
async def list_usuarios(
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Usuario).order_by(Usuario.nombre_completo))
    return result.scalars().all()


@router.post("", response_model=UsuarioOut, status_code=201)
async def create_usuario(
    data: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    # Crear usuario en Supabase Auth vía Admin API
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            json={
                "email": data.email,
                "password": data.password,
                "email_confirm": True,
            },
            headers={
                "apikey": settings.SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            },
        )
        if r.status_code not in (200, 201):
            raise APIException(f"Error creando usuario en Auth: {r.text}", 400)
        auth_user = r.json()
        user_id = auth_user["id"]

    # Crear perfil
    perfil = Usuario(
        id=user_id,
        nombre_completo=data.nombre_completo,
        rol=data.rol,
        embarcacion_id=data.embarcacion_id,
        telefono=data.telefono,
    )
    db.add(perfil)
    await db.commit()
    await db.refresh(perfil)
    return perfil


@router.get("/{id}", response_model=UsuarioOut)
async def get_usuario(
    id: str,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Usuario).where(Usuario.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise APIException("Usuario no encontrado", 404)
    return user


@router.patch("/{id}", response_model=UsuarioOut)
async def update_usuario(
    id: str,
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Usuario).where(Usuario.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise APIException("Usuario no encontrado", 404)
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{id}", status_code=204)
async def delete_usuario(
    id: str,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Usuario).where(Usuario.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise APIException("Usuario no encontrado", 404)
    
    user.activo = False
    await db.commit()
    return None