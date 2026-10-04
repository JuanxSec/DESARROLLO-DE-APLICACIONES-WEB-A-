"""Aplicación Flask, configuración, CSRF y Flask-Login."""

import os

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

import init_db

# Variables del archivo .env (en Render se configuran en el panel).
init_db.cargar_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_segura_2026')
csrf = CSRFProtect(app)

# Motor de base de datos: mysql, postgres o sqlite.
app.config['DB_ENGINE'] = os.environ.get('DB_ENGINE', 'mysql').lower()
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')

# Configuración de MySQL (Semana 13), tomada de variables de entorno.
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', '3306'))
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DATABASE'] = os.environ.get('MYSQL_DATABASE', 'juanseccti')
app.config['MYSQL_SSL'] = os.environ.get('MYSQL_SSL', '0') == '1'
app.config['MYSQL_SSL_CA'] = os.environ.get('MYSQL_SSL_CA', '')

# En Render el esquema se carga en el primer arranque si no hay tablas.
if os.environ.get('AUTO_INIT_DB', '0') == '1':
    try:
        init_db.main()
    except Exception as error:  # noqa: BLE001
        app.logger.error('No se pudo preparar el esquema: %s', error)

# Gestión de sesiones de usuario (Semana 14).
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Debe iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'
