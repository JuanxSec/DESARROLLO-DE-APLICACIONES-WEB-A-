"""Solicitudes de información enviadas desde la página pública (tabla solicitudes)."""

from modelos.base import consultar, filtro_vista


def listar_solicitudes(ver='activos', q='', estado=None):
    sql = ('SELECT s.id_solicitud, s.nombre, s.organizacion, s.correo, s.telefono, s.mensaje, s.fecha, '
           '       s.activo, p.nombre AS servicio, e.nombre AS estado '
           'FROM solicitudes s '
           'INNER JOIN productos p ON p.id_producto = s.id_producto '
           'INNER JOIN estados e ON e.id_estado = s.id_estado '
           'WHERE ' + filtro_vista(ver, 's') + ' ')
    params = []
    if q:
        sql += 'AND (LOWER(s.organizacion) LIKE LOWER(%s) OR LOWER(s.nombre) LIKE LOWER(%s)) '
        params += ['%' + q + '%', '%' + q + '%']
    if estado:
        sql += 'AND s.id_estado = %s '
        params.append(estado)
    return consultar(sql + 'ORDER BY s.id_solicitud DESC', tuple(params))
