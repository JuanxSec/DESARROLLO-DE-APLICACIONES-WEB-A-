"""Boletines de ciberinteligencia (tabla boletines)."""

from modelos.base import consultar, filtro_vista


def boletines_publicos(limite=None):
    filas = consultar(
        'SELECT b.id_boletin, b.titulo, b.resumen, b.nivel, b.referencia, b.fecha, '
        '       c.nombre AS categoria, pr.nombre AS fuente '
        'FROM boletines b '
        'INNER JOIN categorias c ON c.id_categoria = b.id_categoria '
        'LEFT JOIN proveedores pr ON pr.id_proveedor = b.id_proveedor '
        'WHERE b.activo = TRUE ORDER BY b.fecha DESC, b.id_boletin DESC')
    return filas[:limite] if limite else filas


def listar_boletines(ver='activos', q=''):
    sql = ('SELECT b.id_boletin, b.titulo, b.resumen, b.nivel, b.referencia, b.fecha, b.activo, '
           '       c.nombre AS categoria, pr.nombre AS fuente '
           'FROM boletines b '
           'INNER JOIN categorias c ON c.id_categoria = b.id_categoria '
           'LEFT JOIN proveedores pr ON pr.id_proveedor = b.id_proveedor '
           'WHERE ' + filtro_vista(ver, 'b') + ' ')
    params = ()
    if q:
        sql += 'AND LOWER(b.titulo) LIKE LOWER(%s) '
        params = ('%' + q + '%',)
    return consultar(sql + 'ORDER BY b.fecha DESC, b.id_boletin DESC', params)
