-- ============================================================================
-- Esquema relacional del Proyecto Integrador JuansecCTI
-- Asignatura: Desarrollo de Aplicaciones Web - Unidad 4 (Semanas 13 y 14)
-- Motor: MySQL 8 / 9
-- Ejecutar:  mysql --host=127.0.0.1 --user=root < sql/esquema.sql
--
-- El modelo separa las tablas de catalogo (tablas padre) de las tablas de
-- movimiento (tablas hijas) y utiliza los tres tipos de relacion revisados
-- en clase:
--   1:1  usuarios  <-> perfiles_usuario
--   1:N  provincias -> cantones -> parroquias, categorias -> productos, etc.
--   N:N  facturas  <-> productos  (a traves de detalle_factura)
-- ============================================================================

DROP DATABASE IF EXISTS juanseccti;
CREATE DATABASE juanseccti CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE juanseccti;

-- ---------------------------------------------------------------------------
-- 1. UBICACION GEOGRAFICA (provincia -> canton -> parroquia)
-- ---------------------------------------------------------------------------
CREATE TABLE provincias (
    id_provincia INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE cantones (
    id_canton    INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(80) NOT NULL,
    id_provincia INT NOT NULL,
    CONSTRAINT fk_cantones_provincia
        FOREIGN KEY (id_provincia) REFERENCES provincias (id_provincia)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE parroquias (
    id_parroquia INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(80) NOT NULL,
    id_canton    INT NOT NULL,
    CONSTRAINT fk_parroquias_canton
        FOREIGN KEY (id_canton) REFERENCES cantones (id_canton)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- 2. CATALOGOS DEL SISTEMA
-- ---------------------------------------------------------------------------
CREATE TABLE sectores (
    id_sector   INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(60)  NOT NULL UNIQUE,
    descripcion VARCHAR(200) NOT NULL
);

CREATE TABLE tipos_proveedor (
    id_tipo     INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(60)  NOT NULL UNIQUE,
    descripcion VARCHAR(200) NOT NULL
);

CREATE TABLE categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(60)  NOT NULL UNIQUE,
    descripcion  VARCHAR(200) NOT NULL
);

CREATE TABLE estados (
    id_estado INT AUTO_INCREMENT PRIMARY KEY,
    nombre    VARCHAR(40) NOT NULL,
    ambito    ENUM('producto', 'factura') NOT NULL,
    CONSTRAINT uq_estados UNIQUE (nombre, ambito)
);

CREATE TABLE roles (
    id_rol      INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(40)  NOT NULL UNIQUE,
    descripcion VARCHAR(200) NOT NULL
);

-- ---------------------------------------------------------------------------
-- 3. ENTIDADES PRINCIPALES
-- ---------------------------------------------------------------------------
CREATE TABLE proveedores (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    id_tipo      INT          NOT NULL,
    aporte       VARCHAR(300) NOT NULL,
    correo       VARCHAR(120) NULL,
    telefono     VARCHAR(20)  NULL,
    CONSTRAINT fk_proveedores_tipo
        FOREIGN KEY (id_tipo) REFERENCES tipos_proveedor (id_tipo)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE productos (
    id_producto  INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100)  NOT NULL,
    id_categoria INT           NOT NULL,
    id_estado    INT           NOT NULL,
    precio       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock        INT           NOT NULL DEFAULT 0,
    descripcion  VARCHAR(500)  NOT NULL,
    id_proveedor INT           NULL,
    CONSTRAINT fk_productos_categoria
        FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_productos_estado
        FOREIGN KEY (id_estado) REFERENCES estados (id_estado)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_productos_proveedor
        FOREIGN KEY (id_proveedor) REFERENCES proveedores (id_proveedor)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE clientes (
    id_cliente   INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    id_sector    INT          NOT NULL,
    id_parroquia INT          NOT NULL,
    servicio     VARCHAR(100) NOT NULL,
    correo       VARCHAR(120) NULL,
    telefono     VARCHAR(20)  NULL,
    CONSTRAINT fk_clientes_sector
        FOREIGN KEY (id_sector) REFERENCES sectores (id_sector)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_clientes_parroquia
        FOREIGN KEY (id_parroquia) REFERENCES parroquias (id_parroquia)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE facturas (
    id_factura INT AUTO_INCREMENT PRIMARY KEY,
    codigo     VARCHAR(20)   NOT NULL UNIQUE,
    id_cliente INT           NOT NULL,
    id_estado  INT           NOT NULL,
    servicio   VARCHAR(100)  NOT NULL,
    fecha      DATE          NOT NULL DEFAULT (CURRENT_DATE),
    total      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_facturas_cliente
        FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_facturas_estado
        FOREIGN KEY (id_estado) REFERENCES estados (id_estado)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla intermedia: resuelve la relacion muchos a muchos entre facturas y
-- productos. Una factura puede incluir varios servicios y un mismo servicio
-- puede aparecer en varias facturas.
CREATE TABLE detalle_factura (
    id_detalle      INT AUTO_INCREMENT PRIMARY KEY,
    id_factura      INT           NOT NULL,
    id_producto     INT           NOT NULL,
    cantidad        INT           NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_detalle_factura
        FOREIGN KEY (id_factura) REFERENCES facturas (id_factura)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_detalle_producto
        FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_detalle UNIQUE (id_factura, id_producto)
);

-- ---------------------------------------------------------------------------
-- 4. AUTENTICACION (Semana 14)
-- ---------------------------------------------------------------------------
CREATE TABLE usuarios (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    usuario  VARCHAR(50)  UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    id_rol   INT          NOT NULL,
    CONSTRAINT fk_usuarios_rol
        FOREIGN KEY (id_rol) REFERENCES roles (id_rol)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Relacion uno a uno: cada usuario tiene un unico perfil con sus datos.
CREATE TABLE perfiles_usuario (
    id_perfil       INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT          NOT NULL UNIQUE,
    nombre_completo VARCHAR(120) NOT NULL,
    correo          VARCHAR(120) NULL,
    CONSTRAINT fk_perfil_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================================
-- DATOS INICIALES
-- ============================================================================

INSERT INTO provincias (nombre) VALUES
    ('Pastaza'), ('Pichincha'), ('Guayas');

INSERT INTO cantones (nombre, id_provincia) VALUES
    ('Pastaza', 1), ('Mera', 1), ('Quito', 2), ('Guayaquil', 3);

INSERT INTO parroquias (nombre, id_canton) VALUES
    ('Puyo', 1), ('Tarqui', 1), ('Shell', 2),
    ('Inaquito', 3), ('Tarqui de Guayaquil', 4);

INSERT INTO sectores (nombre, descripcion) VALUES
    ('Financiero',  'Cooperativas, bancos y entidades del sistema financiero.'),
    ('Educacion',   'Universidades, institutos y unidades educativas.'),
    ('Tecnologia',  'Empresas de desarrollo de software y servicios TI.'),
    ('Salud',       'Clinicas, hospitales y centros de salud.'),
    ('Publico',     'Instituciones y entidades del sector publico.');

INSERT INTO tipos_proveedor (nombre, descripcion) VALUES
    ('Informacion publica', 'Fuentes OSINT y portales abiertos de noticias.'),
    ('Investigacion',       'Comunidades y laboratorios de investigacion en seguridad.'),
    ('Documentacion',       'Boletines oficiales y avisos de fabricantes.'),
    ('Plataforma',          'Plataformas comerciales de inteligencia de amenazas.');

INSERT INTO categorias (nombre, descripcion) VALUES
    ('Boletin',      'Boletines periodicos de ciberinteligencia.'),
    ('Alerta',       'Alertas puntuales sobre vulnerabilidades criticas.'),
    ('Noticias',     'Resumenes de noticias de ciberseguridad.'),
    ('Informe',      'Informes tecnicos y analisis de amenazas.'),
    ('Capacitacion', 'Charlas y material de concienciacion para el personal.');

INSERT INTO estados (nombre, ambito) VALUES
    ('Disponible', 'producto'),
    ('Activo',     'producto'),
    ('Inactivo',   'producto'),
    ('Agotado',    'producto'),
    ('Emitida',    'factura'),
    ('Pendiente',  'factura'),
    ('Pagado',     'factura'),
    ('Anulada',    'factura');

INSERT INTO roles (nombre, descripcion) VALUES
    ('Administrador', 'Acceso completo a los modulos de administracion.'),
    ('Analista',      'Registra y consulta boletines, alertas e informes.'),
    ('Consulta',      'Solo puede revisar la informacion publicada.');

INSERT INTO proveedores (nombre, id_tipo, aporte, correo, telefono) VALUES
    ('Fuentes OSINT',            1, 'Apoyo para recopilar noticias y alertas de ciberseguridad.',    'contacto@osint.example',     '032885000'),
    ('Comunidades de seguridad', 2, 'Referencias sobre amenazas y buenas practicas.',                'info@comunidad.example',     '032885001'),
    ('Boletines oficiales',      3, 'Informacion tecnica sobre vulnerabilidades y actualizaciones.', 'avisos@boletin.example',     '032885002'),
    ('Plataforma de amenazas',   4, 'Indicadores de compromiso y reportes de campanas activas.',     'soporte@plataforma.example', '032885003');

INSERT INTO productos (nombre, id_categoria, id_estado, precio, stock, descripcion, id_proveedor) VALUES
    ('Boletin CTI semanal',              1, 1,  45.00, 15, 'Resumen semanal de amenazas, vulnerabilidades y recomendaciones de seguridad.', 1),
    ('Alerta de vulnerabilidad',         2, 2,  30.00,  8, 'Informacion sobre vulnerabilidades criticas que pueden afectar a empresas.',    3),
    ('Reporte de noticias de seguridad', 3, 4,  20.00,  0, 'Noticias relevantes de ciberseguridad explicadas de forma sencilla.',          2),
    ('Informe mensual de amenazas',      4, 1,  90.00,  5, 'Analisis mensual de campanas, actores y tecnicas observadas en la region.',    4),
    ('Taller de concienciacion',         5, 2, 120.00,  3, 'Sesion practica de concienciacion en seguridad para el personal del cliente.', 2);

INSERT INTO clientes (nombre, id_sector, id_parroquia, servicio, correo, telefono) VALUES
    ('Empresa demostrativa A',      1, 1, 'Boletines CTI',             'contacto@empresaa.example', '032880010'),
    ('Entidad demostrativa B',      2, 2, 'Noticias de seguridad',     'info@entidadb.example',     '032880011'),
    ('Organizacion demostrativa C', 3, 4, 'Alertas de vulnerabilidad', 'soporte@orgc.example',      '022880012'),
    ('Cooperativa demostrativa D',  1, 3, 'Informe mensual',           'sistemas@coopd.example',    '032880013');

INSERT INTO facturas (codigo, id_cliente, id_estado, servicio, fecha, total) VALUES
    ('FAC-001', 1, 7, 'Boletin CTI semanal',      '2026-09-01', 90.00),
    ('FAC-002', 2, 6, 'Noticias de seguridad',    '2026-09-05', 20.00),
    ('FAC-003', 3, 5, 'Alerta de vulnerabilidad', '2026-09-10', 60.00),
    ('FAC-004', 4, 6, 'Informe mensual',          '2026-09-15', 90.00);

INSERT INTO detalle_factura (id_factura, id_producto, cantidad, precio_unitario) VALUES
    (1, 1, 2, 45.00),
    (2, 3, 1, 20.00),
    (3, 2, 2, 30.00),
    (4, 4, 1, 90.00);

-- Los usuarios se registran desde la ruta /registro de la aplicacion: la
-- contrasena se transforma con generate_password_hash() antes del INSERT, por
-- eso aqui no se insertan credenciales en texto plano.
