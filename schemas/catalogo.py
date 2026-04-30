from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FamiliaOut(BaseModel):
    id: str
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    orden: int
    activo: bool

    class Config:
        from_attributes = True


class SubFamiliaOut(BaseModel):
    id: str
    codigo: str
    familia_id: str
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    orden: int
    activo: bool

    class Config:
        from_attributes = True


class ProductoBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    sub_familia_id: str
    proveedor_id: Optional[str] = None
    presentacion: str
    unidad_medida: Optional[str] = "UND"
    contenido_neto: Optional[str] = None
    tipo_impuesto: str = "afecto"
    precio_referencia: Optional[float] = None
    stock_minimo: float = 0
    imagen_url: Optional[str] = None
    codigo_barras: Optional[str] = None
    activo: bool = True


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    proveedor_id: Optional[str] = None
    presentacion: Optional[str] = None
    unidad_medida: Optional[str] = None
    contenido_neto: Optional[str] = None
    tipo_impuesto: Optional[str] = None
    precio_referencia: Optional[float] = None
    stock_minimo: Optional[float] = None
    imagen_url: Optional[str] = None
    codigo_barras: Optional[str] = None
    activo: Optional[bool] = None


class ProductoOut(ProductoBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CatalogoProductoOut(BaseModel):
    id: str
    codigo: str
    nombre: str
    presentacion: str
    contenido_neto: Optional[str] = None
    precio_referencia: Optional[float] = None
    stock_minimo: Optional[float] = None
    imagen_url: Optional[str] = None
    tipo_impuesto: str
    sub_familia_id: str
    sub_familia: str
    sub_familia_codigo: str
    familia_id: str
    familia: str
    familia_codigo: str
    familia_icono: Optional[str] = None
    sub_familia_icono: Optional[str] = None

    class Config:
        from_attributes = True