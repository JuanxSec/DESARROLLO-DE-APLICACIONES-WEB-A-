"""Migración automática e idempotente de bases creadas con versiones anteriores del esquema."""

import os
from datetime import date

from conexion.conexion import motor
from modelos.base import consultar, contar, ejecutar, id_por_nombre


# Agrega a una base antigua las columnas y tablas nuevas sin tocar los datos.
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
        if not id_por_nombre('categorias', 'id_categoria', nombre):
            ejecutar('INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)', (nombre, descripcion))

    id_disponible = id_por_nombre('estados', 'id_estado', 'Disponible', " AND ambito = 'producto'")
    id_fuente = consultar('SELECT MIN(id_proveedor) AS id FROM proveedores', uno=True)['id']
    for nombre, categoria, precio, cupos, descripcion, imagen in SERVICIOS_BASE:
        fila = consultar('SELECT id_producto, imagen FROM productos WHERE nombre = %s', (nombre,), uno=True)
        if fila is None:
            id_categoria = id_por_nombre('categorias', 'id_categoria', categoria)
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
        id_categoria = id_por_nombre('categorias', 'id_categoria', categoria) or 1
        ejecutar('INSERT INTO boletines (titulo, resumen, nivel, referencia, fecha, id_categoria, id_proveedor) '
                 'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                 (titulo, resumen, nivel, referencia, fecha, id_categoria, id_fuente))
