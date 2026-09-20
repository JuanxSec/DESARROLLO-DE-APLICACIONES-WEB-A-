-- ============================================================================
-- Persistencia local con SQLite - Avance 12/16 (Semana 12)
--
-- Este script documenta la base de datos local que se utilizo antes de migrar
-- el proyecto a MySQL en la Semana 13. Se conserva dentro del repositorio como
-- evidencia del avance de la Unidad 3 y permite volver a generar el archivo
-- data/juanseccti.db en cualquier equipo:
--
--     sqlite3 data/juanseccti.db < sql/esquema_sqlite.sql
--
-- o bien, desde Python:
--
--     import sqlite3
--     conn = sqlite3.connect('data/juanseccti.db')
--     conn.executescript(open('sql/esquema_sqlite.sql', encoding='utf-8').read())
--     conn.commit()
--     conn.close()
--
-- El flujo que se implemento en la Semana 12 fue:
--     Formulario -> validacion Flask-WTF -> INSERT -> SELECT -> tabla Jinja2
-- utilizando siempre consultas parametrizadas con el marcador ? de sqlite3.
-- ============================================================================

CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    tipo         TEXT NOT NULL,
    aporte       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT    NOT NULL,
    categoria    TEXT    NOT NULL,
    estado       TEXT    NOT NULL,
    stock        INTEGER NOT NULL DEFAULT 0,
    descripcion  TEXT    NOT NULL,
    id_proveedor INTEGER,
    FOREIGN KEY (id_proveedor) REFERENCES proveedores (id_proveedor)
);

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    sector     TEXT NOT NULL,
    servicio   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS facturas (
    id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo     TEXT NOT NULL UNIQUE,
    id_cliente INTEGER NOT NULL,
    servicio   TEXT NOT NULL,
    estado     TEXT NOT NULL,
    fecha      TEXT NOT NULL DEFAULT (date('now')),
    FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
);

-- Datos de ejemplo utilizados durante la Semana 12.
INSERT INTO proveedores (nombre, tipo, aporte) VALUES
    ('Fuentes OSINT', 'Informacion publica', 'Apoyo para recopilar noticias y alertas de ciberseguridad.'),
    ('Comunidades de seguridad', 'Investigacion', 'Referencias sobre amenazas y buenas practicas.'),
    ('Boletines oficiales', 'Documentacion', 'Informacion tecnica sobre vulnerabilidades y actualizaciones.');

INSERT INTO productos (nombre, categoria, estado, stock, descripcion, id_proveedor) VALUES
    ('Boletin CTI semanal', 'Boletin', 'Disponible', 15, 'Resumen semanal de amenazas, vulnerabilidades y recomendaciones de seguridad.', 1),
    ('Alerta de vulnerabilidad', 'Alerta', 'Activo', 8, 'Informacion sobre vulnerabilidades criticas que pueden afectar a empresas.', 3),
    ('Reporte de noticias de seguridad', 'Noticias', 'Disponible', 0, 'Noticias relevantes de ciberseguridad explicadas de forma sencilla.', 2);

INSERT INTO clientes (nombre, sector, servicio) VALUES
    ('Empresa demostrativa A', 'Financiero', 'Boletines CTI'),
    ('Entidad demostrativa B', 'Educacion', 'Noticias de seguridad'),
    ('Organizacion demostrativa C', 'Tecnologia', 'Alertas de vulnerabilidad');

INSERT INTO facturas (codigo, id_cliente, servicio, estado) VALUES
    ('FAC-001', 1, 'Boletin CTI semanal', 'Pagado'),
    ('FAC-002', 2, 'Noticias de seguridad', 'Pendiente'),
    ('FAC-003', 3, 'Alerta de vulnerabilidad', 'Emitida');
