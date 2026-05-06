from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text, func
from typing import Optional, List
from datetime import date
from database import get_db
from auth import get_current_user, require_chef, require_supervisor, require_any, require_chef_or_bodeguero
from models.operaciones import Usuario, Pedido, PedidoItem, PedidoHistorial
from models.utilidades import Notificacion
from schemas.pedido import (
    PedidoCreate, PedidoOut, PedidoUpdate, PedidoResumenOut,
    PedidoAprobar, PedidoRecibir, PedidoHistorialOut
)
from services.pedido_service import validar_pedido_propiedad, transicionar_estado, crear_notificacion
from exceptions import APIException
from fastapi import Response

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.get("", response_model=List[PedidoResumenOut])
async def list_pedidos(
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    # Usamos la vista v_pedidos_resumen para listados eficientes
    conditions = ["1=1"]
    params = {}
    
    if user.rol == "chef":
        conditions.append("embarcacion_id = :emb_id")
        params["emb_id"] = str(user.embarcacion_id)
    
    if estado:
        conditions.append("estado = :estado")
        params["estado"] = estado
    if fecha_desde:
        conditions.append("fecha_pedido >= :fd")
        params["fd"] = fecha_desde
    if fecha_hasta:
        conditions.append("fecha_pedido <= :fh")
        params["fh"] = fecha_hasta
    
    where_clause = " AND ".join(conditions)
    query = text(f"""
        SELECT * FROM inventario.v_pedidos_resumen
        WHERE {where_clause}
        ORDER BY fecha_pedido DESC
        LIMIT 200
    """)
    
    result = await db.execute(query, params)
    return result.mappings().all()


@router.post("", response_model=PedidoOut, status_code=201)
async def create_pedido(
    data: PedidoCreate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    if not user.embarcacion_id:
        raise APIException("El chef debe tener una embarcación asignada", 400)
    
    # El trigger generar_numero_pedido() creará el número automáticamente
    pedido = Pedido(
        embarcacion_id=user.embarcacion_id,
        solicitante_id=user.id,
        fecha_requerida=data.fecha_requerida,
        observaciones=data.observaciones,
    )
    db.add(pedido)
    await db.commit()
    await db.refresh(pedido)
    return pedido


@router.get("/{id}", response_model=PedidoOut)
async def get_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    pedido = await validar_pedido_propiedad(id, user, db)
    return pedido


@router.patch("/{id}", response_model=PedidoOut)
async def update_pedido(
    id: str,
    data: PedidoUpdate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    pedido = await validar_pedido_propiedad(id, user, db, estados_permitidos=["borrador"])
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(pedido, k, v)
    
    await db.commit()
    await db.refresh(pedido)
    return pedido


@router.post("/{id}/enviar", response_model=PedidoOut)
async def enviar_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    pedido = await validar_pedido_propiedad(id, user, db, estados_permitidos=["borrador"])
    
    # Verificar que tenga items
    result = await db.execute(select(PedidoItem).where(PedidoItem.pedido_id == id))
    items = result.scalars().all()
    if not items:
        raise APIException("No se puede enviar un pedido sin items", 400)
    
    pedido = await transicionar_estado(db, pedido, "enviado", str(user.id))
    
    # Notificar a supervisores (simplificado: notificar a todos los supervisores)
    sups = await db.execute(select(Usuario).where(Usuario.rol == "supervisor", Usuario.activo == True))
    for sup in sups.scalars().all():
        await crear_notificacion(
            db, str(sup.id), 
            "Nuevo pedido enviado", 
            f"El pedido {pedido.numero} fue enviado por {user.nombre_completo}",
            str(pedido.id)
        )
    
    return pedido


@router.post("/{id}/aprobar", response_model=PedidoOut)
async def aprobar_pedido(
    id: str,
    data: PedidoAprobar,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_supervisor),
):
    pedido = await validar_pedido_propiedad(id, user, db, estados_permitidos=["enviado"])
    
    # Actualizar items aprobados si vienen
    if data.items:
        result = await db.execute(select(PedidoItem).where(PedidoItem.pedido_id == id))
        items = {str(i.id): i for i in result.scalars().all()}
        # Nota: En una implementación real se mapearía por producto_id o item_id
        # Aquí simplificamos asumiendo que el frontend envía la estructura correcta
    
    pedido = await transicionar_estado(
        db, pedido, "confirmado", str(user.id),
        campos_extra={
            "aprobado_por_id": user.id,
            "notas_aprobacion": data.notas_aprobacion,
            "fecha_aprobacion": func.now()
        }
    )
    
    await crear_notificacion(
        db, str(pedido.solicitante_id),
        "Pedido aprobado",
        f"Tu pedido {pedido.numero} ha sido aprobado",
        str(pedido.id)
    )
    
    return pedido


@router.post("/{id}/despachar", response_model=PedidoOut)
async def despachar_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_supervisor),
):
    pedido = await validar_pedido_propiedad(id, user, db, estados_permitidos=["confirmado"])
    pedido = await transicionar_estado(
        db, pedido, "en_transito", str(user.id),
        campos_extra={"fecha_envio": func.now()}
    )
    return pedido


@router.post("/{id}/recibir", response_model=PedidoOut)
async def recibir_pedido(
    id: str,
    data: PedidoRecibir,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef_or_bodeguero),
):
    pedido = await validar_pedido_propiedad(id, user, db, estados_permitidos=["en_transito"])
    pedido = await transicionar_estado(
        db, pedido, "recibido", str(user.id),
        campos_extra={
            "notas_recepcion": data.notas_recepcion,
            "fecha_recepcion": func.now()
        }
    )
    return pedido


@router.post("/{id}/cancelar", response_model=PedidoOut)
async def cancelar_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    pedido = await validar_pedido_propiedad(id, user, db)
    if pedido.estado == "recibido":
        raise APIException("No se puede cancelar un pedido ya recibido", 400)
    
    # Solo chef propietario, supervisor o admin pueden cancelar
    if user.rol == "chef" and str(pedido.solicitante_id) != str(user.id):
        raise APIException("Solo el creador puede cancelar", 403)
    
    pedido = await transicionar_estado(db, pedido, "cancelado", str(user.id))
    return pedido


@router.get("/{id}/historial", response_model=List[PedidoHistorialOut])
async def historial_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    await validar_pedido_propiedad(id, user, db)
    result = await db.execute(
        select(PedidoHistorial)
        .where(PedidoHistorial.pedido_id == id)
        .order_by(PedidoHistorial.created_at)
    )
    return result.scalars().all()


@router.get("/{id}/pdf")
async def pdf_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    from services.pdf_service import generar_pdf_pedido
    await validar_pedido_propiedad(id, user, db)
    pdf_bytes = await generar_pdf_pedido(db, id)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=pedido_{id}.pdf"}
    )