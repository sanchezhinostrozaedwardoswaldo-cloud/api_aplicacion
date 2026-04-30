from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base
from exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from routers import auth, catalogo, pedidos, items, plantillas, usuarios, reportes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear tablas si no existen (opcional, útil para dev)
    # En producción con Supabase ya tienes el schema, así que puedes omitir esto
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        pass
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Sistema de Inventario para Embarcación",
    description="API REST para Representaciones Fray Martín SRL",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS para la app móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restringir en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Excepciones globales
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Routers
app.include_router(auth.router)
app.include_router(catalogo.router)
app.include_router(pedidos.router)
app.include_router(items.router)
app.include_router(plantillas.router)
app.include_router(usuarios.router)
app.include_router(reportes.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}