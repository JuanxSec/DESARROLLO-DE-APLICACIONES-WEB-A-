"""Suscripciones: cabecera (facturas) y detalle (detalle_factura, relación N:N con productos)."""

from modelos.base import consultar, ejecutar, filtro_vista


def recalcular_total(id_factura):
    """Actualiza el total de la factura a partir de su detalle (relación N:N)."""
    fila = consultar(
        'SELECT COALESCE(SUM(cantidad * precio_unitario), 0) AS total '
        'FROM detalle_factura WHERE id_factura = %s',
        (id_factura,), uno=True
    )
    ejecutar('UPDATE facturas SET total = %s WHERE id_factura = %s',
             (fila['total'], id_factura))


def listar_facturas(ver='activos', q=''):
    """SELECT con JOIN a organizaciones y estados, y conteo de líneas de detalle."""
    sql = ('SELECT f.id_factura, f.codigo, f.servicio, f.fecha, f.total, f.activo, '
           '       c.nombre AS cliente, e.nombre AS estado, COUNT(d.id_detalle) AS lineas '
           'FROM facturas f '
           'INNER JOIN clientes c ON c.id_cliente = f.id_cliente '
           'INNER JOIN estados e ON e.id_estado = f.id_estado '
           'LEFT JOIN detalle_factura d ON d.id_factura = f.id_factura '
           'WHERE ' + filtro_vista(ver, 'f') + ' ')
    params = ()
    if q:
        sql += 'AND (LOWER(f.codigo) LIKE LOWER(%s) OR LOWER(c.nombre) LIKE LOWER(%s)) '
        params = ('%' + q + '%', '%' + q + '%')
    return consultar(sql + 'GROUP BY f.id_factura, f.codigo, f.servicio, f.fecha, f.total, f.activo, '
                     'c.nombre, e.nombre ORDER BY f.id_factura DESC', params)


def siguiente_codigo():
    """Propone el siguiente código FAC-NNN a partir del mayor existente."""
    numeros = []
    for fila in consultar("SELECT codigo FROM facturas WHERE codigo LIKE 'FAC-%'"):
        try:
            numeros.append(int(fila['codigo'].split('-')[1]))
        except (IndexError, ValueError):
            pass
    return 'FAC-%03d' % (max(numeros or [0]) + 1)


def datos_factura(id_factura):
    return consultar(
        'SELECT f.id_factura, f.codigo, f.servicio, f.fecha, f.total, f.activo, '
        '       c.nombre AS cliente, c.ruc, c.correo, c.telefono, e.nombre AS estado, '
        "       CONCAT(pr.nombre, ' / ', ca.nombre, ' / ', pa.nombre) AS ubicacion "
        'FROM facturas f '
        'INNER JOIN clientes c ON c.id_cliente = f.id_cliente '
        'INNER JOIN estados e ON e.id_estado = f.id_estado '
        'INNER JOIN parroquias pa ON pa.id_parroquia = c.id_parroquia '
        'INNER JOIN cantones ca ON ca.id_canton = pa.id_canton '
        'INNER JOIN provincias pr ON pr.id_provincia = ca.id_provincia '
        'WHERE f.id_factura = %s', (id_factura,), uno=True)


def lineas_factura(id_factura):
    return consultar(
        'SELECT d.id_detalle, d.id_producto, d.cantidad, d.precio_unitario, '
        '       (d.cantidad * d.precio_unitario) AS subtotal, p.nombre AS producto, c.nombre AS categoria '
        'FROM detalle_factura d '
        'INNER JOIN productos p ON p.id_producto = d.id_producto '
        'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
        'WHERE d.id_factura = %s ORDER BY d.id_detalle', (id_factura,))
