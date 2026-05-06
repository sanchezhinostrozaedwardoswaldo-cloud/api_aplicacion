import uuid
from sqlalchemy import Column, String, Text, Boolean, SmallInteger, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base, TimestampMixin

class Familia(Base, TimestampMixin):
    __tablename__ = "familias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(10), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    icono = Column(String(50))
    orden = Column(SmallInteger, default=0, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)


class SubFamilia(Base, TimestampMixin):
    __tablename__ = "sub_familias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(10), unique=True, nullable=False)
    familia_id = Column(UUID(as_uuid=True), ForeignKey("inventario.familias.id", ondelete="RESTRICT"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    icono = Column(String(50))
    orden = Column(SmallInteger, default=0, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)


class Proveedor(Base, TimestampMixin):
    __tablename__ = "proveedores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ruc = Column(String(20), unique=True)
    razon_social = Column(String(150), nullable=False)
    nombre_comercial = Column(String(100))
    contacto = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(150))
    direccion = Column(Text)
    activo = Column(Boolean, default=True, nullable=False)


class Producto(Base, TimestampMixin):
    __tablename__ = "productos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    sub_familia_id = Column(UUID(as_uuid=True), ForeignKey("inventario.sub_familias.id", ondelete="RESTRICT"), nullable=False)
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("inventario.proveedores.id"))
    presentacion = Column(String(50), nullable=False, default="otro")  # tipo_presentacion enum
    unidad_medida = Column(String(20), default="UND")
    contenido_neto = Column(String(50))
    tipo_impuesto = Column(String(20), default="afecto", nullable=False)  # enum
    precio_referencia = Column(Numeric(12, 4))
    stock_minimo = Column(Numeric(10, 2), default=0)
    imagen_url = Column(Text)
    codigo_barras = Column(String(50))
    activo = Column(Boolean, default=True, nullable=False)