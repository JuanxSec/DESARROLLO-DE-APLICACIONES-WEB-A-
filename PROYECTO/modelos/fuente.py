"""Fuentes de inteligencia (tabla proveedores)."""

from modelos.base import consultar, filtro_vista


def listar_proveedores(ver='activos', q=''):
    """SELECT con JOIN al catálogo de tipos y conteo de servicios asociados."""
    sql = ('SELECT pr.id_proveedor, pr.nombre, pr.aporte, pr.correo, pr.telefono, pr.activo, '
           '       t.nombre AS tipo, COUNT(p.id_producto) AS total_productos '
           'FROM proveedores pr '
           'INNER JOIN tipos_proveedor t ON t.id_tipo = pr.id_tipo '
           'LEFT JOIN productos p ON p.id_proveedor = pr.id_proveedor '
           'WHERE ' + filtro_vista(ver, 'pr') + ' ')
    params = ()
    if q:
        sql += 'AND LOWER(pr.nombre) LIKE LOWER(%s) '
        params = ('%' + q + '%',)
    return consultar(sql + 'GROUP BY pr.id_proveedor, pr.nombre, pr.aporte, pr.correo, pr.telefono, '
                     'pr.activo, t.nombre ORDER BY pr.id_proveedor', params)
