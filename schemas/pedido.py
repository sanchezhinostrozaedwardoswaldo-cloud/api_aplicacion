from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class PedidoItemBase(BaseModel):
    producto_id: str
    cantidad_solicitada: Decimal = Field(gt=0)
    notas: Optional[str] = None


class PedidoItemCreate(PedidoItemBase):
    pass


class PedidoItemUpdate(BaseModel):
    cantidad_solicitada: Optional[Decimal] = Field(default=None, gt=0)
    notas: Optional[str] = None


class PedidoItemAprobar(BaseModel):
    cantidad_aprobada: Decimal = Field(gt=0)
    precio_unitario: Optional[Decimal] = None


class PedidoItemRecibir(BaseModel):
    cantidad_recibida: Decimal = Field(ge=0)


class PedidoItemOut(BaseModel):
    id: str
    pedido_id: str
    producto_id: str
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    cantidad_solicitada: Decimal
    cantidad_aprobada: Optional[Decimal] = None
    cantidad_recibida: Optional[Decimal] = None
    precio_unitario: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    igv: Optional[Decimal] = None
    total: Optional[Decimal] = None
    notas: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PedidoBase(BaseModel):
    embarcacion_id: str
    fecha_requerida: Optional[date] = None
    observaciones: Optional[str] = None


class PedidoCreate(BaseModel):
    fecha_requerida: Optional[date] = None
    observaciones: Optional[str] = None


class PedidoUpdate(BaseModel):
    fecha_requerida: Optional[date] = None
    observaciones: Optional[str] = None


class PedidoAprobar(BaseModel):
    notas_aprobacion: Optional[str] = None
    items: Optional[List[PedidoItemAprobar]] = None


class PedidoRecibir(BaseModel):
    notas_recepcion: Optional[str] = None
    items: Optional[List[PedidoItemRecibir]] = None


class PedidoOut(BaseModel):
    id: str
    numero: str
    embarcacion_id: str
    solicitante_id: str
    aprobado_por_id: Optional[str] = None
    proveedor_id: Optional[str] = None
    estado: str
    fecha_pedido: datetime
    fecha_requerida: Optional[date] = None
    fecha_aprobacion: Optional[datetime] = None
    fecha_envio: Optional[datetime] = None
    fecha_recepcion: Optional[datetime] = None
    observaciones: Optional[str] = None
    notas_aprobacion: Optional[str] = None
    notas_recepcion: Optional[str] = None
    total_items: int
    subtotal: Decimal
    igv: Decimal
    total: Decimal
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PedidoResumenOut(BaseModel):
    id: str
    numero: str
    estado: str
    fecha_pedido: datetime
    fecha_requerida: Optional[date] = None
    total_items: int
    total: Decimal
    observaciones: Optional[str] = None
    embarcacion: Optional[str] = None
    solicitante: Optional[str] = None
    aprobado_por: Optional[str] = None

    class Config:
        from_attributes = True


class PedidoHistorialOut(BaseModel):
    id: str
    pedido_id: str
    usuario_id: str
    estado_anterior: Optional[str] = None
    estado_nuevo: str
    comentario: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PlantillaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class PlantillaCreate(PlantillaBase):
    items: List[PedidoItemBase]


class PlantillaOut(PlantillaBase):
    id: str
    embarcacion_id: str
    creado_por_id: str
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PlantillaItemOut(BaseModel):
    id: str
    plantilla_id: str
    producto_id: str
    producto_nombre: Optional[str] = None
    cantidad: Decimal
    notas: Optional[str] = None

    class Config:
        from_attributes = True


class PlantillaDetailOut(PlantillaOut):
    items: List[PlantillaItemOut] = []