import uuid
from sqlalchemy import (
    Column, String, Text, Boolean, ForeignKey, DateTime, Date, Integer, Numeric, func
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from models.base import Base, TimestampMixin


class Embarcacion(Base, TimestampMixin):
    __tablename__ = "embarcaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    matricula = Column(String(50))
    capacidad_kg = Column(Numeric(10, 2))
    activo = Column(Boolean, default=True, nullable=False)


class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True)
    nombre_completo = Column(String(150), nullable=False)
    rol = Column(String(20), nullable=False, default="chef")  # enum rol_usuario
    embarcacion_id = Column(UUID(as_uuid=True), ForeignKey("inventario.embarcaciones.id"))
    telefono = Column(String(20))
    activo = Column(Boolean, default=True, nullable=False)


class Pedido(Base, TimestampMixin):
    __tablename__ = "pedidos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero = Column(String(20), unique=True, nullable=False)
    embarcacion_id = Column(UUID(as_uuid=True), ForeignKey("inventario.embarcaciones.id"), nullable=False)
    solicitante_id = Column(UUID(as_uuid=True), ForeignKey("inventario.usuarios.id"), nullable=False)
    aprobado_por_id = Column(UUID(as_uuid=True), ForeignKey("inventario.usuarios.id"))
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("inventario.proveedores.id"))
    estado = Column(
        ENUM(
            'borrador', 'enviado', 'confirmado', 'en_transito', 'recibido', 'cancelado', 
            name='estado_pedido', schema='inventario'
        ), 
        default="borrador", 
        nullable=False
    )  # enum estado_pedido
    fecha_pedido = Column(DateTime(timezone=True), server_default=func.now())
    fecha_requerida = Column(Date)
    fecha_aprobacion = Column(DateTime(timezone=True))
    fecha_envio = Column(DateTime(timezone=True))
    fecha_recepcion = Column(DateTime(timezone=True))
    observaciones = Column(Text)
    notas_aprobacion = Column(Text)
    notas_recepcion = Column(Text)
    total_items = Column(Integer, default=0)
    subtotal = Column(Numeric(14, 4), default=0)
    igv = Column(Numeric(14, 4), default=0)
    total = Column(Numeric(14, 4), default=0)
    pdf_url = Column(Text)


class PedidoItem(Base, TimestampMixin):
    __tablename__ = "pedido_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("inventario.pedidos.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("inventario.productos.id"), nullable=False)
    cantidad_solicitada = Column(Numeric(10, 2), nullable=False)
    cantidad_aprobada = Column(Numeric(10, 2))
    cantidad_recibida = Column(Numeric(10, 2))
    precio_unitario = Column(Numeric(12, 4))
    subtotal = Column(Numeric(14, 4))
    igv = Column(Numeric(14, 4))
    total = Column(Numeric(14, 4))
    notas = Column(Text)


class PedidoHistorial(Base):
    __tablename__ = "pedido_historial"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("inventario.pedidos.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("inventario.usuarios.id"), nullable=False)
    estado_anterior = Column(String(20))
    estado_nuevo = Column(String(20), nullable=False)
    comentario = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())