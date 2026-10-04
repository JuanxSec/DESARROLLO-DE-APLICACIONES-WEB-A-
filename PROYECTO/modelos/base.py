"""Acceso a la base de datos: SELECT, INSERT, UPDATE y DELETE parametrizados y utilidades comunes."""

from conexion.conexion import get_db_connection, motor


def consultar(sql, params=(), uno=False):
    """Ejecuta un SELECT y cierra siempre el cursor y la conexión."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    if uno:
        resultado = cursor.fetchone()
        # MySQL no permite cerrar un cursor con filas pendientes de leer.
        cursor.fetchall()
    else:
        resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


def ejecutar(sql, params=()):
    """Ejecuta INSERT / UPDATE / DELETE, hace commit y retorna las filas afectadas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas


def insertar(sql, params=()):
    """Igual que ejecutar() pero devuelve el id autogenerado del nuevo registro."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return nuevo_id


def contar(sql, params=()):
    return consultar(sql, params, uno=True)['t']


def expr_mes(columna):
    """Expresión SQL que convierte una fecha en el texto AAAA-MM según el motor."""
    if motor() == 'postgres':
        return "to_char(" + columna + ", 'YYYY-MM')"
    if motor() == 'sqlite':
        return "strftime('%Y-%m', " + columna + ")"
    return "CONCAT(YEAR(" + columna + "), '-', LPAD(MONTH(" + columna + "), 2, '0'))"


# Dar de baja y reactivar cambian el campo activo; eliminar hace un DELETE.
VISTAS = {
    'activos': 'activo = TRUE',
    'baja': 'activo = FALSE',
    'todos': '1 = 1',
}


def filtro_vista(ver, alias=''):
    condicion = VISTAS[ver]
    return condicion if not alias else condicion.replace('activo', alias + '.activo')


def cambiar_activo(tabla, columna_id, id_registro, activo):
    """UPDATE que da de baja o reactiva un registro conservando el histórico."""
    return ejecutar(
        'UPDATE ' + tabla + ' SET activo = %s WHERE ' + columna_id + ' = %s',
        (activo, id_registro)
    )


def id_por_nombre(tabla, columna_id, nombre, extra=''):
    fila = consultar('SELECT ' + columna_id + ' AS id FROM ' + tabla +
                     ' WHERE nombre = %s' + extra, (nombre,), uno=True)
    return fila['id'] if fila else None
