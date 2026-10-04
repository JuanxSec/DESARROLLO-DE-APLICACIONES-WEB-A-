"""Panel de control, prueba de conexión y páginas de error."""

from flask import render_template
from flask_login import login_required

from conexion.conexion import get_db_connection, motor
from extensiones import app
from modelos.base import consultar, contar, expr_mes
from modelos.boletin import boletines_publicos


@app.route('/dashboard')
@login_required
def dashboard():
    resumen = {
        'productos': contar('SELECT COUNT(*) AS t FROM productos WHERE activo = TRUE'),
        'clientes': contar('SELECT COUNT(*) AS t FROM clientes WHERE activo = TRUE'),
        'proveedores': contar('SELECT COUNT(*) AS t FROM proveedores WHERE activo = TRUE'),
        'facturas': contar('SELECT COUNT(*) AS t FROM facturas WHERE activo = TRUE'),
        'boletines': contar('SELECT COUNT(*) AS t FROM boletines WHERE activo = TRUE'),
        'solicitudes': contar('SELECT COUNT(*) AS t FROM solicitudes WHERE activo = TRUE'),
    }
    facturado = consultar(
        'SELECT COALESCE(SUM(f.total), 0) AS total FROM facturas f '
        'INNER JOIN estados e ON e.id_estado = f.id_estado '
        "WHERE f.activo = TRUE AND e.nombre <> 'Anulada'", uno=True)['total']
    # Consulta relacionada: servicios más contratados (facturas + detalle + productos).
    mas_contratados = consultar(
        'SELECT p.nombre, SUM(d.cantidad) AS unidades, SUM(d.cantidad * d.precio_unitario) AS ingresos '
        'FROM detalle_factura d '
        'INNER JOIN productos p ON p.id_producto = d.id_producto '
        'INNER JOIN facturas f ON f.id_factura = d.id_factura '
        'WHERE f.activo = TRUE '
        'GROUP BY p.id_producto, p.nombre '
        'ORDER BY unidades DESC LIMIT 5'
    )
    por_mes = consultar(
        'SELECT ' + expr_mes('f.fecha') + ' AS mes, SUM(f.total) AS total '
        'FROM facturas f WHERE f.activo = TRUE '
        'GROUP BY ' + expr_mes('f.fecha') + ' ORDER BY mes')
    sin_cupos = consultar('SELECT nombre FROM productos WHERE activo = TRUE AND stock = 0 ORDER BY nombre')
    recientes = consultar(
        'SELECT s.id_solicitud, s.nombre, s.organizacion, s.fecha, p.nombre AS servicio, e.nombre AS estado '
        'FROM solicitudes s '
        'INNER JOIN productos p ON p.id_producto = s.id_producto '
        'INNER JOIN estados e ON e.id_estado = s.id_estado '
        'WHERE s.activo = TRUE ORDER BY s.id_solicitud DESC LIMIT 5')
    return render_template('dashboard.html', titulo='Panel de control', resumen=resumen,
                           mas_contratados=mas_contratados, facturado=facturado,
                           grafico={'meses': [f['mes'] for f in por_mes],
                                    'totales': [float(f['total'] or 0) for f in por_mes]},
                           sin_cupos=sin_cupos, recientes=recientes,
                           boletines=boletines_publicos(limite=3))


@app.route('/test_db')
@login_required
def test_db():
    if motor() == 'postgres':
        sql = ("SELECT table_name FROM information_schema.tables "
               "WHERE table_schema = 'public' ORDER BY table_name")
        nombre_base = 'PostgreSQL (Render)'
    elif motor() == 'sqlite':
        sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        nombre_base = 'SQLite (data/juanseccti.db)'
    else:
        sql = 'SHOW TABLES'
        nombre_base = app.config['MYSQL_DATABASE']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    tablas = [t[0] for t in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {'motor': motor(), 'base_de_datos': nombre_base,
            'total_tablas': len(tablas), 'tablas': tablas}


@app.errorhandler(404)
def no_encontrado(error):
    return render_template('error.html', titulo='Página no encontrada', codigo=404,
                           mensaje='La página que busca no existe o fue movida.'), 404


@app.errorhandler(500)
def error_interno(error):
    return render_template('error.html', titulo='Error del servidor', codigo=500,
                           mensaje='Ocurrió un problema inesperado. Intente nuevamente en unos minutos.'), 500
