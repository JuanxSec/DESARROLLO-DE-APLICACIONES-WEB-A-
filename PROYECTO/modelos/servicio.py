"""Servicios CTI (tabla productos)."""

from modelos.base import consultar, filtro_vista


def servicios_publicos(limite=None, categoria=None, q=''):
    sql = ('SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.stock, p.imagen, '
           '       c.nombre AS categoria, e.nombre AS estado '
           'FROM productos p '
           'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
           'INNER JOIN estados e ON e.id_estado = p.id_estado '
           "WHERE p.activo = TRUE AND e.nombre <> 'Inactivo' ")
    params = []
    if categoria:
        sql += 'AND c.id_categoria = %s '
        params.append(categoria)
    if q:
        sql += 'AND LOWER(p.nombre) LIKE LOWER(%s) '
        params.append('%' + q + '%')
    sql += 'ORDER BY p.stock = 0, p.id_producto'
    filas = consultar(sql, tuple(params))
    return filas[:limite] if limite else filas


def listar_productos(ver='activos', q=''):
    """SELECT con JOIN a categorías, estados y fuentes."""
    sql = ('SELECT p.id_producto, p.nombre, p.precio, p.stock, p.descripcion, p.imagen, p.activo, '
           '       c.nombre AS categoria, e.nombre AS estado, pr.nombre AS proveedor '
           'FROM productos p '
           'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
           'INNER JOIN estados e ON e.id_estado = p.id_estado '
           'LEFT JOIN proveedores pr ON pr.id_proveedor = p.id_proveedor '
           'WHERE ' + filtro_vista(ver, 'p') + ' ')
    params = ()
    if q:
        sql += 'AND (LOWER(p.nombre) LIKE LOWER(%s) OR LOWER(c.nombre) LIKE LOWER(%s)) '
        params = ('%' + q + '%', '%' + q + '%')
    return consultar(sql + 'ORDER BY p.id_producto', params)
