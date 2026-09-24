import mysql.connector
from flask import current_app


def get_db_connection():
    """Crea y retorna una conexión a la base de datos MySQL.

    Los parámetros salen de la configuración de la aplicación, que a su vez
    los toma de variables de entorno. En local apunta al MySQL instalado en
    el equipo y en producción al servidor MySQL del proveedor externo, que
    exige conexión cifrada con TLS.
    """
    parametros = {
        'host': current_app.config['MYSQL_HOST'],
        'port': current_app.config['MYSQL_PORT'],
        'user': current_app.config['MYSQL_USER'],
        'password': current_app.config['MYSQL_PASSWORD'],
        'database': current_app.config['MYSQL_DATABASE'],
    }

    if current_app.config.get('MYSQL_SSL'):
        # El servidor gestionado obliga a cifrar el tráfico. Si además se
        # entrega el certificado de la autoridad, se valida contra él.
        parametros['ssl_disabled'] = False
        ca = current_app.config.get('MYSQL_SSL_CA')
        if ca:
            parametros['ssl_ca'] = ca

    return mysql.connector.connect(**parametros)
