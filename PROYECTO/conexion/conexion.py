"""Conexión centralizada con la base de datos.

El proyecto trabaja con dos motores y la variable de entorno DB_ENGINE decide
cuál se usa:

  * ``mysql``    (valor por defecto) es el motor de la asignatura, el que
    documenta sql/esquema.sql y el que se usa al desarrollar en local.
  * ``postgres`` es el motor del despliegue en Render, que ofrece PostgreSQL
    gestionado y entrega la cadena de conexión en DATABASE_URL.

El resto de la aplicación no se entera de la diferencia: las funciones
consultar(), ejecutar() e insertar() de app.py siguen pidiendo un cursor con
``cursor(dictionary=True)`` y leyendo ``rowcount`` y ``lastrowid``. Cuando el
motor es PostgreSQL, las clases de más abajo traducen esa interfaz.
"""

from flask import current_app


def motor():
    """Devuelve el motor activo: 'mysql' o 'postgres'."""
    return (current_app.config.get('DB_ENGINE') or 'mysql').lower()


class _CursorPostgres:
    """Da al cursor de psycopg la misma interfaz que el de mysql-connector."""

    def __init__(self, conn, dictionary=False):
        from psycopg.rows import dict_row
        self._conn = conn
        self._cursor = conn.cursor(row_factory=dict_row) if dictionary else conn.cursor()

    def execute(self, sql, params=()):
        # psycopg intenta interpolar aunque la secuencia venga vacía, así que
        # las consultas sin parámetros se envían tal cual.
        if params:
            return self._cursor.execute(sql, params)
        return self._cursor.execute(sql)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        """Equivalente de lastrowid en PostgreSQL.

        psycopg no expone ese atributo. En PostgreSQL el identificador recién
        generado se obtiene con lastval(), que devuelve el último valor que
        produjo una secuencia en esta misma conexión. Sigue siendo válido
        después del commit, porque lastval() es de ámbito de sesión y no de
        transacción.
        """
        with self._conn.cursor() as aux:
            aux.execute('SELECT lastval()')
            return aux.fetchone()[0]

    def close(self):
        self._cursor.close()


class _ConexionPostgres:
    """Envuelve la conexión de psycopg para aceptar cursor(dictionary=...)."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=False):
        return _CursorPostgres(self._conn, dictionary)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_db_connection():
    """Crea y retorna una conexión al motor configurado."""
    if motor() == 'postgres':
        import psycopg
        return _ConexionPostgres(psycopg.connect(current_app.config['DATABASE_URL']))

    import mysql.connector
    parametros = {
        'host': current_app.config['MYSQL_HOST'],
        'port': current_app.config['MYSQL_PORT'],
        'user': current_app.config['MYSQL_USER'],
        'password': current_app.config['MYSQL_PASSWORD'],
        'database': current_app.config['MYSQL_DATABASE'],
    }

    if current_app.config.get('MYSQL_SSL'):
        # Un servidor MySQL gestionado obliga a cifrar el tráfico. Si además se
        # entrega el certificado de la autoridad, se valida contra él.
        parametros['ssl_disabled'] = False
        ca = current_app.config.get('MYSQL_SSL_CA')
        if ca:
            parametros['ssl_ca'] = ca

    return mysql.connector.connect(**parametros)
