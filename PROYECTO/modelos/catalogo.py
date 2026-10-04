"""Tablas padre editables desde el panel: categorías, sectores y tipos de fuente."""

from flask import abort

from modelos.base import contar


# Catálogos con la misma estructura: tabla, clave primaria y tablas hijas.
CATALOGOS = {
    'categorias': {
        'tabla': 'categorias', 'id': 'id_categoria', 'titulo': 'Categorías de servicio',
        'singular': 'categoría', 'icono': 'bi-tags',
        'usos': [('productos', 'id_categoria'), ('boletines', 'id_categoria')],
    },
    'sectores': {
        'tabla': 'sectores', 'id': 'id_sector', 'titulo': 'Sectores de las organizaciones',
        'singular': 'sector', 'icono': 'bi-diagram-3',
        'usos': [('clientes', 'id_sector')],
    },
    'tipos-fuente': {
        'tabla': 'tipos_proveedor', 'id': 'id_tipo', 'titulo': 'Tipos de fuente',
        'singular': 'tipo de fuente', 'icono': 'bi-broadcast-pin',
        'usos': [('proveedores', 'id_tipo')],
    },
}


def catalogo_pedido(clave):
    if clave not in CATALOGOS:
        abort(404)
    return CATALOGOS[clave]


def usos_catalogo(cat, id_registro):
    """Cuántos registros de las tablas hijas usan este elemento del catálogo."""
    return sum(contar('SELECT COUNT(*) AS t FROM ' + hija + ' WHERE ' + columna + ' = %s', (id_registro,))
               for hija, columna in cat['usos'])


def nombre_repetido(cat, nombre, excluir=None):
    sql = 'SELECT COUNT(*) AS t FROM ' + cat['tabla'] + ' WHERE LOWER(nombre) = LOWER(%s)'
    params = (nombre,)
    if excluir:
        sql += ' AND ' + cat['id'] + ' <> %s'
        params = (nombre, excluir)
    return contar(sql, params)
