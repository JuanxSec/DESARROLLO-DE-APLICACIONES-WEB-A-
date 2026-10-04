"""Carga el esquema SQL en la base configurada.

Uso: python init_db.py [--reset]
"""

import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)


def cargar_dotenv():
    """Lee el archivo .env, si existe, sin depender de librerías externas."""
    ruta = os.path.join(BASE, '.env')
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding='utf-8') as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith('#') or '=' not in linea:
                continue
            clave, valor = linea.split('=', 1)
            # Las variables ya definidas en el entorno tienen prioridad.
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def motor():
    return os.environ.get('DB_ENGINE', 'mysql').lower()


def archivo_esquema():
    nombre = {'postgres': 'esquema_postgres.sql',
              'sqlite': 'esquema_sqlite.sql'}.get(motor(), 'esquema.sql')
    return os.path.join(BASE, 'sql', nombre)


def conectar():
    if motor() == 'sqlite':
        from conexion.conexion import conectar_sqlite, ruta_sqlite
        os.makedirs(os.path.dirname(ruta_sqlite()), exist_ok=True)
        return conectar_sqlite()

    if motor() == 'postgres':
        import psycopg
        url = os.environ.get('DATABASE_URL', '')
        if not url:
            raise SystemExit('Falta DATABASE_URL para conectarse a PostgreSQL.')
        return psycopg.connect(url)

    import mysql.connector
    parametros = {
        'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.environ.get('MYSQL_PORT', '3306')),
        'user': os.environ.get('MYSQL_USER', 'root'),
        'password': os.environ.get('MYSQL_PASSWORD', ''),
        'database': os.environ.get('MYSQL_DATABASE', 'juanseccti'),
    }
    if os.environ.get('MYSQL_SSL', '0') == '1':
        parametros['ssl_disabled'] = False
        ca = os.environ.get('MYSQL_SSL_CA', '')
        if ca:
            parametros['ssl_ca'] = ca
    return mysql.connector.connect(**parametros)


def sentencias_del_esquema():
    """Devuelve las sentencias del esquema listas para ejecutar."""
    with open(archivo_esquema(), encoding='utf-8') as archivo:
        contenido = archivo.read()

    # Fuera los comentarios de línea, que pueden contener punto y coma.
    contenido = re.sub(r'--[^\n]*', '', contenido)

    sentencias = []
    for sentencia in contenido.split(';'):
        sentencia = sentencia.strip()
        if not sentencia:
            continue
        # Las sentencias de nivel de base de datos no aplican en un servidor
        # gestionado: la base ya existe y es la que indica la configuración.
        if re.match(r'^(DROP\s+DATABASE|CREATE\s+DATABASE|USE)\b', sentencia, re.IGNORECASE):
            continue
        sentencias.append(sentencia)
    return sentencias


def tablas_existentes(cursor):
    if motor() == 'sqlite':
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                       "AND name NOT LIKE 'sqlite_%' ORDER BY name")
    elif motor() == 'postgres':
        cursor.execute("SELECT table_name FROM information_schema.tables "
                       "WHERE table_schema = 'public' ORDER BY table_name")
    else:
        cursor.execute('SHOW TABLES')
    return [fila[0] for fila in cursor.fetchall()]


def vaciar(cursor, tablas):
    """Borra las tablas ignorando el orden de las claves foráneas."""
    if motor() == 'postgres':
        for tabla in tablas:
            cursor.execute('DROP TABLE IF EXISTS "' + tabla + '" CASCADE')
        return

    if motor() == 'sqlite':
        cursor.execute('PRAGMA foreign_keys = OFF')
        for tabla in tablas:
            cursor.execute('DROP TABLE IF EXISTS "' + tabla + '"')
        cursor.execute('PRAGMA foreign_keys = ON')
        return

    cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
    for tabla in tablas:
        cursor.execute('DROP TABLE IF EXISTS `' + tabla + '`')
    cursor.execute('SET FOREIGN_KEY_CHECKS = 1')


def main():
    cargar_dotenv()
    reiniciar = '--reset' in sys.argv

    conn = conectar()
    cursor = conn.cursor()
    print('Motor: ' + motor())
    print('Esquema: ' + os.path.basename(archivo_esquema()))

    existentes = tablas_existentes(cursor)
    if existentes and not reiniciar:
        # No es un error: el esquema ya está puesto y no hay nada que hacer.
        # Devolver 0 permite llamar al script en cada arranque sin romper nada.
        print('La base ya tiene ' + str(len(existentes)) + ' tablas, no hay nada que cargar.')
        print('Use --reset si desea borrarlas y volver a cargar el esquema.')
        cursor.close()
        conn.close()
        return 0

    if existentes:
        print('Borrando ' + str(len(existentes)) + ' tablas existentes...')
        vaciar(cursor, existentes)
        conn.commit()

    sentencias = sentencias_del_esquema()
    print('Ejecutando ' + str(len(sentencias)) + ' sentencias...')
    for sentencia in sentencias:
        cursor.execute(sentencia)
    conn.commit()

    creadas = tablas_existentes(cursor)
    print('Listo. La base quedó con ' + str(len(creadas)) + ' tablas:')
    for tabla in creadas:
        cursor.execute('SELECT COUNT(*) FROM ' + tabla)
        print('  - ' + tabla + ': ' + str(cursor.fetchone()[0]) + ' registros')

    cursor.close()
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
