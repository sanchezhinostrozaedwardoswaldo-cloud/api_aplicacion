import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base, TimestampMixin


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("inventario.usuarios.id", ondelete="CASCADE"), nullable=False)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("inventario.pedidos.id", ondelete="CASCADE"))
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    leido = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PlantillaPedido(Base, TimestampMixin):
    __tablename__ = "plantillas_pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    embarcacion_id = Column(UUID(as_uuid=True), ForeignKey("inventario.embarcaciones.id"), nullable=False)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("inventario.usuarios.id"), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)


class PlantillaItem(Base):
    __tablename__ = "plantilla_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plantilla_id = Column(UUID(as_uuid=True), ForeignKey("inventario.plantillas_pedido.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("inventario.productos.id"), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False)
    notas = Column(Text)