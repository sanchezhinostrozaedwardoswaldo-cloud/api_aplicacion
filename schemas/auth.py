from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UsuarioMe"


class RefreshRequest(BaseModel):
    refresh_token: str


class UsuarioMe(BaseModel):
    id: str
    email: Optional[str] = None
    nombre_completo: str
    rol: str
    embarcacion_id: Optional[str] = None
    embarcacion_nombre: Optional[str] = None
    telefono: Optional[str] = None

    class Config:
        from_attributes = True