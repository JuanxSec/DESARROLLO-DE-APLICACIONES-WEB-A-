"""Organizaciones suscritas (tabla clientes)."""

from modelos.base import consultar, filtro_vista


def listar_clientes(ver='activos', q=''):
    """SELECT con JOIN a sectores y a las tres tablas de ubicación geográfica."""
    sql = ('SELECT c.id_cliente, c.nombre, c.ruc, c.servicio, c.correo, c.telefono, c.activo, '
           '       s.nombre AS sector, pa.nombre AS parroquia, ca.nombre AS canton, '
           '       pr.nombre AS provincia '
           'FROM clientes c '
           'INNER JOIN sectores s ON s.id_sector = c.id_sector '
           'INNER JOIN parroquias pa ON pa.id_parroquia = c.id_parroquia '
           'INNER JOIN cantones ca ON ca.id_canton = pa.id_canton '
           'INNER JOIN provincias pr ON pr.id_provincia = ca.id_provincia '
           'WHERE ' + filtro_vista(ver, 'c') + ' ')
    params = ()
    if q:
        sql += 'AND (LOWER(c.nombre) LIKE LOWER(%s) OR c.ruc LIKE %s) '
        params = ('%' + q + '%', '%' + q + '%')
    return consultar(sql + 'ORDER BY c.id_cliente', params)


def ruc_repetido(ruc, id_cliente=None):
    if not ruc:
        return False
    fila = consultar('SELECT id_cliente FROM clientes WHERE ruc = %s', (ruc,), uno=True)
    return fila is not None and fila['id_cliente'] != id_cliente
