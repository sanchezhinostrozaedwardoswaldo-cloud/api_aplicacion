from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class NotificacionOut(BaseModel):
    id: str
    usuario_id: str
    pedido_id: Optional[str] = None
    titulo: str
    mensaje: str
    leido: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReportePedidoFiltro(BaseModel):
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    embarcacion_id: Optional[str] = None
    estado: Optional[str] = None


class ProductoFrecuenteOut(BaseModel):
    producto_id: str
    producto_nombre: str
    total_cantidad: Decimal
    total_pedidos: int

    class Config:
        from_attributes = True