"""Proyecto Integrador JuansecCTI - Desarrollo de Aplicaciones Web.

JuansecCTI es una empresa (ficticia, con fines académicos) que presta servicios
de ciberinteligencia de amenazas (Cyber Threat Intelligence): boletines,
alertas de vulnerabilidades, monitoreo de la dark web, protección de marca,
búsqueda proactiva de amenazas y apoyo en incidentes.

La aplicación Flask integra los avances de las semanas 9 a 16:
  * Semana 9  : proyecto Flask, carpetas templates/static y rutas por módulo.
  * Semana 10 : contenido dinámico con Jinja2 (variables, for, if, filtros,
                herencia de base.html y componentes reutilizables).
  * Semana 11 : formularios con Flask-WTF / WTForms, validaciones y CSRF.
  * Semana 12 : persistencia local con SQLite (DB_ENGINE=sqlite).
  * Semana 13 : base de datos relacional MySQL con SELECT, INSERT, UPDATE y
                DELETE parametrizados.
  * Semana 14 : login funcional con Flask-Login y Werkzeug.
  * Semana 15 : CRUD completo sobre PostgreSQL desplegado en Render, consultas
                JOIN, baja lógica y reportes exportables.
  * Semana 16 : pruebas del sistema (pruebas/prueba_sistema.py).
"""

import csv
import io
import json
import math
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import (Flask, render_template, redirect, url_for, flash, abort,
                   request, Response)
from flask_wtf.csrf import CSRFProtect
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash

import init_db
from conexion.conexion import get_db_connection, motor
from models import Usuario

# Variables locales del archivo .env (no se sube al repositorio). En Render se
# definen en el panel del servicio y tienen prioridad.
init_db.cargar_dotenv()
from forms.producto_form import ProductoForm
from forms.cliente_form import ClienteForm
from forms.proveedor_form import ProveedorForm
from forms.facturacion_form import FacturacionForm
from forms.detalle_form import DetalleFacturaForm
from forms.login_form import LoginForm
from forms.usuario_form import UsuarioForm
from forms.boletin_form import BoletinForm, NIVELES
from forms.solicitud_form import SolicitudForm
from forms.catalogo_form import CatalogoForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_segura_2026')
csrf = CSRFProtect(app)

# Motor de base de datos: 'mysql' (el de la asignatura, en local), 'postgres'
# (el despliegue en Render, que entrega la cadena en DATABASE_URL) o 'sqlite'
# (la persistencia local de la Semana 12, archivo data/juanseccti.db).
app.config['DB_ENGINE'] = os.environ.get('DB_ENGINE', 'mysql').lower()
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')

# Configuración de MySQL (Semana 13). Las credenciales reales se toman de
# variables de entorno para no subirlas al repositorio.
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', '3306'))
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DATABASE'] = os.environ.get('MYSQL_DATABASE', 'juanseccti')
app.config['MYSQL_SSL'] = os.environ.get('MYSQL_SSL', '0') == '1'
app.config['MYSQL_SSL_CA'] = os.environ.get('MYSQL_SSL_CA', '')

# En el despliegue la base nace vacía y el plan gratuito no da consola donde
# ejecutar init_db.py, así que el esquema se carga en el primer arranque. El
# script solo actúa si todavía no hay tablas.
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

titulo_sitio = 'JuansecCTI'
POR_PAGINA = 8

# Datos de la página pública que no cambian con la base de datos. Se envían a
# la plantilla como lista de diccionarios y se recorren con un for de Jinja2.
PILARES = [
    {'icono': 'bi-binoculars', 'titulo': 'Recolección',
     'texto': 'Fuentes abiertas, comunidades de investigación, avisos de fabricantes y plataformas de amenazas.'},
    {'icono': 'bi-diagram-3', 'titulo': 'Análisis',
     'texto': 'Correlación de indicadores y técnicas de ataque con la realidad de cada organización.'},
    {'icono': 'bi-megaphone', 'titulo': 'Difusión',
     'texto': 'Boletines y alertas en lenguaje claro, con recomendaciones que se pueden aplicar el mismo día.'},
    {'icono': 'bi-arrow-repeat', 'titulo': 'Retroalimentación',
     'texto': 'Cada incidente atendido mejora las reglas de detección y las fuentes que se vigilan.'},
]

IMAGENES_SERVICIO = [
    ('servicio-boletin.jpg', 'Boletín'),
    ('servicio-alerta.jpg', 'Alerta'),
    ('servicio-noticias.jpg', 'Noticias'),
    ('servicio-informe.jpg', 'Informe'),
    ('servicio-capacitacion.jpg', 'Capacitación'),
    ('servicio-darkweb.jpg', 'Dark web'),
    ('servicio-marca.jpg', 'Protección de marca'),
    ('servicio-infraestructura.jpg', 'Superficie de ataque'),
    ('servicio-threat-hunting.jpg', 'Threat hunting'),
    ('servicio-incidentes.jpg', 'Respuesta a incidentes'),
]

NIVEL_ETIQUETA = dict(NIVELES)
NIVEL_COLOR = {'Critico': 'danger', 'Alto': 'warning', 'Medio': 'info', 'Bajo': 'secondary'}


# ---------------- Acceso a datos: consultas parametrizadas ----------------

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


def recalcular_total(id_factura):
    """Actualiza el total de la factura a partir de su detalle (relación N:N)."""
    fila = consultar(
        'SELECT COALESCE(SUM(cantidad * precio_unitario), 0) AS total '
        'FROM detalle_factura WHERE id_factura = %s',
        (id_factura,), uno=True
    )
    ejecutar('UPDATE facturas SET total = %s WHERE id_factura = %s',
             (fila['total'], id_factura))


def registrar(accion, modulo, detalle):
    """Pista de auditoría: guarda quién hizo qué y cuándo en la tabla bitacora."""
    try:
        if current_user.is_authenticated:
            id_usuario, nombre = current_user.id, current_user.usuario
        else:
            id_usuario, nombre = None, 'visitante'
        ejecutar('INSERT INTO bitacora (id_usuario, usuario, accion, modulo, detalle) '
                 'VALUES (%s, %s, %s, %s, %s)',
                 (id_usuario, nombre, accion, modulo, detalle[:255]))
    except Exception as error:  # noqa: BLE001
        # La auditoría nunca debe impedir la operación principal.
        app.logger.warning('No se pudo registrar en la bitácora: %s', error)


def paginar(registros, pagina):
    """Divide una lista en páginas de POR_PAGINA elementos."""
    total = len(registros)
    paginas = max(1, math.ceil(total / POR_PAGINA))
    pagina = min(max(1, pagina), paginas)
    inicio = (pagina - 1) * POR_PAGINA
    return registros[inicio:inicio + POR_PAGINA], {'pagina': pagina, 'paginas': paginas, 'total': total}


def pagina_pedida():
    try:
        return int(request.args.get('pagina', 1))
    except ValueError:
        return 1


# ---------------- Baja lógica: el borrado por cambio de estado ----------------
#
# Las guías piden la operación DELETE, pero en la Clase Encuentro de la Semana 15
# el docente indicó que el botón de eliminar no debe borrar físicamente el
# registro, sino ejecutar un UPDATE que cambie su estado para conservar el
# histórico. El sistema implementa las dos operaciones:
#
#   Dar de baja   -> UPDATE ... SET activo = FALSE WHERE ...   (se conserva)
#   Reactivar     -> UPDATE ... SET activo = TRUE  WHERE ...
#   Eliminar      -> DELETE FROM ... WHERE ...                 (definitivo)

VISTAS = {
    'activos': 'activo = TRUE',
    'baja': 'activo = FALSE',
    'todos': '1 = 1',
}


def vista_pedida():
    """Lee el filtro ?ver= de la URL y lo valida contra la lista de vistas."""
    ver = request.args.get('ver', 'activos')
    return ver if ver in VISTAS else 'activos'


def filtro_vista(ver, alias=''):
    condicion = VISTAS[ver]
    return condicion if not alias else condicion.replace('activo', alias + '.activo')


def texto_buscado():
    return (request.args.get('q') or '').strip()[:60]


def cambiar_activo(tabla, columna_id, id_registro, activo):
    """UPDATE que da de baja o reactiva un registro conservando el histórico."""
    return ejecutar(
        'UPDATE ' + tabla + ' SET activo = %s WHERE ' + columna_id + ' = %s',
        (activo, id_registro)
    )


# ---------------- Migración automática de bases anteriores ----------------
#
# El despliegue de Render tiene una base creada con versiones anteriores del
# esquema. Al arrancar se agregan las columnas y tablas nuevas y se completan
# los catálogos, sin tocar los datos existentes. Todo es idempotente: si ya
# está hecho, no cambia nada.

COLUMNAS_NUEVAS = [
    ('productos', 'activo', 'BOOLEAN NOT NULL DEFAULT TRUE'),
    ('clientes', 'activo', 'BOOLEAN NOT NULL DEFAULT TRUE'),
    ('proveedores', 'activo', 'BOOLEAN NOT NULL DEFAULT TRUE'),
    ('facturas', 'activo', 'BOOLEAN NOT NULL DEFAULT TRUE'),
    ('productos', 'imagen', 'VARCHAR(120) NULL'),
    ('clientes', 'ruc', 'VARCHAR(13) NULL'),
    ('productos', 'creado_en', 'TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP'),
    ('clientes', 'creado_en', 'TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP'),
    ('proveedores', 'creado_en', 'TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP'),
    ('facturas', 'creado_en', 'TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP'),
]

# Textos de los datos iniciales antiguos (sin tildes) y su versión actual.
RENOMBRAR = [
    ('categorias', 'nombre', 'Boletin', 'Boletín'),
    ('categorias', 'nombre', 'Capacitacion', 'Capacitación'),
    ('sectores', 'nombre', 'Educacion', 'Educación'),
    ('sectores', 'nombre', 'Tecnologia', 'Tecnología'),
    ('sectores', 'nombre', 'Publico', 'Público'),
    ('tipos_proveedor', 'nombre', 'Informacion publica', 'Información pública'),
    ('tipos_proveedor', 'nombre', 'Investigacion', 'Investigación'),
    ('tipos_proveedor', 'nombre', 'Documentacion', 'Documentación'),
    ('parroquias', 'nombre', 'Inaquito', 'Iñaquito'),
    ('productos', 'nombre', 'Boletin CTI semanal', 'Boletín CTI semanal'),
    ('productos', 'nombre', 'Alerta de vulnerabilidad', 'Alertas de vulnerabilidades críticas'),
    ('productos', 'nombre', 'Taller de concienciacion', 'Taller de concienciación'),
]

# Organizaciones de ejemplo de la primera versión: se reemplazan por los datos
# actuales (nombre, RUC, servicio y correo), conservando su id y sus facturas.
ORGANIZACIONES_EJEMPLO = [
    ('Empresa demostrativa A', 'Cooperativa Amazonía Segura', '1690012345001',
     'Boletín CTI semanal', 'sistemas@coopamazonia.example'),
    ('Entidad demostrativa B', 'Instituto Tecnológico del Puyo', '1690023456001',
     'Reporte de noticias de seguridad', 'ti@itpuyo.example'),
    ('Organizacion demostrativa C', 'Software Andino', '1790034567001',
     'Alertas de vulnerabilidades críticas', 'seguridad@andino.example'),
    ('Cooperativa demostrativa D', 'Clínica Shell Salud', '1690045678001',
     'Informe mensual de amenazas', 'soporte@clinicashell.example'),
]

# Conceptos antiguos de las facturas de ejemplo y su nombre actual.
CONCEPTOS_FACTURA = [
    ('Boletin CTI semanal', 'Boletín CTI semanal'),
    ('Noticias de seguridad', 'Reporte de noticias de seguridad'),
    ('Alerta de vulnerabilidad', 'Alertas de vulnerabilidades críticas'),
    ('Informe mensual', 'Informe mensual de amenazas'),
]

SERVICIOS_BASE = [
    # nombre, categoría, precio, cupos, descripción, imagen
    ('Boletín CTI semanal', 'Boletín', 45, 15, 'Resumen semanal de amenazas, vulnerabilidades y recomendaciones accionables para el equipo de TI.', 'servicio-boletin.jpg'),
    ('Alertas de vulnerabilidades críticas', 'Alerta', 30, 8, 'Aviso temprano cuando un fallo crítico afecta a la tecnología que usa la organización, con pasos de mitigación.', 'servicio-alerta.jpg'),
    ('Reporte de noticias de seguridad', 'Noticias', 20, 0, 'Noticias relevantes de ciberseguridad explicadas en lenguaje sencillo para la gerencia.', 'servicio-noticias.jpg'),
    ('Informe mensual de amenazas', 'Informe', 90, 5, 'Análisis mensual de campañas, actores y técnicas observadas en Ecuador y la región.', 'servicio-informe.jpg'),
    ('Taller de concienciación', 'Capacitación', 120, 3, 'Sesión práctica para que el personal reconozca el phishing y la ingeniería social.', 'servicio-capacitacion.jpg'),
    ('Monitoreo de la dark web', 'Monitoreo', 150, 6, 'Vigilancia de foros, mercados y filtraciones donde aparezcan credenciales o datos de la organización.', 'servicio-darkweb.jpg'),
    ('Protección de marca y dominios', 'Monitoreo', 110, 4, 'Detección de dominios parecidos, perfiles falsos y sitios de phishing que suplantan a la marca.', 'servicio-marca.jpg'),
    ('Superficie de ataque externa', 'Monitoreo', 130, 5, 'Inventario de activos expuestos en internet y priorización de los que presentan riesgo.', 'servicio-infraestructura.jpg'),
    ('Búsqueda proactiva de amenazas', 'Respuesta', 200, 2, 'Threat hunting guiado por indicadores de compromiso para encontrar intrusiones que pasan desapercibidas.', 'servicio-threat-hunting.jpg'),
    ('Apoyo en respuesta a incidentes', 'Respuesta', 250, 2, 'Acompañamiento técnico para contener, analizar y documentar un incidente de seguridad.', 'servicio-incidentes.jpg'),
]


def _existe_columna(tabla, columna):
    esquema = 'current_schema()' if motor() == 'postgres' else 'DATABASE()'
    return contar('SELECT COUNT(*) AS t FROM information_schema.columns '
                  'WHERE table_schema = ' + esquema + ' AND table_name = %s AND column_name = %s',
                  (tabla, columna))


def _existe_tabla(tabla):
    esquema = 'current_schema()' if motor() == 'postgres' else 'DATABASE()'
    return contar('SELECT COUNT(*) AS t FROM information_schema.tables '
                  'WHERE table_schema = ' + esquema + ' AND table_name = %s', (tabla,))


def _ddl_desde_esquema(tabla):
    """Toma el CREATE TABLE de la tabla desde el archivo de esquema del motor."""
    archivo = 'esquema_postgres.sql' if motor() == 'postgres' else 'esquema.sql'
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sql', archivo)
    with open(ruta, encoding='utf-8') as fuente:
        contenido = fuente.read()
    inicio = contenido.index('CREATE TABLE ' + tabla + ' (')
    fin = contenido.index(');', inicio) + 1
    return contenido[inicio:fin]


def _id_por_nombre(tabla, columna_id, nombre, extra=''):
    fila = consultar('SELECT ' + columna_id + ' AS id FROM ' + tabla +
                     ' WHERE nombre = %s' + extra, (nombre,), uno=True)
    return fila['id'] if fila else None


def migrar_base():
    if motor() == 'sqlite':
        return  # el archivo SQLite se genera completo con init_db.py

    if not _existe_tabla('productos'):
        return  # base vacía: init_db.py cargará el esquema completo

    for tabla, columna, tipo in COLUMNAS_NUEVAS:
        if not _existe_columna(tabla, columna):
            ejecutar('ALTER TABLE ' + tabla + ' ADD COLUMN ' + columna + ' ' + tipo)
            print('[migracion] ' + tabla + '.' + columna + ' agregada')

    # El catálogo de estados ahora también sirve al módulo de solicitudes.
    if motor() == 'postgres':
        ejecutar('ALTER TABLE estados DROP CONSTRAINT IF EXISTS ck_estados_ambito')
        ejecutar("ALTER TABLE estados ADD CONSTRAINT ck_estados_ambito "
                 "CHECK (ambito IN ('producto', 'factura', 'solicitud'))")
    else:
        ejecutar('ALTER TABLE estados MODIFY ambito VARCHAR(20) NOT NULL')

    for tabla, columna, viejo, nuevo in RENOMBRAR:
        if not contar('SELECT COUNT(*) AS t FROM ' + tabla + ' WHERE ' + columna + ' = %s', (nuevo,)):
            ejecutar('UPDATE ' + tabla + ' SET ' + columna + ' = %s WHERE ' + columna + ' = %s',
                     (nuevo, viejo))

    for viejo, nombre, ruc, servicio, correo in ORGANIZACIONES_EJEMPLO:
        if not contar('SELECT COUNT(*) AS t FROM clientes WHERE nombre = %s OR ruc = %s', (nombre, ruc)):
            ejecutar('UPDATE clientes SET nombre = %s, ruc = %s, servicio = %s, correo = %s WHERE nombre = %s',
                     (nombre, ruc, servicio, correo, viejo))

    for viejo, nuevo in CONCEPTOS_FACTURA:
        ejecutar('UPDATE facturas SET servicio = %s WHERE servicio = %s', (nuevo, viejo))

    for nombre, ambito in (('Nueva', 'solicitud'), ('En gestión', 'solicitud'), ('Atendida', 'solicitud')):
        if not contar('SELECT COUNT(*) AS t FROM estados WHERE nombre = %s AND ambito = %s', (nombre, ambito)):
            ejecutar('INSERT INTO estados (nombre, ambito) VALUES (%s, %s)', (nombre, ambito))

    for nombre, descripcion in (
            ('Monitoreo', 'Vigilancia continua de la dark web, la marca y la superficie expuesta.'),
            ('Respuesta', 'Búsqueda proactiva de amenazas y apoyo ante incidentes.')):
        if not _id_por_nombre('categorias', 'id_categoria', nombre):
            ejecutar('INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)', (nombre, descripcion))

    id_disponible = _id_por_nombre('estados', 'id_estado', 'Disponible', " AND ambito = 'producto'")
    id_fuente = consultar('SELECT MIN(id_proveedor) AS id FROM proveedores', uno=True)['id']
    for nombre, categoria, precio, cupos, descripcion, imagen in SERVICIOS_BASE:
        fila = consultar('SELECT id_producto, imagen FROM productos WHERE nombre = %s', (nombre,), uno=True)
        if fila is None:
            id_categoria = _id_por_nombre('categorias', 'id_categoria', categoria)
            ejecutar('INSERT INTO productos (nombre, id_categoria, id_estado, precio, stock, '
                     'descripcion, id_proveedor, imagen) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                     (nombre, id_categoria, id_disponible, precio, cupos, descripcion, id_fuente, imagen))
        elif not fila['imagen']:
            ejecutar('UPDATE productos SET imagen = %s, descripcion = %s WHERE id_producto = %s',
                     (imagen, descripcion, fila['id_producto']))
    ejecutar("UPDATE productos SET imagen = 'servicio-boletin.jpg' WHERE imagen IS NULL")

    for tabla in ('boletines', 'solicitudes', 'bitacora'):
        if not _existe_tabla(tabla):
            ejecutar(_ddl_desde_esquema(tabla))
            print('[migracion] tabla ' + tabla + ' creada')

    if not contar('SELECT COUNT(*) AS t FROM boletines'):
        sembrar_boletines()


def sembrar_boletines():
    datos = [
        ('Phishing que suplanta a entidades financieras del país',
         'Se observan correos y mensajes SMS que imitan a cooperativas y bancos para robar credenciales de banca en línea. Recomendación: activar doble factor, revisar el dominio del remitente y reportar los enlaces sospechosos.',
         'Alto', 'Campaña observada en Ecuador', date(2026, 9, 28), 'Boletín'),
        ('Vulnerabilidad crítica en VPN SSL de uso empresarial',
         'Los fabricantes de soluciones VPN publicaron parches para fallos que permiten ejecutar código sin autenticación. Se recomienda actualizar de inmediato y revisar los registros de acceso remoto.',
         'Critico', 'Avisos de seguridad de fabricantes', date(2026, 9, 24), 'Alerta'),
        ('Credenciales corporativas a la venta en foros clandestinos',
         'Los ladrones de información (infostealers) siguen alimentando mercados de la dark web con accesos a correo y VPN. Se aconseja forzar el cambio de contraseñas expuestas y monitorear inicios de sesión inusuales.',
         'Alto', 'Monitoreo de la dark web', date(2026, 9, 19), 'Monitoreo'),
        ('Ransomware dirigido a instituciones educativas',
         'Grupos de ransomware aprovechan cuentas sin doble factor y servidores expuestos durante los periodos de matrícula. Mantener copias de seguridad fuera de línea y segmentar la red administrativa.',
         'Medio', 'Informe mensual de amenazas', date(2026, 9, 12), 'Informe'),
        ('Buenas prácticas de contraseñas para el personal',
         'Recordatorio para la concienciación interna: frases de paso largas, gestor de contraseñas y doble factor en todas las cuentas críticas.',
         'Bajo', 'Material de capacitación', date(2026, 9, 5), 'Capacitación'),
    ]
    id_fuente = consultar('SELECT MIN(id_proveedor) AS id FROM proveedores', uno=True)['id']
    for titulo, resumen, nivel, referencia, fecha, categoria in datos:
        id_categoria = _id_por_nombre('categorias', 'id_categoria', categoria) or 1
        ejecutar('INSERT INTO boletines (titulo, resumen, nivel, referencia, fecha, id_categoria, id_proveedor) '
                 'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                 (titulo, resumen, nivel, referencia, fecha, id_categoria, id_fuente))


with app.app_context():
    # La migración nunca impide que la aplicación arranque: si la base todavía
    # no responde, las rutas que la necesiten ya avisarán.
    try:
        migrar_base()
    except Exception as error:  # noqa: BLE001
        print('[migracion] no se pudo completar: ' + str(error))


# ---------------- Catálogos: alimentan los SelectField de los formularios ----------------

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


# ---------------- Utilidades para las plantillas ----------------

def es_admin():
    return current_user.is_authenticated and current_user.rol == 'Administrador'


def solo_admin(vista):
    """Restringe una ruta al rol Administrador (gestión de usuarios y bitácora)."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not es_admin():
            flash('Esta opción está reservada al rol Administrador.', 'warning')
            return redirect(url_for('dashboard'))
        return vista(*args, **kwargs)
    return envoltura


@app.context_processor
def datos_globales():
    """Variables disponibles en todas las plantillas."""
    pendientes = 0
    if current_user.is_authenticated:
        try:
            pendientes = contar(
                'SELECT COUNT(*) AS t FROM solicitudes s '
                'INNER JOIN estados e ON e.id_estado = s.id_estado '
                "WHERE s.activo = TRUE AND e.nombre = 'Nueva'")
        except Exception:  # noqa: BLE001
            pendientes = 0
    return {
        'titulo_sitio': titulo_sitio,
        'anio_actual': date.today().year,
        'nivel_etiqueta': NIVEL_ETIQUETA,
        'nivel_color': NIVEL_COLOR,
        'es_admin': es_admin(),
        'solicitudes_nuevas': pendientes,
    }


@app.template_filter('dinero')
def filtro_dinero(valor):
    return '{:,.2f}'.format(float(valor or 0))


@app.template_filter('fecha')
def filtro_fecha(valor):
    if not valor:
        return ''
    if isinstance(valor, str):
        return valor[:10]
    return valor.strftime('%d/%m/%Y')


# ---------------- PÁGINAS PÚBLICAS ----------------

def servicios_publicos(limite=None, categoria=None, q=''):
    sql = ('SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.stock, p.imagen, '
           '       c.nombre AS categoria, e.nombre AS estado '
           'FROM productos p '
           'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
           'INNER JOIN estados e ON e.id_estado = p.id_estado '
           "WHERE p.activo = TRUE AND e.nombre <> 'Inactivo' ")
    params = []
    if categoria:
        sql += 'AND c.id_categoria = %s '
        params.append(categoria)
    if q:
        sql += 'AND LOWER(p.nombre) LIKE LOWER(%s) '
        params.append('%' + q + '%')
    sql += 'ORDER BY p.stock = 0, p.id_producto'
    filas = consultar(sql, tuple(params))
    return filas[:limite] if limite else filas


def boletines_publicos(limite=None):
    filas = consultar(
        'SELECT b.id_boletin, b.titulo, b.resumen, b.nivel, b.referencia, b.fecha, '
        '       c.nombre AS categoria, pr.nombre AS fuente '
        'FROM boletines b '
        'INNER JOIN categorias c ON c.id_categoria = b.id_categoria '
        'LEFT JOIN proveedores pr ON pr.id_proveedor = b.id_proveedor '
        'WHERE b.activo = TRUE ORDER BY b.fecha DESC, b.id_boletin DESC')
    return filas[:limite] if limite else filas


def formulario_solicitud():
    form = SolicitudForm()
    form.id_producto.choices = opciones_productos()
    form.id_estado.choices = opciones_estados('solicitud')
    return form


@app.route('/')
def inicio():
    # La portada es pública, así que no debe caerse si la base de datos aún no
    # responde: en ese caso se muestra sin el contenido dinámico.
    try:
        servicios = servicios_publicos(limite=6)
        boletines = boletines_publicos(limite=3)
        cifras = {
            'servicios': contar('SELECT COUNT(*) AS t FROM productos WHERE activo = TRUE'),
            'organizaciones': contar('SELECT COUNT(*) AS t FROM clientes WHERE activo = TRUE'),
            'boletines': contar('SELECT COUNT(*) AS t FROM boletines WHERE activo = TRUE'),
            'fuentes': contar('SELECT COUNT(*) AS t FROM proveedores WHERE activo = TRUE'),
        }
        form = formulario_solicitud()
    except Exception as error:  # noqa: BLE001
        app.logger.error('Portada sin base de datos: %s', error)
        servicios, boletines, cifras, form = [], [], None, None
    return render_template('index.html', titulo='Inicio', servicios=servicios,
                           boletines=boletines, cifras=cifras, pilares=PILARES, form=form)


@app.route('/servicios')
def catalogo_servicios():
    categoria = request.args.get('categoria', type=int)
    q = texto_buscado()
    return render_template('servicios.html', titulo='Servicios CTI',
                           servicios=servicios_publicos(categoria=categoria, q=q),
                           categorias=opciones_categorias(), categoria=categoria, q=q)


@app.route('/boletines-publicos')
def boletines_publicados():
    return render_template('boletines_publicos.html', titulo='Boletines',
                           boletines=boletines_publicos())


@app.route('/solicitar', methods=['GET', 'POST'])
def solicitar():
    """Formulario público de solicitud de información (se guarda en la base)."""
    form = formulario_solicitud()
    if request.method == 'GET' and request.args.get('servicio', type=int):
        form.id_producto.data = request.args.get('servicio', type=int)

    if form.validate_on_submit():
        id_nueva = _id_por_nombre('estados', 'id_estado', 'Nueva', " AND ambito = 'solicitud'")
        insertar('INSERT INTO solicitudes (nombre, organizacion, correo, telefono, id_producto, '
                 'id_estado, mensaje) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                 (form.nombre.data.strip(), form.organizacion.data.strip(), form.correo.data.strip(),
                  form.telefono.data or None, form.id_producto.data, id_nueva, form.mensaje.data.strip()))
        registrar('CREAR', 'Solicitudes', 'Solicitud pública de ' + form.organizacion.data.strip())
        flash('Gracias, ' + form.nombre.data.split()[0] + '. Recibimos su solicitud y un analista '
              'le escribirá en menos de 24 horas.', 'success')
        return redirect(url_for('solicitar'))

    return render_template('solicitar.html', titulo='Solicitar información', form=form)


@app.route('/terminos')
def terminos():
    return render_template('terminos.html', titulo='Términos y privacidad')


# ---------------- AUTENTICACIÓN: registro, login, sesión y logout ----------------

SQL_USUARIO = ('SELECT u.id, u.usuario, u.password, r.nombre AS rol, p.nombre_completo, p.correo '
               'FROM usuarios u '
               'INNER JOIN roles r ON r.id_rol = u.id_rol '
               'LEFT JOIN perfiles_usuario p ON p.id_usuario = u.id ')


def usuario_desde_fila(data):
    return Usuario(data['id'], data['usuario'], data['password'], data['rol'],
                   data['nombre_completo'], data.get('correo'))


@login_manager.user_loader
def load_user(user_id):
    """Reconstruye el usuario autenticado a partir de su identificador."""
    data = consultar(SQL_USUARIO + 'WHERE u.id = %s', (user_id,), uno=True)
    return usuario_desde_fila(data) if data else None


def crear_usuario(form, id_rol):
    """INSERT del usuario con la contraseña cifrada y de su perfil (relación 1:1)."""
    nuevo_id = insertar(
        'INSERT INTO usuarios (usuario, password, id_rol) VALUES (%s, %s, %s)',
        (form.usuario.data, generate_password_hash(form.password.data), id_rol)
    )
    ejecutar('INSERT INTO perfiles_usuario (id_usuario, nombre_completo, correo) VALUES (%s, %s, %s)',
             (nuevo_id, form.nombre_completo.data.strip(), form.correo.data.strip()))
    return nuevo_id


def datos_duplicados(form):
    if consultar('SELECT id FROM usuarios WHERE usuario = %s', (form.usuario.data,), uno=True):
        return 'El usuario "' + form.usuario.data + '" ya está registrado.'
    if consultar('SELECT id_perfil FROM perfiles_usuario WHERE correo = %s', (form.correo.data,), uno=True):
        return 'El correo ' + form.correo.data + ' ya pertenece a otra cuenta.'
    return None


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = UsuarioForm()
    form.id_rol.choices = opciones_roles()
    # En el registro público el rol no se elige: se asigna el de Analista.
    # La única excepción es la primera cuenta del sistema, que queda como
    # Administrador para que alguien pueda gestionar usuarios y bitácora.
    id_analista = _id_por_nombre('roles', 'id_rol', 'Analista')
    if contar('SELECT COUNT(*) AS t FROM usuarios') == 0:
        id_analista = _id_por_nombre('roles', 'id_rol', 'Administrador')
    if request.method == 'GET':
        form.id_rol.data = id_analista

    if form.validate_on_submit():
        error = datos_duplicados(form)
        if error:
            flash(error, 'danger')
        else:
            crear_usuario(form, id_analista)
            registrar('CREAR', 'Usuarios', 'Registro de la cuenta ' + form.usuario.data)
            flash('Cuenta "' + form.usuario.data + '" creada correctamente. Ya puede iniciar sesión.', 'success')
            return redirect(url_for('login'))

    return render_template('registro.html', titulo='Crear cuenta', form=form, publico=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        # Se puede ingresar con el nombre de usuario o con el correo del perfil.
        data = consultar(SQL_USUARIO + 'WHERE u.usuario = %s OR p.correo = %s',
                         (form.usuario.data.strip(), form.usuario.data.strip()), uno=True)
        # La contraseña escrita nunca se compara directamente con la almacenada.
        if data and check_password_hash(data['password'], form.password.data):
            login_user(usuario_desde_fila(data), remember=form.recordar.data)
            registrar('LOGIN', 'Sesión', 'Inicio de sesión')
            flash('Bienvenido, ' + (data['nombre_completo'] or data['usuario']) + '.', 'success')
            siguiente = request.args.get('next')
            # Solo se aceptan rutas internas para evitar redirecciones abiertas.
            if not siguiente or not siguiente.startswith('/') or siguiente.startswith('//'):
                siguiente = url_for('dashboard')
            return redirect(siguiente)
        flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html', titulo='Iniciar sesión', form=form)


@app.route('/logout')
@login_required
def logout():
    nombre = current_user.usuario
    registrar('LOGOUT', 'Sesión', 'Cierre de sesión')
    logout_user()
    flash('Sesión cerrada correctamente. Hasta pronto, ' + nombre + '.', 'info')
    return redirect(url_for('login'))


# ---------------- PANEL DE CONTROL ----------------

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


# ---------------- SERVICIOS CTI (tabla productos) ----------------

def cargar_opciones_producto(form):
    form.id_categoria.choices = opciones_categorias()
    form.id_estado.choices = opciones_estados('producto')
    form.id_proveedor.choices = opciones_proveedores()
    form.imagen.choices = IMAGENES_SERVICIO


def listar_productos(ver='activos', q=''):
    """SELECT con JOIN a categorías, estados y fuentes."""
    sql = ('SELECT p.id_producto, p.nombre, p.precio, p.stock, p.descripcion, p.imagen, p.activo, '
           '       c.nombre AS categoria, e.nombre AS estado, pr.nombre AS proveedor '
           'FROM productos p '
           'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
           'INNER JOIN estados e ON e.id_estado = p.id_estado '
           'LEFT JOIN proveedores pr ON pr.id_proveedor = p.id_proveedor '
           'WHERE ' + filtro_vista(ver, 'p') + ' ')
    params = ()
    if q:
        sql += 'AND (LOWER(p.nombre) LIKE LOWER(%s) OR LOWER(c.nombre) LIKE LOWER(%s)) '
        params = ('%' + q + '%', '%' + q + '%')
    return consultar(sql + 'ORDER BY p.id_producto', params)


@app.route('/productos')
@login_required
def ver_productos():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_productos(ver, q), pagina_pedida())
    return render_template('productos.html', titulo='Servicios CTI', productos=registros,
                           paginacion=paginacion, ver=ver, q=q)


@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    form = ProductoForm()
    cargar_opciones_producto(form)
    if form.validate_on_submit():
        insertar(
            'INSERT INTO productos (nombre, id_categoria, id_estado, precio, stock, '
            '                       descripcion, id_proveedor, imagen) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (form.nombre.data.strip(), form.id_categoria.data, form.id_estado.data, form.precio.data,
             form.stock.data, form.descripcion.data.strip(), form.id_proveedor.data, form.imagen.data)
        )
        registrar('CREAR', 'Servicios', form.nombre.data.strip())
        flash('Servicio "' + form.nombre.data.strip() + '" agregado correctamente.', 'success')
        return redirect(url_for('ver_productos'))
    return render_template('formulario_producto.html', titulo='Nuevo servicio', form=form, producto=None)


@app.route('/productos/editar/<int:id_producto>', methods=['GET', 'POST'])
@login_required
def editar_producto(id_producto):
    producto = consultar('SELECT * FROM productos WHERE id_producto = %s', (id_producto,), uno=True)
    if producto is None:
        abort(404)

    form = ProductoForm(data=producto)
    cargar_opciones_producto(form)
    form.enviar.label.text = 'Actualizar servicio'

    if form.validate_on_submit():
        ejecutar(
            'UPDATE productos SET nombre = %s, id_categoria = %s, id_estado = %s, precio = %s, '
            '       stock = %s, descripcion = %s, id_proveedor = %s, imagen = %s '
            'WHERE id_producto = %s',
            (form.nombre.data.strip(), form.id_categoria.data, form.id_estado.data, form.precio.data,
             form.stock.data, form.descripcion.data.strip(), form.id_proveedor.data, form.imagen.data,
             id_producto)
        )
        registrar('EDITAR', 'Servicios', form.nombre.data.strip())
        flash('Servicio "' + form.nombre.data.strip() + '" actualizado correctamente.', 'success')
        return redirect(url_for('ver_productos'))

    return render_template('formulario_producto.html', titulo='Editar servicio', form=form,
                           producto=producto)


@app.route('/productos/baja/<int:id_producto>', methods=['POST'])
@login_required
def baja_producto(id_producto):
    """Baja lógica: el servicio sale del catálogo pero se conserva en la base."""
    if cambiar_activo('productos', 'id_producto', id_producto, False):
        registrar('BAJA', 'Servicios', 'ID ' + str(id_producto))
        flash('Servicio dado de baja. El registro se conserva como histórico.', 'warning')
    else:
        flash('El servicio no existe.', 'danger')
    return redirect(url_for('ver_productos'))


@app.route('/productos/reactivar/<int:id_producto>', methods=['POST'])
@login_required
def reactivar_producto(id_producto):
    if cambiar_activo('productos', 'id_producto', id_producto, True):
        registrar('REACTIVAR', 'Servicios', 'ID ' + str(id_producto))
        flash('Servicio reactivado correctamente.', 'success')
    else:
        flash('El servicio no existe.', 'danger')
    return redirect(url_for('ver_productos', ver='baja'))


@app.route('/productos/eliminar/<int:id_producto>', methods=['POST'])
@login_required
def eliminar_producto(id_producto):
    """Borrado definitivo con DELETE, el que piden las guías de la Semana 13."""
    if contar('SELECT COUNT(*) AS t FROM detalle_factura WHERE id_producto = %s', (id_producto,)) or \
            contar('SELECT COUNT(*) AS t FROM solicitudes WHERE id_producto = %s', (id_producto,)):
        flash('No se puede eliminar: el servicio está en una suscripción o una solicitud. '
              'Use "Dar de baja" para conservar el histórico.', 'danger')
        return redirect(url_for('ver_productos'))

    if ejecutar('DELETE FROM productos WHERE id_producto = %s', (id_producto,)):
        registrar('ELIMINAR', 'Servicios', 'ID ' + str(id_producto))
        flash('Servicio eliminado definitivamente.', 'warning')
    else:
        flash('El servicio no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_productos'))


# ---------------- ORGANIZACIONES (tabla clientes) ----------------

def cargar_opciones_cliente(form, actual=None):
    form.id_sector.choices = opciones_sectores()
    form.id_parroquia.choices = opciones_parroquias()
    form.servicio.choices = opciones_nombre_servicios()
    # Un registro antiguo puede tener un servicio que ya no está en el catálogo:
    # se conserva como opción para que se pueda editar sin perder el dato.
    if actual and actual not in [valor for valor, _ in form.servicio.choices]:
        form.servicio.choices.insert(0, (actual, actual))


def listar_clientes(ver='activos', q=''):
    """SELECT con JOIN a sectores y a las tres tablas de ubicación geográfica."""
    sql = ('SELECT c.id_cliente, c.nombre, c.ruc, c.servicio, c.correo, c.telefono, c.activo, '
           '       s.nombre AS sector, pa.nombre AS parroquia, ca.nombre AS canton, '
           '       pr.nombre AS provincia '
           'FROM clientes c '
           'INNER JOIN sectores s ON s.id_sector = c.id_sector '
           'INNER JOIN parroquias pa ON pa.id_parroquia = c.id_parroquia '
           'INNER JOIN cantones ca ON ca.id_canton = pa.id_canton '
           'INNER JOIN provincias pr ON pr.id_provincia = ca.id_provincia '
           'WHERE ' + filtro_vista(ver, 'c') + ' ')
    params = ()
    if q:
        sql += 'AND (LOWER(c.nombre) LIKE LOWER(%s) OR c.ruc LIKE %s) '
        params = ('%' + q + '%', '%' + q + '%')
    return consultar(sql + 'ORDER BY c.id_cliente', params)


def ruc_repetido(ruc, id_cliente=None):
    if not ruc:
        return False
    fila = consultar('SELECT id_cliente FROM clientes WHERE ruc = %s', (ruc,), uno=True)
    return fila is not None and fila['id_cliente'] != id_cliente


@app.route('/clientes')
@login_required
def ver_clientes():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_clientes(ver, q), pagina_pedida())
    return render_template('clientes.html', titulo='Organizaciones', clientes=registros,
                           paginacion=paginacion, total_clientes=paginacion['total'], ver=ver, q=q)


@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    form = ClienteForm()
    cargar_opciones_cliente(form)
    if form.validate_on_submit():
        if ruc_repetido(form.ruc.data):
            form.ruc.errors.append('Ya existe una organización con ese RUC')
        else:
            insertar(
                'INSERT INTO clientes (nombre, ruc, id_sector, id_parroquia, servicio, correo, telefono) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (form.nombre.data.strip(), form.ruc.data or None, form.id_sector.data,
                 form.id_parroquia.data, form.servicio.data, form.correo.data.strip(),
                 form.telefono.data or None)
            )
            registrar('CREAR', 'Organizaciones', form.nombre.data.strip())
            flash('Organización "' + form.nombre.data.strip() + '" agregada correctamente.', 'success')
            return redirect(url_for('ver_clientes'))
    return render_template('formulario_cliente.html', titulo='Nueva organización', form=form, cliente=None)


@app.route('/clientes/editar/<int:id_cliente>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id_cliente):
    cliente = consultar('SELECT * FROM clientes WHERE id_cliente = %s', (id_cliente,), uno=True)
    if cliente is None:
        abort(404)

    form = ClienteForm(data=cliente)
    cargar_opciones_cliente(form, cliente['servicio'])
    form.enviar.label.text = 'Actualizar organización'

    if form.validate_on_submit():
        if ruc_repetido(form.ruc.data, id_cliente):
            form.ruc.errors.append('Ya existe una organización con ese RUC')
        else:
            ejecutar(
                'UPDATE clientes SET nombre = %s, ruc = %s, id_sector = %s, id_parroquia = %s, '
                '       servicio = %s, correo = %s, telefono = %s '
                'WHERE id_cliente = %s',
                (form.nombre.data.strip(), form.ruc.data or None, form.id_sector.data,
                 form.id_parroquia.data, form.servicio.data, form.correo.data.strip(),
                 form.telefono.data or None, id_cliente)
            )
            registrar('EDITAR', 'Organizaciones', form.nombre.data.strip())
            flash('Organización "' + form.nombre.data.strip() + '" actualizada correctamente.', 'success')
            return redirect(url_for('ver_clientes'))

    return render_template('formulario_cliente.html', titulo='Editar organización', form=form,
                           cliente=cliente)


@app.route('/clientes/baja/<int:id_cliente>', methods=['POST'])
@login_required
def baja_cliente(id_cliente):
    if cambiar_activo('clientes', 'id_cliente', id_cliente, False):
        registrar('BAJA', 'Organizaciones', 'ID ' + str(id_cliente))
        flash('Organización dada de baja. El registro se conserva como histórico.', 'warning')
    else:
        flash('La organización no existe.', 'danger')
    return redirect(url_for('ver_clientes'))


@app.route('/clientes/reactivar/<int:id_cliente>', methods=['POST'])
@login_required
def reactivar_cliente(id_cliente):
    if cambiar_activo('clientes', 'id_cliente', id_cliente, True):
        registrar('REACTIVAR', 'Organizaciones', 'ID ' + str(id_cliente))
        flash('Organización reactivada correctamente.', 'success')
    else:
        flash('La organización no existe.', 'danger')
    return redirect(url_for('ver_clientes', ver='baja'))


@app.route('/clientes/eliminar/<int:id_cliente>', methods=['POST'])
@login_required
def eliminar_cliente(id_cliente):
    """Borrado definitivo con DELETE, el que piden las guías de la Semana 13."""
    if contar('SELECT COUNT(*) AS t FROM facturas WHERE id_cliente = %s', (id_cliente,)):
        flash('No se puede eliminar: la organización tiene suscripciones registradas. '
              'Use "Dar de baja" para conservar el histórico.', 'danger')
        return redirect(url_for('ver_clientes'))

    if ejecutar('DELETE FROM clientes WHERE id_cliente = %s', (id_cliente,)):
        registrar('ELIMINAR', 'Organizaciones', 'ID ' + str(id_cliente))
        flash('Organización eliminada definitivamente.', 'warning')
    else:
        flash('La organización no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_clientes'))


# ---------------- FUENTES DE INTELIGENCIA (tabla proveedores) ----------------

def listar_proveedores(ver='activos', q=''):
    """SELECT con JOIN al catálogo de tipos y conteo de servicios asociados."""
    sql = ('SELECT pr.id_proveedor, pr.nombre, pr.aporte, pr.correo, pr.telefono, pr.activo, '
           '       t.nombre AS tipo, COUNT(p.id_producto) AS total_productos '
           'FROM proveedores pr '
           'INNER JOIN tipos_proveedor t ON t.id_tipo = pr.id_tipo '
           'LEFT JOIN productos p ON p.id_proveedor = pr.id_proveedor '
           'WHERE ' + filtro_vista(ver, 'pr') + ' ')
    params = ()
    if q:
        sql += 'AND LOWER(pr.nombre) LIKE LOWER(%s) '
        params = ('%' + q + '%',)
    return consultar(sql + 'GROUP BY pr.id_proveedor, pr.nombre, pr.aporte, pr.correo, pr.telefono, '
                     'pr.activo, t.nombre ORDER BY pr.id_proveedor', params)


@app.route('/proveedores')
@login_required
def ver_proveedores():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_proveedores(ver, q), pagina_pedida())
    return render_template('proveedores.html', titulo='Fuentes de inteligencia', proveedores=registros,
                           paginacion=paginacion, ver=ver, q=q)


@app.route('/proveedores/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_proveedor():
    form = ProveedorForm()
    form.id_tipo.choices = opciones_tipos_proveedor()
    if form.validate_on_submit():
        insertar('INSERT INTO proveedores (nombre, id_tipo, aporte, correo, telefono) '
                 'VALUES (%s, %s, %s, %s, %s)',
                 (form.nombre.data.strip(), form.id_tipo.data, form.aporte.data.strip(),
                  form.correo.data or None, form.telefono.data or None))
        registrar('CREAR', 'Fuentes', form.nombre.data.strip())
        flash('Fuente "' + form.nombre.data.strip() + '" agregada correctamente.', 'success')
        return redirect(url_for('ver_proveedores'))
    return render_template('formulario_proveedor.html', titulo='Nueva fuente', form=form, proveedor=None)


@app.route('/proveedores/editar/<int:id_proveedor>', methods=['GET', 'POST'])
@login_required
def editar_proveedor(id_proveedor):
    proveedor = consultar('SELECT * FROM proveedores WHERE id_proveedor = %s', (id_proveedor,), uno=True)
    if proveedor is None:
        abort(404)

    form = ProveedorForm(data=proveedor)
    form.id_tipo.choices = opciones_tipos_proveedor()
    form.enviar.label.text = 'Actualizar fuente'

    if form.validate_on_submit():
        ejecutar('UPDATE proveedores SET nombre = %s, id_tipo = %s, aporte = %s, correo = %s, telefono = %s '
                 'WHERE id_proveedor = %s',
                 (form.nombre.data.strip(), form.id_tipo.data, form.aporte.data.strip(),
                  form.correo.data or None, form.telefono.data or None, id_proveedor))
        registrar('EDITAR', 'Fuentes', form.nombre.data.strip())
        flash('Fuente "' + form.nombre.data.strip() + '" actualizada correctamente.', 'success')
        return redirect(url_for('ver_proveedores'))

    return render_template('formulario_proveedor.html', titulo='Editar fuente', form=form,
                           proveedor=proveedor)


@app.route('/proveedores/baja/<int:id_proveedor>', methods=['POST'])
@login_required
def baja_proveedor(id_proveedor):
    if cambiar_activo('proveedores', 'id_proveedor', id_proveedor, False):
        registrar('BAJA', 'Fuentes', 'ID ' + str(id_proveedor))
        flash('Fuente dada de baja. El registro se conserva como histórico.', 'warning')
    else:
        flash('La fuente no existe.', 'danger')
    return redirect(url_for('ver_proveedores'))


@app.route('/proveedores/reactivar/<int:id_proveedor>', methods=['POST'])
@login_required
def reactivar_proveedor(id_proveedor):
    if cambiar_activo('proveedores', 'id_proveedor', id_proveedor, True):
        registrar('REACTIVAR', 'Fuentes', 'ID ' + str(id_proveedor))
        flash('Fuente reactivada correctamente.', 'success')
    else:
        flash('La fuente no existe.', 'danger')
    return redirect(url_for('ver_proveedores', ver='baja'))


@app.route('/proveedores/eliminar/<int:id_proveedor>', methods=['POST'])
@login_required
def eliminar_proveedor(id_proveedor):
    """Borrado definitivo con DELETE. Los servicios y boletines quedan sin fuente."""
    if ejecutar('DELETE FROM proveedores WHERE id_proveedor = %s', (id_proveedor,)):
        registrar('ELIMINAR', 'Fuentes', 'ID ' + str(id_proveedor))
        flash('Fuente eliminada. Los servicios asociados quedaron sin fuente asignada.', 'warning')
    else:
        flash('La fuente no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_proveedores'))


# ---------------- SUSCRIPCIONES (tablas facturas y detalle_factura) ----------------

def cargar_opciones_factura(form):
    form.id_cliente.choices = opciones_clientes()
    form.id_estado.choices = opciones_estados('factura')


def listar_facturas(ver='activos', q=''):
    """SELECT con JOIN a organizaciones y estados, y conteo de líneas de detalle."""
    sql = ('SELECT f.id_factura, f.codigo, f.servicio, f.fecha, f.total, f.activo, '
           '       c.nombre AS cliente, e.nombre AS estado, COUNT(d.id_detalle) AS lineas '
           'FROM facturas f '
           'INNER JOIN clientes c ON c.id_cliente = f.id_cliente '
           'INNER JOIN estados e ON e.id_estado = f.id_estado '
           'LEFT JOIN detalle_factura d ON d.id_factura = f.id_factura '
           'WHERE ' + filtro_vista(ver, 'f') + ' ')
    params = ()
    if q:
        sql += 'AND (LOWER(f.codigo) LIKE LOWER(%s) OR LOWER(c.nombre) LIKE LOWER(%s)) '
        params = ('%' + q + '%', '%' + q + '%')
    return consultar(sql + 'GROUP BY f.id_factura, f.codigo, f.servicio, f.fecha, f.total, f.activo, '
                     'c.nombre, e.nombre ORDER BY f.id_factura DESC', params)


def siguiente_codigo():
    """Propone el siguiente código FAC-NNN a partir del mayor existente."""
    numeros = []
    for fila in consultar("SELECT codigo FROM facturas WHERE codigo LIKE 'FAC-%'"):
        try:
            numeros.append(int(fila['codigo'].split('-')[1]))
        except (IndexError, ValueError):
            pass
    return 'FAC-%03d' % (max(numeros or [0]) + 1)


@app.route('/facturacion')
@login_required
def ver_facturacion():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_facturas(ver, q), pagina_pedida())
    return render_template('facturacion.html', titulo='Suscripciones', facturas=registros,
                           paginacion=paginacion, total_facturas=paginacion['total'], ver=ver, q=q)


@app.route('/facturacion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_factura():
    form = FacturacionForm()
    cargar_opciones_factura(form)
    if request.method == 'GET':
        form.codigo.data = siguiente_codigo()
        form.fecha.data = date.today()

    if form.validate_on_submit():
        if consultar('SELECT id_factura FROM facturas WHERE codigo = %s', (form.codigo.data,), uno=True):
            form.codigo.errors.append('Ya existe una suscripción con ese código')
        else:
            nuevo_id = insertar(
                'INSERT INTO facturas (codigo, id_cliente, id_estado, servicio, fecha) '
                'VALUES (%s, %s, %s, %s, %s)',
                (form.codigo.data.upper(), form.id_cliente.data, form.id_estado.data,
                 form.servicio.data.strip(), form.fecha.data))
            registrar('CREAR', 'Suscripciones', form.codigo.data.upper())
            flash('Suscripción ' + form.codigo.data.upper() + ' registrada. Agregue ahora los servicios '
                  'que incluye.', 'success')
            return redirect(url_for('detalle_factura', id_factura=nuevo_id))
    return render_template('formulario_facturacion.html', titulo='Nueva suscripción', form=form, factura=None)


@app.route('/facturacion/editar/<int:id_factura>', methods=['GET', 'POST'])
@login_required
def editar_factura(id_factura):
    factura = consultar('SELECT * FROM facturas WHERE id_factura = %s', (id_factura,), uno=True)
    if factura is None:
        abort(404)

    form = FacturacionForm(data=factura)
    cargar_opciones_factura(form)
    form.enviar.label.text = 'Actualizar suscripción'

    if form.validate_on_submit():
        repetida = consultar('SELECT id_factura FROM facturas WHERE codigo = %s', (form.codigo.data,), uno=True)
        if repetida and repetida['id_factura'] != id_factura:
            form.codigo.errors.append('Ya existe una suscripción con ese código')
        else:
            ejecutar('UPDATE facturas SET codigo = %s, id_cliente = %s, id_estado = %s, servicio = %s, fecha = %s '
                     'WHERE id_factura = %s',
                     (form.codigo.data.upper(), form.id_cliente.data, form.id_estado.data,
                      form.servicio.data.strip(), form.fecha.data, id_factura))
            registrar('EDITAR', 'Suscripciones', form.codigo.data.upper())
            flash('Suscripción ' + form.codigo.data.upper() + ' actualizada correctamente.', 'success')
            return redirect(url_for('ver_facturacion'))

    return render_template('formulario_facturacion.html', titulo='Editar suscripción', form=form,
                           factura=factura)


@app.route('/facturacion/baja/<int:id_factura>', methods=['POST'])
@login_required
def baja_factura(id_factura):
    """Baja lógica: lo correcto en facturación, porque una factura no se borra."""
    if cambiar_activo('facturas', 'id_factura', id_factura, False):
        registrar('BAJA', 'Suscripciones', 'ID ' + str(id_factura))
        flash('Suscripción dada de baja. La factura se conserva como histórico.', 'warning')
    else:
        flash('La suscripción no existe.', 'danger')
    return redirect(url_for('ver_facturacion'))


@app.route('/facturacion/reactivar/<int:id_factura>', methods=['POST'])
@login_required
def reactivar_factura(id_factura):
    if cambiar_activo('facturas', 'id_factura', id_factura, True):
        registrar('REACTIVAR', 'Suscripciones', 'ID ' + str(id_factura))
        flash('Suscripción reactivada correctamente.', 'success')
    else:
        flash('La suscripción no existe.', 'danger')
    return redirect(url_for('ver_facturacion', ver='baja'))


@app.route('/facturacion/eliminar/<int:id_factura>', methods=['POST'])
@login_required
def eliminar_factura(id_factura):
    """Borrado definitivo con DELETE: devuelve los cupos y elimina el detalle en cascada."""
    for linea in consultar('SELECT id_producto, cantidad FROM detalle_factura WHERE id_factura = %s',
                           (id_factura,)):
        ejecutar('UPDATE productos SET stock = stock + %s WHERE id_producto = %s',
                 (linea['cantidad'], linea['id_producto']))
    if ejecutar('DELETE FROM facturas WHERE id_factura = %s', (id_factura,)):
        registrar('ELIMINAR', 'Suscripciones', 'ID ' + str(id_factura))
        flash('Suscripción eliminada junto con su detalle. Los cupos volvieron al catálogo.', 'warning')
    else:
        flash('La suscripción no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_facturacion'))


def datos_factura(id_factura):
    return consultar(
        'SELECT f.id_factura, f.codigo, f.servicio, f.fecha, f.total, f.activo, '
        '       c.nombre AS cliente, c.ruc, c.correo, c.telefono, e.nombre AS estado, '
        "       CONCAT(pr.nombre, ' / ', ca.nombre, ' / ', pa.nombre) AS ubicacion "
        'FROM facturas f '
        'INNER JOIN clientes c ON c.id_cliente = f.id_cliente '
        'INNER JOIN estados e ON e.id_estado = f.id_estado '
        'INNER JOIN parroquias pa ON pa.id_parroquia = c.id_parroquia '
        'INNER JOIN cantones ca ON ca.id_canton = pa.id_canton '
        'INNER JOIN provincias pr ON pr.id_provincia = ca.id_provincia '
        'WHERE f.id_factura = %s', (id_factura,), uno=True)


def lineas_factura(id_factura):
    return consultar(
        'SELECT d.id_detalle, d.id_producto, d.cantidad, d.precio_unitario, '
        '       (d.cantidad * d.precio_unitario) AS subtotal, p.nombre AS producto, c.nombre AS categoria '
        'FROM detalle_factura d '
        'INNER JOIN productos p ON p.id_producto = d.id_producto '
        'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
        'WHERE d.id_factura = %s ORDER BY d.id_detalle', (id_factura,))


@app.route('/facturacion/detalle/<int:id_factura>', methods=['GET', 'POST'])
@login_required
def detalle_factura(id_factura):
    """Gestiona la relación muchos a muchos entre suscripciones y servicios."""
    factura = datos_factura(id_factura)
    if factura is None:
        abort(404)

    form = DetalleFacturaForm()
    form.id_producto.choices = opciones_productos(con_cupos=True)

    if form.validate_on_submit():
        servicio = consultar('SELECT nombre, stock, precio FROM productos WHERE id_producto = %s',
                             (form.id_producto.data,), uno=True)
        repetido = consultar('SELECT id_detalle FROM detalle_factura WHERE id_factura = %s AND id_producto = %s',
                             (id_factura, form.id_producto.data), uno=True)
        if servicio is None:
            flash('El servicio seleccionado no existe.', 'danger')
        elif repetido:
            flash('Ese servicio ya forma parte del detalle de la suscripción.', 'danger')
        elif form.cantidad.data > servicio['stock']:
            # Control de cupos: no se puede vender más de lo disponible.
            flash('No hay cupos suficientes de "' + servicio['nombre'] + '": se pidieron ' +
                  str(form.cantidad.data) + ' y quedan ' + str(servicio['stock']) + '.', 'danger')
        else:
            precio = form.precio_unitario.data if form.precio_unitario.data is not None else servicio['precio']
            ejecutar('INSERT INTO detalle_factura (id_factura, id_producto, cantidad, precio_unitario) '
                     'VALUES (%s, %s, %s, %s)', (id_factura, form.id_producto.data, form.cantidad.data, precio))
            ejecutar('UPDATE productos SET stock = stock - %s WHERE id_producto = %s',
                     (form.cantidad.data, form.id_producto.data))
            recalcular_total(id_factura)
            registrar('CREAR', 'Suscripciones', 'Detalle de ' + factura['codigo'] + ': ' + servicio['nombre'])
            flash('Servicio agregado. Se descontaron ' + str(form.cantidad.data) + ' cupo(s) de "' +
                  servicio['nombre'] + '".', 'success')
        return redirect(url_for('detalle_factura', id_factura=id_factura))

    return render_template('detalle_factura.html', titulo='Detalle de la suscripción',
                           factura=factura, lineas=lineas_factura(id_factura), form=form)


@app.route('/facturacion/detalle/<int:id_factura>/eliminar/<int:id_detalle>', methods=['POST'])
@login_required
def eliminar_detalle(id_factura, id_detalle):
    linea = consultar('SELECT id_producto, cantidad FROM detalle_factura WHERE id_detalle = %s AND id_factura = %s',
                      (id_detalle, id_factura), uno=True)
    if linea and ejecutar('DELETE FROM detalle_factura WHERE id_detalle = %s AND id_factura = %s',
                          (id_detalle, id_factura)):
        ejecutar('UPDATE productos SET stock = stock + %s WHERE id_producto = %s',
                 (linea['cantidad'], linea['id_producto']))
        recalcular_total(id_factura)
        registrar('ELIMINAR', 'Suscripciones', 'Línea ' + str(id_detalle) + ' de la factura ' + str(id_factura))
        flash('Línea quitada del detalle. Los cupos volvieron al servicio.', 'warning')
    else:
        flash('La línea no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('detalle_factura', id_factura=id_factura))


@app.route('/facturacion/<int:id_factura>/comprobante')
@login_required
def comprobante_factura(id_factura):
    """Comprobante imprimible de la suscripción (se imprime o guarda como PDF)."""
    factura = datos_factura(id_factura)
    if factura is None:
        abort(404)
    lineas = lineas_factura(id_factura)
    subtotal = sum(Decimal(str(l['subtotal'])) for l in lineas)
    return render_template('comprobante.html', titulo='Comprobante ' + factura['codigo'],
                           factura=factura, lineas=lineas, subtotal=subtotal,
                           emitido=datetime.now())


@app.route('/facturacion/<int:id_factura>/pdf')
@login_required
def pdf_factura(id_factura):
    factura = datos_factura(id_factura)
    if factura is None:
        abort(404)
    lineas = lineas_factura(id_factura)
    filas = [[str(i + 1), l['producto'], str(l['cantidad']), filtro_dinero(l['precio_unitario']),
              filtro_dinero(l['subtotal'])] for i, l in enumerate(lineas)]
    filas.append(['', '', '', 'TOTAL', filtro_dinero(factura['total'])])
    contenido = generar_pdf(
        'Comprobante de suscripción ' + factura['codigo'],
        ['Organización: ' + factura['cliente'] + ('  -  RUC ' + factura['ruc'] if factura['ruc'] else ''),
         'Ubicación: ' + factura['ubicacion'],
         'Fecha de emisión: ' + filtro_fecha(factura['fecha']) + '   Estado: ' + factura['estado']],
        ['#', 'Servicio', 'Cant.', 'P. unitario (USD)', 'Subtotal (USD)'], filas)
    registrar('EXPORTAR', 'Suscripciones', 'PDF de ' + factura['codigo'])
    return Response(contenido, mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment; filename=' + factura['codigo'] + '.pdf'})


# ---------------- BOLETINES ----------------

def cargar_opciones_boletin(form):
    form.id_categoria.choices = opciones_categorias()
    form.id_proveedor.choices = opciones_proveedores()


def listar_boletines(ver='activos', q=''):
    sql = ('SELECT b.id_boletin, b.titulo, b.resumen, b.nivel, b.referencia, b.fecha, b.activo, '
           '       c.nombre AS categoria, pr.nombre AS fuente '
           'FROM boletines b '
           'INNER JOIN categorias c ON c.id_categoria = b.id_categoria '
           'LEFT JOIN proveedores pr ON pr.id_proveedor = b.id_proveedor '
           'WHERE ' + filtro_vista(ver, 'b') + ' ')
    params = ()
    if q:
        sql += 'AND LOWER(b.titulo) LIKE LOWER(%s) '
        params = ('%' + q + '%',)
    return consultar(sql + 'ORDER BY b.fecha DESC, b.id_boletin DESC', params)


@app.route('/boletines')
@login_required
def ver_boletines():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_boletines(ver, q), pagina_pedida())
    return render_template('boletines.html', titulo='Boletines', boletines=registros,
                           paginacion=paginacion, ver=ver, q=q)


@app.route('/boletines/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_boletin():
    form = BoletinForm()
    cargar_opciones_boletin(form)
    if request.method == 'GET':
        form.fecha.data = date.today()
    if form.validate_on_submit():
        insertar('INSERT INTO boletines (titulo, resumen, nivel, referencia, fecha, id_categoria, id_proveedor) '
                 'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                 (form.titulo.data.strip(), form.resumen.data.strip(), form.nivel.data,
                  form.referencia.data or None, form.fecha.data, form.id_categoria.data, form.id_proveedor.data))
        registrar('CREAR', 'Boletines', form.titulo.data.strip())
        flash('Boletín publicado. Ya aparece en la página principal.', 'success')
        return redirect(url_for('ver_boletines'))
    return render_template('formulario_boletin.html', titulo='Nuevo boletín', form=form, boletin=None)


@app.route('/boletines/editar/<int:id_boletin>', methods=['GET', 'POST'])
@login_required
def editar_boletin(id_boletin):
    boletin = consultar('SELECT * FROM boletines WHERE id_boletin = %s', (id_boletin,), uno=True)
    if boletin is None:
        abort(404)
    form = BoletinForm(data=boletin)
    cargar_opciones_boletin(form)
    form.enviar.label.text = 'Actualizar boletín'
    if form.validate_on_submit():
        ejecutar('UPDATE boletines SET titulo = %s, resumen = %s, nivel = %s, referencia = %s, fecha = %s, '
                 '       id_categoria = %s, id_proveedor = %s WHERE id_boletin = %s',
                 (form.titulo.data.strip(), form.resumen.data.strip(), form.nivel.data,
                  form.referencia.data or None, form.fecha.data, form.id_categoria.data,
                  form.id_proveedor.data, id_boletin))
        registrar('EDITAR', 'Boletines', form.titulo.data.strip())
        flash('Boletín actualizado correctamente.', 'success')
        return redirect(url_for('ver_boletines'))
    return render_template('formulario_boletin.html', titulo='Editar boletín', form=form, boletin=boletin)


@app.route('/boletines/baja/<int:id_boletin>', methods=['POST'])
@login_required
def baja_boletin(id_boletin):
    if cambiar_activo('boletines', 'id_boletin', id_boletin, False):
        registrar('BAJA', 'Boletines', 'ID ' + str(id_boletin))
        flash('Boletín retirado de la página pública. Se conserva como histórico.', 'warning')
    return redirect(url_for('ver_boletines'))


@app.route('/boletines/reactivar/<int:id_boletin>', methods=['POST'])
@login_required
def reactivar_boletin(id_boletin):
    if cambiar_activo('boletines', 'id_boletin', id_boletin, True):
        registrar('REACTIVAR', 'Boletines', 'ID ' + str(id_boletin))
        flash('Boletín publicado nuevamente.', 'success')
    return redirect(url_for('ver_boletines', ver='baja'))


@app.route('/boletines/eliminar/<int:id_boletin>', methods=['POST'])
@login_required
def eliminar_boletin(id_boletin):
    if ejecutar('DELETE FROM boletines WHERE id_boletin = %s', (id_boletin,)):
        registrar('ELIMINAR', 'Boletines', 'ID ' + str(id_boletin))
        flash('Boletín eliminado definitivamente.', 'warning')
    else:
        flash('El boletín no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_boletines'))


# ---------------- SOLICITUDES (llegan desde la página pública) ----------------

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


@app.route('/solicitudes')
@login_required
def ver_solicitudes():
    ver, q = vista_pedida(), texto_buscado()
    estado = request.args.get('estado', type=int)
    registros, paginacion = paginar(listar_solicitudes(ver, q, estado), pagina_pedida())
    return render_template('solicitudes.html', titulo='Solicitudes', solicitudes=registros,
                           paginacion=paginacion, ver=ver, q=q, estado_filtro=estado,
                           estados=opciones_estados('solicitud'))


@app.route('/solicitudes/editar/<int:id_solicitud>', methods=['GET', 'POST'])
@login_required
def editar_solicitud(id_solicitud):
    solicitud = consultar('SELECT * FROM solicitudes WHERE id_solicitud = %s', (id_solicitud,), uno=True)
    if solicitud is None:
        abort(404)
    form = SolicitudForm(data=solicitud)
    form.id_producto.choices = opciones_productos()
    form.id_estado.choices = opciones_estados('solicitud')
    form.enviar.label.text = 'Actualizar solicitud'
    if form.validate_on_submit():
        ejecutar('UPDATE solicitudes SET nombre = %s, organizacion = %s, correo = %s, telefono = %s, '
                 '       id_producto = %s, id_estado = %s, mensaje = %s WHERE id_solicitud = %s',
                 (form.nombre.data.strip(), form.organizacion.data.strip(), form.correo.data.strip(),
                  form.telefono.data or None, form.id_producto.data, form.id_estado.data,
                  form.mensaje.data.strip(), id_solicitud))
        registrar('EDITAR', 'Solicitudes', form.organizacion.data.strip())
        flash('Solicitud actualizada correctamente.', 'success')
        return redirect(url_for('ver_solicitudes'))
    return render_template('formulario_solicitud.html', titulo='Gestionar solicitud', form=form,
                           solicitud=solicitud)


@app.route('/solicitudes/baja/<int:id_solicitud>', methods=['POST'])
@login_required
def baja_solicitud(id_solicitud):
    if cambiar_activo('solicitudes', 'id_solicitud', id_solicitud, False):
        registrar('BAJA', 'Solicitudes', 'ID ' + str(id_solicitud))
        flash('Solicitud archivada. Se conserva como histórico.', 'warning')
    return redirect(url_for('ver_solicitudes'))


@app.route('/solicitudes/reactivar/<int:id_solicitud>', methods=['POST'])
@login_required
def reactivar_solicitud(id_solicitud):
    if cambiar_activo('solicitudes', 'id_solicitud', id_solicitud, True):
        registrar('REACTIVAR', 'Solicitudes', 'ID ' + str(id_solicitud))
        flash('Solicitud reactivada.', 'success')
    return redirect(url_for('ver_solicitudes', ver='baja'))


@app.route('/solicitudes/eliminar/<int:id_solicitud>', methods=['POST'])
@login_required
def eliminar_solicitud(id_solicitud):
    if ejecutar('DELETE FROM solicitudes WHERE id_solicitud = %s', (id_solicitud,)):
        registrar('ELIMINAR', 'Solicitudes', 'ID ' + str(id_solicitud))
        flash('Solicitud eliminada definitivamente.', 'warning')
    else:
        flash('La solicitud no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_solicitudes'))


# ---------------- REPORTES (Semana 15: consulta, tabla y exportación) ----------------

def rango_reporte():
    """Lee las fechas del filtro; por defecto, desde el primer día del año."""
    hoy = date.today()
    try:
        desde = date.fromisoformat(request.args.get('desde', ''))
    except ValueError:
        desde = date(hoy.year, 1, 1)
    try:
        hasta = date.fromisoformat(request.args.get('hasta', ''))
    except ValueError:
        hasta = hoy
    if hasta < desde:
        desde, hasta = hasta, desde
    return desde, hasta


def datos_reporte(desde, hasta):
    """Servicios contratados en el periodo: facturas + detalle + productos + categorías."""
    condicion = ('FROM detalle_factura d '
                 'INNER JOIN facturas f ON f.id_factura = d.id_factura '
                 'INNER JOIN productos p ON p.id_producto = d.id_producto '
                 'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
                 'INNER JOIN estados e ON e.id_estado = f.id_estado '
                 "WHERE f.activo = TRUE AND e.nombre <> 'Anulada' "
                 'AND f.fecha >= %s AND f.fecha < %s ')
    params = (desde, hasta + timedelta(days=1))
    por_servicio = consultar(
        'SELECT p.nombre AS servicio, c.nombre AS categoria, COUNT(DISTINCT f.id_factura) AS suscripciones, '
        '       SUM(d.cantidad) AS cupos, SUM(d.cantidad * d.precio_unitario) AS ingresos '
        + condicion + 'GROUP BY p.id_producto, p.nombre, c.nombre ORDER BY ingresos DESC', params)
    por_organizacion = consultar(
        'SELECT cl.nombre AS organizacion, COUNT(DISTINCT f.id_factura) AS suscripciones, '
        '       SUM(d.cantidad * d.precio_unitario) AS ingresos '
        + condicion.replace('WHERE', 'INNER JOIN clientes cl ON cl.id_cliente = f.id_cliente WHERE', 1)
        + 'GROUP BY cl.id_cliente, cl.nombre ORDER BY ingresos DESC', params)
    por_mes = consultar(
        'SELECT ' + expr_mes('f.fecha') + ' AS mes, SUM(d.cantidad * d.precio_unitario) AS ingresos '
        + condicion + 'GROUP BY ' + expr_mes('f.fecha') + ' ORDER BY mes', params)
    total = sum(Decimal(str(f['ingresos'] or 0)) for f in por_servicio)
    return por_servicio, por_organizacion, por_mes, total


@app.route('/reportes')
@login_required
def reportes():
    desde, hasta = rango_reporte()
    por_servicio, por_organizacion, por_mes, total = datos_reporte(desde, hasta)
    return render_template('reportes.html', titulo='Reportes', desde=desde, hasta=hasta,
                           por_servicio=por_servicio, por_organizacion=por_organizacion,
                           por_mes=por_mes, total=total)


def a_texto(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


@app.route('/reportes/exportar/<formato>')
@login_required
def exportar_reporte(formato):
    desde, hasta = rango_reporte()
    por_servicio, _, _, total = datos_reporte(desde, hasta)
    nombre = 'reporte_servicios_%s_%s' % (desde.isoformat(), hasta.isoformat())
    registrar('EXPORTAR', 'Reportes', formato.upper() + ' ' + desde.isoformat() + ' a ' + hasta.isoformat())

    if formato == 'csv':
        salida = io.StringIO()
        escritor = csv.writer(salida)
        escritor.writerow(['Servicio', 'Categoría', 'Suscripciones', 'Cupos', 'Ingresos (USD)'])
        for fila in por_servicio:
            escritor.writerow([fila['servicio'], fila['categoria'], fila['suscripciones'],
                               fila['cupos'], '%.2f' % float(fila['ingresos'] or 0)])
        escritor.writerow(['TOTAL', '', '', '', '%.2f' % float(total)])
        # El BOM permite que Excel abra el archivo con tildes correctas.
        return Response('﻿' + salida.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=' + nombre + '.csv'})

    if formato == 'json':
        cuerpo = {'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'total': float(total),
                  'servicios': [{k: a_texto(v) for k, v in fila.items()} for fila in por_servicio]}
        return Response(json.dumps(cuerpo, ensure_ascii=False, indent=2), mimetype='application/json',
                        headers={'Content-Disposition': 'attachment; filename=' + nombre + '.json'})

    if formato == 'pdf':
        filas = [[f['servicio'], f['categoria'], str(f['suscripciones']), str(f['cupos']),
                  filtro_dinero(f['ingresos'])] for f in por_servicio]
        filas.append(['TOTAL', '', '', '', filtro_dinero(total)])
        contenido = generar_pdf('Reporte de servicios contratados',
                                ['Periodo: ' + filtro_fecha(desde) + ' al ' + filtro_fecha(hasta)],
                                ['Servicio', 'Categoría', 'Suscripciones', 'Cupos', 'Ingresos (USD)'], filas)
        return Response(contenido, mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename=' + nombre + '.pdf'})

    abort(404)


def generar_pdf(titulo, lineas, encabezados, filas):
    """Arma un PDF con reportlab: título, datos de cabecera y una tabla."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    memoria = io.BytesIO()
    documento = SimpleDocTemplate(memoria, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                  topMargin=1.8 * cm, bottomMargin=1.8 * cm, title=titulo,
                                  author='JuansecCTI')
    estilos = getSampleStyleSheet()
    partes = [Paragraph('<b>JuansecCTI</b> - Servicios de ciberinteligencia', estilos['Normal']),
              Spacer(1, 6), Paragraph(titulo, estilos['Title'])]
    partes += [Paragraph(texto, estilos['Normal']) for texto in lineas]
    partes.append(Spacer(1, 12))
    tabla = Table([encabezados] + filas, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b1f3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f1f5f9')]),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
    ]))
    partes.append(tabla)
    partes.append(Spacer(1, 16))
    partes.append(Paragraph('Generado el ' + datetime.now().strftime('%d/%m/%Y %H:%M') +
                            ' desde el sistema JuansecCTI.', estilos['Italic']))
    documento.build(partes)
    return memoria.getvalue()


# ---------------- CATÁLOGOS (tablas padre: categorías, sectores, tipos de fuente) ----------------
#
# Las tres tablas tienen la misma estructura (nombre único y descripción), así
# que comparten rutas, formulario y plantillas. Cada entrada indica su tabla,
# su clave primaria y las tablas hijas que la referencian por clave foránea.

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


@app.route('/catalogos')
@app.route('/catalogos/<clave>')
@login_required
def ver_catalogos(clave='categorias'):
    cat = catalogo_pedido(clave)
    q = texto_buscado()
    usos = ' + '.join('(SELECT COUNT(*) FROM ' + hija + ' h WHERE h.' + columna + ' = c.' + cat['id'] + ')'
                      for hija, columna in cat['usos'])
    sql = ('SELECT c.' + cat['id'] + ' AS id, c.nombre, c.descripcion, ' + usos + ' AS usos '
           'FROM ' + cat['tabla'] + ' c ')
    params = ()
    if q:
        sql += 'WHERE LOWER(c.nombre) LIKE LOWER(%s) '
        params = ('%' + q + '%',)
    registros = consultar(sql + 'ORDER BY c.nombre', params)
    return render_template('catalogos.html', titulo='Catálogos', catalogos=CATALOGOS, clave=clave,
                           cat=cat, registros=registros, q=q)


@app.route('/catalogos/<clave>/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_catalogo(clave):
    cat = catalogo_pedido(clave)
    form = CatalogoForm()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        if nombre_repetido(cat, nombre):
            form.nombre.errors.append('Ya existe un registro con ese nombre')
        else:
            insertar('INSERT INTO ' + cat['tabla'] + ' (nombre, descripcion) VALUES (%s, %s)',
                     (nombre, form.descripcion.data.strip()))
            registrar('CREAR', 'Catálogos', cat['singular'].capitalize() + ' ' + nombre)
            flash('Registro "' + nombre + '" agregado al catálogo.', 'success')
            return redirect(url_for('ver_catalogos', clave=clave))
    return render_template('formulario_catalogo.html', titulo='Catálogos', form=form, cat=cat,
                           clave=clave, registro=None)


@app.route('/catalogos/<clave>/editar/<int:id_registro>', methods=['GET', 'POST'])
@login_required
def editar_catalogo(clave, id_registro):
    cat = catalogo_pedido(clave)
    registro = consultar('SELECT ' + cat['id'] + ' AS id, nombre, descripcion FROM ' + cat['tabla'] +
                         ' WHERE ' + cat['id'] + ' = %s', (id_registro,), uno=True)
    if registro is None:
        abort(404)
    form = CatalogoForm(data=registro)
    form.enviar.label.text = 'Actualizar'
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        if nombre_repetido(cat, nombre, id_registro):
            form.nombre.errors.append('Ya existe un registro con ese nombre')
        else:
            ejecutar('UPDATE ' + cat['tabla'] + ' SET nombre = %s, descripcion = %s WHERE ' + cat['id'] + ' = %s',
                     (nombre, form.descripcion.data.strip(), id_registro))
            registrar('EDITAR', 'Catálogos', cat['singular'].capitalize() + ' ' + nombre)
            flash('Registro "' + nombre + '" actualizado correctamente.', 'success')
            return redirect(url_for('ver_catalogos', clave=clave))
    return render_template('formulario_catalogo.html', titulo='Catálogos', form=form, cat=cat,
                           clave=clave, registro=registro)


@app.route('/catalogos/<clave>/eliminar/<int:id_registro>', methods=['POST'])
@login_required
def eliminar_catalogo(clave, id_registro):
    cat = catalogo_pedido(clave)
    usados = usos_catalogo(cat, id_registro)
    if usados:
        flash('No se puede eliminar: lo usan ' + str(usados) + ' registro(s) relacionados. '
              'La clave foránea protege la integridad de los datos.', 'danger')
    elif ejecutar('DELETE FROM ' + cat['tabla'] + ' WHERE ' + cat['id'] + ' = %s', (id_registro,)):
        registrar('ELIMINAR', 'Catálogos', cat['singular'].capitalize() + ' ID ' + str(id_registro))
        flash('Registro eliminado definitivamente.', 'warning')
    else:
        flash('El registro no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_catalogos', clave=clave))


# ---------------- USUARIOS Y BITÁCORA (solo Administrador) ----------------

@app.route('/usuarios')
@login_required
@solo_admin
def ver_usuarios():
    usuarios = consultar(
        'SELECT u.id, u.usuario, r.nombre AS rol, p.nombre_completo, p.correo '
        'FROM usuarios u INNER JOIN roles r ON r.id_rol = u.id_rol '
        'LEFT JOIN perfiles_usuario p ON p.id_usuario = u.id ORDER BY u.id')
    return render_template('usuarios.html', titulo='Usuarios', usuarios=usuarios, roles=opciones_roles())


@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@solo_admin
def nuevo_usuario():
    form = UsuarioForm()
    form.id_rol.choices = opciones_roles()
    if form.validate_on_submit():
        error = datos_duplicados(form)
        if error:
            flash(error, 'danger')
        else:
            crear_usuario(form, form.id_rol.data)
            registrar('CREAR', 'Usuarios', form.usuario.data)
            flash('Usuario "' + form.usuario.data + '" creado correctamente.', 'success')
            return redirect(url_for('ver_usuarios'))
    return render_template('registro.html', titulo='Nuevo usuario', form=form, publico=False)


@app.route('/usuarios/rol/<int:id_usuario>', methods=['POST'])
@login_required
@solo_admin
def cambiar_rol(id_usuario):
    id_rol = request.form.get('id_rol', type=int)
    if id_usuario == current_user.id:
        flash('No puede cambiar su propio rol.', 'warning')
    elif id_rol and ejecutar('UPDATE usuarios SET id_rol = %s WHERE id = %s', (id_rol, id_usuario)):
        registrar('EDITAR', 'Usuarios', 'Rol del usuario ' + str(id_usuario))
        flash('Rol actualizado correctamente.', 'success')
    return redirect(url_for('ver_usuarios'))


@app.route('/usuarios/eliminar/<int:id_usuario>', methods=['POST'])
@login_required
@solo_admin
def eliminar_usuario(id_usuario):
    if id_usuario == current_user.id:
        flash('No puede eliminar la cuenta con la que inició sesión.', 'warning')
    elif ejecutar('DELETE FROM usuarios WHERE id = %s', (id_usuario,)):
        registrar('ELIMINAR', 'Usuarios', 'ID ' + str(id_usuario))
        flash('Usuario eliminado junto con su perfil.', 'warning')
    return redirect(url_for('ver_usuarios'))


@app.route('/bitacora')
@login_required
@solo_admin
def ver_bitacora():
    modulo = request.args.get('modulo', '')
    sql = 'SELECT id_bitacora, usuario, accion, modulo, detalle, fecha FROM bitacora '
    params = ()
    if modulo:
        sql += 'WHERE modulo = %s '
        params = (modulo,)
    registros, paginacion = paginar(consultar(sql + 'ORDER BY id_bitacora DESC', params), pagina_pedida())
    modulos = [f['modulo'] for f in consultar('SELECT DISTINCT modulo FROM bitacora ORDER BY modulo')]
    return render_template('bitacora.html', titulo='Bitácora', registros=registros,
                           paginacion=paginacion, modulos=modulos, modulo=modulo)


# ---------------- Páginas de error ----------------

@app.errorhandler(404)
def no_encontrado(error):
    return render_template('error.html', titulo='Página no encontrada', codigo=404,
                           mensaje='La página que busca no existe o fue movida.'), 404


@app.errorhandler(500)
def error_interno(error):
    return render_template('error.html', titulo='Error del servidor', codigo=500,
                           mensaje='Ocurrió un problema inesperado. Intente nuevamente en unos minutos.'), 500


if __name__ == '__main__':
    # En producción el servidor lo levanta gunicorn, así que este bloque solo se
    # usa en desarrollo. El modo depuración queda apagado salvo que se pida.
    puerto = int(os.environ.get('PORT', '5000'))
    depuracion = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=puerto, debug=depuracion)
