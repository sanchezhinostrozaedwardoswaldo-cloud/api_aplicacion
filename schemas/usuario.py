from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    nombre_completo: str
    rol: str
    embarcacion_id: Optional[str] = None
    telefono: Optional[str] = None


class UsuarioCreate(UsuarioBase):
    email: EmailStr
    password: str


class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None
    embarcacion_id: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None


class UsuarioOut(UsuarioBase):
    id: str
    activo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True