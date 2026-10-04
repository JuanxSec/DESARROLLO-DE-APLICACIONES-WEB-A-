"""Catálogos que alimentan los SelectField de los formularios (tablas padre)."""

from modelos.base import consultar


def opciones(sql, clave, etiqueta, params=()):
    return [(fila[clave], fila[etiqueta]) for fila in consultar(sql, params)]


def opciones_proveedores():
    return opciones('SELECT id_proveedor, nombre FROM proveedores WHERE activo = TRUE ORDER BY nombre',
                    'id_proveedor', 'nombre')


def opciones_clientes():
    return opciones('SELECT id_cliente, nombre FROM clientes WHERE activo = TRUE ORDER BY nombre',
                    'id_cliente', 'nombre')


def opciones_categorias():
    return opciones('SELECT id_categoria, nombre FROM categorias ORDER BY nombre',
                    'id_categoria', 'nombre')


def opciones_estados(ambito):
    return opciones('SELECT id_estado, nombre FROM estados WHERE ambito = %s ORDER BY id_estado',
                    'id_estado', 'nombre', (ambito,))


def opciones_sectores():
    return opciones('SELECT id_sector, nombre FROM sectores ORDER BY nombre', 'id_sector', 'nombre')


def opciones_tipos_proveedor():
    return opciones('SELECT id_tipo, nombre FROM tipos_proveedor ORDER BY nombre', 'id_tipo', 'nombre')


def opciones_roles():
    return opciones('SELECT id_rol, nombre FROM roles ORDER BY id_rol', 'id_rol', 'nombre')


def opciones_parroquias():
    """Ubicación completa uniendo las tres tablas geográficas."""
    filas = consultar(
        'SELECT pa.id_parroquia, '
        "       CONCAT(pr.nombre, ' / ', ca.nombre, ' / ', pa.nombre) AS ubicacion "
        'FROM parroquias pa '
        'INNER JOIN cantones ca ON ca.id_canton = pa.id_canton '
        'INNER JOIN provincias pr ON pr.id_provincia = ca.id_provincia '
        'ORDER BY pr.nombre, ca.nombre, pa.nombre'
    )
    return [(f['id_parroquia'], f['ubicacion']) for f in filas]


def opciones_productos(con_cupos=False):
    """Servicios activos; en el detalle se muestran también los cupos que quedan."""
    filas = consultar('SELECT id_producto, nombre, stock, precio FROM productos '
                      'WHERE activo = TRUE ORDER BY nombre')
    if con_cupos:
        return [(f['id_producto'], '%s (cupos: %s, USD %.2f)' % (f['nombre'], f['stock'], f['precio']))
                for f in filas]
    return [(f['id_producto'], f['nombre']) for f in filas]


def opciones_nombre_servicios():
    return [(f['nombre'], f['nombre']) for f in
            consultar('SELECT nombre FROM productos WHERE activo = TRUE ORDER BY nombre')]
