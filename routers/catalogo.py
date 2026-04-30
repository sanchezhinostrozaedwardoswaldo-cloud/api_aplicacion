from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
from database import get_db
from auth import require_any, require_admin, get_current_user
from models.operaciones import Usuario
from models.catalogo import Familia, SubFamilia, Producto
from schemas.catalogo import FamiliaOut, SubFamiliaOut, ProductoOut, ProductoCreate, ProductoUpdate, CatalogoProductoOut
from exceptions import APIException

router = APIRouter(prefix="/catalogo", tags=["Catálogo"])


@router.get("/familias", response_model=List[FamiliaOut])
async def list_familias(
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    result = await db.execute(
        select(Familia).where(Familia.activo == True).order_by(Familia.orden, Familia.nombre)
    )
    return result.scalars().all()


@router.get("/familias/{id}/subfamilias", response_model=List[SubFamiliaOut])
async def list_subfamilias(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    result = await db.execute(
        select(SubFamilia)
        .where(SubFamilia.familia_id == id, SubFamilia.activo == True)
        .order_by(SubFamilia.orden, SubFamilia.nombre)
    )
    return result.scalars().all()


@router.get("/productos", response_model=List[CatalogoProductoOut])
async def list_productos(
    familia_id: Optional[str] = Query(None),
    sub_familia_id: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    # Usamos la vista v_catalogo_productos directamente para máxima eficiencia
    from sqlalchemy import text
    conditions = ["p.activo = TRUE"]
    params = {}
    
    if familia_id:
        conditions.append("p.familia_id = :familia_id")
        params["familia_id"] = familia_id
    if sub_familia_id:
        conditions.append("p.sub_familia_id = :sub_familia_id")
        params["sub_familia_id"] = sub_familia_id
    if busqueda:
        conditions.append("p.nombre ILIKE :busqueda")
        params["busqueda"] = f"%{busqueda}%"
    
    where_clause = " AND ".join(conditions)
    query = text(f"""
        SELECT * FROM inventario.v_catalogo_productos p
        WHERE {where_clause}
        ORDER BY p.familia, p.sub_familia, p.nombre
        LIMIT 500
    """)
    
    result = await db.execute(query, params)
    return result.mappings().all()


@router.get("/productos/{id}", response_model=ProductoOut)
async def get_producto(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_any),
):
    result = await db.execute(select(Producto).where(Producto.id == id))
    prod = result.scalar_one_or_none()
    if not prod:
        raise APIException("Producto no encontrado", 404)
    return prod


@router.post("/productos", response_model=ProductoOut, status_code=201)
async def create_producto(
    data: ProductoCreate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    prod = Producto(**data.model_dump())
    db.add(prod)
    await db.commit()
    await db.refresh(prod)
    return prod


@router.patch("/productos/{id}", response_model=ProductoOut)
async def update_producto(
    id: str,
    data: ProductoUpdate,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Producto).where(Producto.id == id))
    prod = result.scalar_one_or_none()
    if not prod:
        raise APIException("Producto no encontrado", 404)
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(prod, k, v)
    
    await db.commit()
    await db.refresh(prod)
    return prod


@router.delete("/productos/{id}", status_code=204)
async def delete_producto(
    id: str,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_admin),
):
    result = await db.execute(select(Producto).where(Producto.id == id))
    prod = result.scalar_one_or_none()
    if not prod:
        raise APIException("Producto no encontrado", 404)
    prod.activo = False
    await db.commit()
    return None