from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import date
from database import get_db
from auth import get_current_user, require_supervisor
from models.operaciones import Usuario, Pedido, PedidoItem
from models.utilidades import Notificacion
from models.catalogo import Producto
from schemas.reporte import NotificacionOut, ProductoFrecuenteOut, ReportePedidoFiltro
from exceptions import APIException

router = APIRouter(prefix="/reportes", tags=["Reportes y Notificaciones"])


# ============ NOTIFICACIONES ============

@router.get("/notificaciones", response_model=List[NotificacionOut])
async def list_notificaciones(
    solo_no_leidas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    q = select(Notificacion).where(Notificacion.usuario_id == user.id)
    if solo_no_leidas:
        q = q.where(Notificacion.leido == False)
    q = q.order_by(Notificacion.created_at.desc()).limit(50)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/notificaciones/{id}/leer", response_model=NotificacionOut)
async def marcar_leida(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    result = await db.execute(
        select(Notificacion).where(Notificacion.id == id, Notificacion.usuario_id == user.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise APIException("Notificación no encontrada", 404)
    notif.leido = True
    await db.commit()
    await db.refresh(notif)
    return notif


@router.patch("/notificaciones/leer-todas", status_code=204)
async def marcar_todas_leidas(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    await db.execute(
        Notificacion.__table__.update()
        .where(and_(Notificacion.usuario_id == user.id, Notificacion.leido == False))
        .values(leido=True)
    )
    await db.commit()
    return None


# ============ REPORTES ============

@router.get("/pedidos")
async def reporte_pedidos(
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    embarcacion_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_supervisor),
):
    from sqlalchemy import text
    conditions = ["1=1"]
    params = {}
    if fecha_desde:
        conditions.append("fecha_pedido >= :fd")
        params["fd"] = fecha_desde
    if fecha_hasta:
        conditions.append("fecha_pedido <= :fh")
        params["fh"] = fecha_hasta
    if embarcacion_id:
        conditions.append("embarcacion_id = :emb")
        params["emb"] = embarcacion_id
    if estado:
        conditions.append("estado = :est")
        params["est"] = estado
    
    where_clause = " AND ".join(conditions)
    query = text(f"""
        SELECT * FROM inventario.v_pedidos_resumen
        WHERE {where_clause}
        ORDER BY fecha_pedido DESC
    """)
    result = await db.execute(query, params)
    return result.mappings().all()


@router.get("/productos-frecuentes", response_model=List[ProductoFrecuenteOut])
async def productos_frecuentes(
    embarcacion_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_supervisor),
):
    q = (
        select(
            Producto.id.label("producto_id"),
            Producto.nombre.label("producto_nombre"),
            func.coalesce(func.sum(PedidoItem.cantidad_solicitada), 0).label("total_cantidad"),
            func.count(func.distinct(PedidoItem.pedido_id)).label("total_pedidos"),
        )
        .join(PedidoItem, PedidoItem.producto_id == Producto.id)
        .join(Pedido, Pedido.id == PedidoItem.pedido_id)
        .where(Pedido.estado != "cancelado")
    )
    
    if embarcacion_id:
        q = q.where(Pedido.embarcacion_id == embarcacion_id)
    
    q = q.group_by(Producto.id, Producto.nombre).order_by(func.sum(PedidoItem.cantidad_solicitada).desc()).limit(limit)
    result = await db.execute(q)
    return result.mappings().all()