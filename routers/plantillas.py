from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from database import get_db
from auth import get_current_user, require_chef
from models.operaciones import Usuario, Pedido
from models.utilidades import PlantillaPedido, PlantillaItem
from schemas.pedido import PlantillaCreate, PlantillaOut, PlantillaDetailOut, PedidoOut
from exceptions import APIException
from models.operaciones import Pedido, PedidoItem

router = APIRouter(prefix="/plantillas", tags=["Plantillas"])


@router.get("", response_model=List[PlantillaOut])
async def list_plantillas(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    result = await db.execute(
        select(PlantillaPedido)
        .where(
            PlantillaPedido.embarcacion_id == user.embarcacion_id,
            PlantillaPedido.activo == True
        )
        .order_by(PlantillaPedido.nombre)
    )
    return result.scalars().all()


@router.post("", response_model=PlantillaOut, status_code=201)
async def create_plantilla(
    data: PlantillaCreate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    if not user.embarcacion_id:
        raise APIException("Chef sin embarcación asignada", 400)
    
    plantilla = PlantillaPedido(
        nombre=data.nombre,
        descripcion=data.descripcion,
        embarcacion_id=user.embarcacion_id,
        creado_por_id=user.id,
    )
    db.add(plantilla)
    await db.flush()
    
    for it in data.items:
        pi = PlantillaItem(
            plantilla_id=plantilla.id,
            producto_id=it.producto_id,
            cantidad=it.cantidad_solicitada,
            notas=it.notas,
        )
        db.add(pi)
    
    await db.commit()
    await db.refresh(plantilla)
    return plantilla


@router.get("/{id}", response_model=PlantillaDetailOut)
async def get_plantilla(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    result = await db.execute(
        select(PlantillaPedido).where(
            PlantillaPedido.id == id,
            PlantillaPedido.embarcacion_id == user.embarcacion_id
        )
    )
    plantilla = result.scalar_one_or_none()
    if not plantilla:
        raise APIException("Plantilla no encontrada", 404)
    
    items_res = await db.execute(
        select(PlantillaItem).where(PlantillaItem.plantilla_id == id)
    )
    items = items_res.scalars().all()
    
    return {
        **{c.name: getattr(plantilla, c.name) for c in plantilla.__table__.columns},
        "items": items,
    }


@router.delete("/{id}", status_code=204)
async def delete_plantilla(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    result = await db.execute(
        select(PlantillaPedido).where(
            PlantillaPedido.id == id,
            PlantillaPedido.embarcacion_id == user.embarcacion_id
        )
    )
    plantilla = result.scalar_one_or_none()
    if not plantilla:
        raise APIException("Plantilla no encontrada", 404)
    
    plantilla.activo = False
    await db.commit()
    return None


@router.post("/{id}/usar", response_model=PedidoOut, status_code=201)
async def usar_plantilla(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    if not user.embarcacion_id:
        raise APIException("Chef sin embarcación asignada", 400)
    
    result = await db.execute(
        select(PlantillaPedido).where(
            PlantillaPedido.id == id,
            PlantillaPedido.embarcacion_id == user.embarcacion_id,
            PlantillaPedido.activo == True
        )
    )
    plantilla = result.scalar_one_or_none()
    if not plantilla:
        raise APIException("Plantilla no encontrada", 404)
    
    # Crear pedido en borrador
    pedido = Pedido(
        embarcacion_id=user.embarcacion_id,
        solicitante_id=user.id,
        estado="borrador",
    )
    db.add(pedido)
    await db.flush()
    
    # Copiar items
    items_res = await db.execute(
        select(PlantillaItem).where(PlantillaItem.plantilla_id == id)
    )
    for it in items_res.scalars().all():
        pi = PedidoItem(
            pedido_id=pedido.id,
            producto_id=it.producto_id,
            cantidad_solicitada=it.cantidad,
            notas=it.notas,
        )
        db.add(pi)
    
    await db.commit()
    await db.refresh(pedido)
    return pedido