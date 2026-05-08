from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from database import get_db
from auth import get_current_user, require_chef
from models.operaciones import Usuario, Pedido, PedidoItem
from models.catalogo import Producto
from schemas.pedido import PedidoItemCreate, PedidoItemUpdate, PedidoItemOut
from services.pedido_service import validar_pedido_propiedad
from exceptions import APIException

router = APIRouter(prefix="/pedidos/{pedido_id}/items", tags=["Items de Pedido"])


@router.get("", response_model=List[PedidoItemOut])
async def list_items(
    pedido_id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    await validar_pedido_propiedad(pedido_id, user, db)
    result = await db.execute(
        select(PedidoItem, Producto.codigo, Producto.nombre)
        .join(Producto, Producto.id == PedidoItem.producto_id)
        .where(PedidoItem.pedido_id == pedido_id)
    )
    items = []
    for row in result.all():
        item, cod, nom = row
        items.append({
            **{c.name: getattr(item, c.name) for c in item.__table__.columns},
            "producto_codigo": cod,
            "producto_nombre": nom,
        })
    return items


@router.post("", response_model=PedidoItemOut, status_code=201)
async def add_item(
    pedido_id: str,
    data: PedidoItemCreate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    pedido = await validar_pedido_propiedad(pedido_id, user, db, estados_permitidos=["borrador"])
    
    # Validar que producto exista
    prod = await db.execute(select(Producto).where(Producto.id == data.producto_id, Producto.activo == True))
    if not prod.scalar_one_or_none():
        raise APIException("Producto no encontrado o inactivo", 404)
    
    # Validar que no esté duplicado
    exist = await db.execute(
        select(PedidoItem).where(
            PedidoItem.pedido_id == pedido_id,
            PedidoItem.producto_id == data.producto_id
        )
    )
    if exist.scalar_one_or_none():
        raise APIException("El producto ya existe en el pedido", 400)
    
    # Precio snapshot del producto
    producto = await db.get(Producto, data.producto_id)
    precio = producto.precio_referencia or 0
    
    item = PedidoItem(
        pedido_id=pedido_id,
        producto_id=data.producto_id,
        cantidad_solicitada=data.cantidad_solicitada,
        precio_unitario=precio,
        notas=data.notas,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    # El trigger recalcular_totales_pedido() actualizará la cabecera automáticamente
    return item


@router.patch("/{item_id}", response_model=PedidoItemOut)
async def update_item(
    pedido_id: str,
    item_id: str,
    data: PedidoItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    await validar_pedido_propiedad(pedido_id, user, db, estados_permitidos=["borrador"])
    
    result = await db.execute(
        select(PedidoItem).where(PedidoItem.id == item_id, PedidoItem.pedido_id == pedido_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise APIException("Item no encontrado", 404)
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    pedido_id: str,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_chef),
):
    await validar_pedido_propiedad(pedido_id, user, db, estados_permitidos=["borrador"])
    
    result = await db.execute(
        select(PedidoItem).where(PedidoItem.id == item_id, PedidoItem.pedido_id == pedido_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise APIException("Item no encontrado", 404)
    
    await db.delete(item)
    await db.commit()
    # El trigger recalculará totales automáticamente
    return None