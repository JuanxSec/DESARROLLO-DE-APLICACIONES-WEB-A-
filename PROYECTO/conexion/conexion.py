"""Conexión con la base de datos: MySQL, PostgreSQL (Render) o SQLite.

El motor se elige con DB_ENGINE. Las clases de abajo adaptan PostgreSQL y
SQLite para que el resto del código los use igual que mysql-connector.
"""

import os
import sqlite3
from datetime import date, datetime
from decimal import Decimal

from flask import current_app


def motor():
    """Devuelve el motor activo: 'mysql', 'postgres' o 'sqlite'."""
    return (current_app.config.get('DB_ENGINE') or 'mysql').lower()


# PostgreSQL

class _CursorPostgres:
    """Da al cursor de psycopg la misma interfaz que el de mysql-connector."""

    def __init__(self, conn, dictionary=False):
        from psycopg.rows import dict_row
        self._conn = conn
        self._cursor = conn.cursor(row_factory=dict_row) if dictionary else conn.cursor()

    def execute(self, sql, params=()):
        # Sin parámetros se envía tal cual para que psycopg no interprete los %.
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
        """psycopg no tiene lastrowid; se usa lastval() de la misma conexión."""
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


# SQLite
# Conversores para que SQLite devuelva fechas y booleanos de Python.
sqlite3.register_adapter(date, lambda valor: valor.isoformat())
sqlite3.register_adapter(datetime, lambda valor: valor.isoformat(' '))
# Los DecimalField de WTForms entregan Decimal, que sqlite3 no sabe guardar.
sqlite3.register_adapter(Decimal, float)
sqlite3.register_converter('DATE', lambda b: date.fromisoformat(b.decode()[:10]))
sqlite3.register_converter('TIMESTAMP', lambda b: datetime.fromisoformat(b.decode()))
sqlite3.register_converter('BOOLEAN', lambda b: b not in (b'0', b'', b'false'))


class _CursorSqlite:
    """Traduce el marcador %s al ? de sqlite3 y entrega filas como diccionarios."""

    def __init__(self, conn, dictionary=False):
        self._cursor = conn.cursor()
        self._dictionary = dictionary

    def execute(self, sql, params=()):
        return self._cursor.execute(sql.replace('%s', '?'), tuple(params or ()))

    def _fila(self, fila):
        if fila is None or not self._dictionary:
            return fila
        columnas = [c[0] for c in self._cursor.description]
        return dict(zip(columnas, fila))

    def fetchone(self):
        return self._fila(self._cursor.fetchone())

    def fetchall(self):
        return [self._fila(fila) for fila in self._cursor.fetchall()]

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def close(self):
        self._cursor.close()


class _ConexionSqlite:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=False):
        return _CursorSqlite(self._conn, dictionary)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def ruta_sqlite():
    """Ruta del archivo SQLite: data/juanseccti.db junto a la aplicación."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.environ.get('SQLITE_PATH', os.path.join(base, 'data', 'juanseccti.db'))


def conectar_sqlite():
    conn = sqlite3.connect(ruta_sqlite(), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def get_db_connection():
    """Crea y retorna una conexión al motor configurado."""
    if motor() == 'postgres':
        import psycopg
        return _ConexionPostgres(psycopg.connect(current_app.config['DATABASE_URL']))

    if motor() == 'sqlite':
        return _ConexionSqlite(conectar_sqlite())

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
