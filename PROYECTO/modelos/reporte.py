"""Consultas del reporte de servicios contratados (JOIN de facturas, detalle, productos y categorías)."""

from datetime import timedelta
from decimal import Decimal

from modelos.base import consultar, expr_mes


def datos_reporte(desde, hasta):
    """Servicios contratados en el periodo: facturas + detalle + productos + categorías."""
    condicion = ('FROM detalle_factura d '
                 'INNER JOIN facturas f ON f.id_factura = d.id_factura '
                 'INNER JOIN productos p ON p.id_producto = d.id_producto '
                 'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
                 'INNER JOIN estados e ON e.id_estado = f.id_estado '
                 "WHERE f.activo = TRUE AND e.nombre <> 'Anulada' "
                 'AND f.fecha >= %s AND f.fecha < %s ')
    params = (desde, hasta + timedelta(days=1))
    por_servicio = consultar(
        'SELECT p.nombre AS servicio, c.nombre AS categoria, COUNT(DISTINCT f.id_factura) AS suscripciones, '
        '       SUM(d.cantidad) AS cupos, SUM(d.cantidad * d.precio_unitario) AS ingresos '
        + condicion + 'GROUP BY p.id_producto, p.nombre, c.nombre ORDER BY ingresos DESC', params)
    por_organizacion = consultar(
        'SELECT cl.nombre AS organizacion, COUNT(DISTINCT f.id_factura) AS suscripciones, '
        '       SUM(d.cantidad * d.precio_unitario) AS ingresos '
        + condicion.replace('WHERE', 'INNER JOIN clientes cl ON cl.id_cliente = f.id_cliente WHERE', 1)
        + 'GROUP BY cl.id_cliente, cl.nombre ORDER BY ingresos DESC', params)
    por_mes = consultar(
        'SELECT ' + expr_mes('f.fecha') + ' AS mes, SUM(d.cantidad * d.precio_unitario) AS ingresos '
        + condicion + 'GROUP BY ' + expr_mes('f.fecha') + ' ORDER BY mes', params)
    total = sum(Decimal(str(f['ingresos'] or 0)) for f in por_servicio)
    return por_servicio, por_organizacion, por_mes, total
