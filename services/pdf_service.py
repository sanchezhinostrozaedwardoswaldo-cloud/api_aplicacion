from jinja2 import Template
from weasyprint import HTML
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Response
import tempfile
import os


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
        .header { border-bottom: 3px solid #1a5276; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { color: #1a5276; margin: 0; }
        .meta { margin: 20px 0; }
        .meta td { padding: 5px 15px 5px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #1a5276; color: white; padding: 10px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #ddd; }
        .totales { margin-top: 30px; text-align: right; }
        .totales table { width: 300px; margin-left: auto; }
        .totales td { border: none; padding: 5px; }
        .footer { margin-top: 50px; font-size: 0.9em; color: #666; border-top: 1px solid #ccc; padding-top: 20px; }
        .estado { display: inline-block; padding: 5px 15px; border-radius: 15px; background: #d4edda; color: #155724; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ORDEN DE PEDIDO</h1>
        <p>Representaciones Fray Martín SRL</p>
    </div>
    
    <div class="meta">
        <table>
            <tr><td><strong>N° Pedido:</strong></td><td>{{ pedido.numero }}</td></tr>
            <tr><td><strong>Embarcación:</strong></td><td>{{ pedido.embarcacion }}</td></tr>
            <tr><td><strong>Solicitante:</strong></td><td>{{ pedido.solicitante }}</td></tr>
            <tr><td><strong>Fecha:</strong></td><td>{{ pedido.fecha_pedido }}</td></tr>
            <tr><td><strong>Requerido:</strong></td><td>{{ pedido.fecha_requerida or 'No especificada' }}</td></tr>
            <tr><td><strong>Estado:</strong></td><td><span class="estado">{{ pedido.estado.upper() }}</span></td></tr>
        </table>
    </div>

    <table>
        <thead>
            <tr>
                <th>Familia / Sub-Familia</th>
                <th>Producto</th>
                <th>Presentación</th>
                <th>Cantidad</th>
                <th>Precio Unit.</th>
                <th>Subtotal</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.familia }} / {{ item.sub_familia }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td>{{ item.presentacion }}</td>
                <td>{{ item.cantidad_solicitada }}</td>
                <td>S/ {{ "%.2f"|format(item.precio_unitario or 0) }}</td>
                <td>S/ {{ "%.2f"|format(item.subtotal or 0) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="totales">
        <table>
            <tr><td><strong>Subtotal:</strong></td><td>S/ {{ "%.2f"|format(pedido.subtotal) }}</td></tr>
            <tr><td><strong>IGV (18%):</strong></td><td>S/ {{ "%.2f"|format(pedido.igv) }}</td></tr>
            <tr><td><strong>TOTAL:</strong></td><td><strong>S/ {{ "%.2f"|format(pedido.total) }}</strong></td></tr>
        </table>
    </div>

    <div class="footer">
        <p>Documento generado automáticamente por el Sistema de Inventario para Embarcación.</p>
    </div>
</body>
</html>
"""


async def generar_pdf_pedido(db: AsyncSession, pedido_id: str) -> bytes:
    # Usamos la vista v_pedido_detalle_completo para obtener todo
    query_items = text("""
        SELECT * FROM inventario.v_pedido_detalle_completo
        WHERE pedido_id = :pedido_id
        ORDER BY familia, sub_familia, producto_nombre
    """)
    result = await db.execute(query_items, {"pedido_id": pedido_id})
    items = result.mappings().all()

    query_pedido = text("""
        SELECT p.*, e.nombre as embarcacion, u.nombre_completo as solicitante
        FROM inventario.pedidos p
        JOIN inventario.embarcaciones e ON e.id = p.embarcacion_id
        JOIN inventario.usuarios u ON u.id = p.solicitante_id
        WHERE p.id = :pedido_id
    """)
    result_p = await db.execute(query_pedido, {"pedido_id": pedido_id})
    pedido = result_p.mappings().one_or_none()

    if not pedido:
        raise ValueError("Pedido no encontrado")

    template = Template(HTML_TEMPLATE)
    html_out = template.render(pedido=dict(pedido), items=[dict(i) for i in items])

    pdf = HTML(string=html_out).write_pdf()
    return pdf