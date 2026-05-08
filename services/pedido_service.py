from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from exceptions import APIException
from models.operaciones import Pedido, PedidoItem, PedidoHistorial, Usuario
from models.catalogo import Producto
from models.utilidades import Notificacion
from schemas.pedido import PedidoItemAprobar, PedidoItemRecibir


async def validar_pedido_propiedad(pedido_id: str, user: Usuario, db: AsyncSession, estados_permitidos: Optional[list] = None):
    result = await db.execute(select(Pedido).where(Pedido.id == pedido_id))
    pedido = result.scalar_one_or_none()
    if not pedido:
        raise APIException("Pedido no encontrado", 404, "NOT_FOUND")
    
    if user.rol == "chef" and pedido.embarcacion_id != user.embarcacion_id:
        raise APIException("No tienes acceso a este pedido", 403, "FORBIDDEN")
    
    if estados_permitidos and pedido.estado not in estados_permitidos:
        raise APIException(f"Acción no permitida en estado {pedido.estado}", 400, "INVALID_STATE")
    
    return pedido


async def transicionar_estado(
    db: AsyncSession,
    pedido: Pedido,
    nuevo_estado: str,
    usuario_id: str,
    comentario: Optional[str] = None,
    campos_extra: Optional[dict] = None
):
    """
    Actualiza el estado del pedido. 
    El trigger registrar_historial_pedido() se encargará de auditar.
    """
    pedido.estado = nuevo_estado
    
    if campos_extra:
        for k, v in campos_extra.items():
            setattr(pedido, k, v)
    
    await db.commit()
    await db.refresh(pedido)
    return pedido


async def crear_notificacion(
    db: AsyncSession,
    usuario_id: str,
    titulo: str,
    mensaje: str,
    pedido_id: Optional[str] = None
):
    notif = Notificacion(
        usuario_id=usuario_id,
        pedido_id=pedido_id,
        titulo=titulo,
        mensaje=mensaje,
    )
    db.add(notif)
    await db.commit()
    return notif