-- Base de datos del proyecto JuansecCTI (SQLite, Semana 12)
-- Ejecutar: python init_db.py --reset con DB_ENGINE=sqlite

PRAGMA foreign_keys = ON;

-- 1. Ubicacion: provincias, cantones y parroquias
CREATE TABLE provincias (
    id_provincia INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE cantones (
    id_canton    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       VARCHAR(80) NOT NULL,
    id_provincia INT NOT NULL,
    CONSTRAINT fk_cantones_provincia
        FOREIGN KEY (id_provincia) REFERENCES provincias (id_provincia)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE parroquias (
    id_parroquia INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       VARCHAR(80) NOT NULL,
    id_canton    INT NOT NULL,
    CONSTRAINT fk_parroquias_canton
        FOREIGN KEY (id_canton) REFERENCES cantones (id_canton)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 2. Catalogos
CREATE TABLE sectores (
    id_sector   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      VARCHAR(60)  NOT NULL UNIQUE,
    descripcion VARCHAR(200) NOT NULL
);

CREATE TABLE tipos_proveedor (
    id_tipo     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      VARCHAR(60)  NOT NULL UNIQUE,
    descripcion VARCHAR(200) NOT NULL
);

CREATE TABLE categorias (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       VARCHAR(60)  NOT NULL UNIQUE,
    descripcion  VARCHAR(200) NOT NULL
);

-- Un solo catalogo de estados sirve a tres modulos; la columna ambito indica a
-- cual pertenece cada estado.
CREATE TABLE estados (
    id_estado INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    VARCHAR(40) NOT NULL,
    ambito    VARCHAR(20) NOT NULL,
    CONSTRAINT ck_estados_ambito CHECK (ambito IN ('producto', 'factura', 'solicitud')),
    CONSTRAINT uq_estados UNIQUE (nombre, ambito)
);

CREATE TABLE roles (
    id_rol      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      VARCHAR(40)  NOT NULL UNIQUE,
    descripcion VARCHAR(200) NOT NULL
);

-- 3. Tablas principales (activo sirve para la baja logica)
CREATE TABLE proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       VARCHAR(100) NOT NULL,
    id_tipo      INT          NOT NULL,
    aporte       VARCHAR(300) NOT NULL,
    correo       VARCHAR(120) NULL,
    telefono     VARCHAR(20)  NULL,
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en    TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_proveedores_tipo
        FOREIGN KEY (id_tipo) REFERENCES tipos_proveedor (id_tipo)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- productos = catalogo de servicios CTI. stock son los cupos disponibles:
-- cada servicio se presta a un numero limitado de organizaciones por ciclo.
CREATE TABLE productos (
    id_producto  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       VARCHAR(100)  NOT NULL,
    id_categoria INT           NOT NULL,
    id_estado    INT           NOT NULL,
    precio       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock        INT           NOT NULL DEFAULT 0,
    descripcion  VARCHAR(500)  NOT NULL,
    id_proveedor INT           NULL,
    imagen       VARCHAR(120)  NULL,
    activo       BOOLEAN       NOT NULL DEFAULT TRUE,
    creado_en    TIMESTAMP     NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_productos_stock CHECK (stock >= 0),
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

-- clientes = organizaciones suscritas.
CREATE TABLE clientes (
    id_cliente   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       VARCHAR(100) NOT NULL,
    ruc          VARCHAR(13)  NULL UNIQUE,
    id_sector    INT          NOT NULL,
    id_parroquia INT          NOT NULL,
    servicio     VARCHAR(100) NOT NULL,
    correo       VARCHAR(120) NULL,
    telefono     VARCHAR(20)  NULL,
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en    TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_clientes_sector
        FOREIGN KEY (id_sector) REFERENCES sectores (id_sector)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_clientes_parroquia
        FOREIGN KEY (id_parroquia) REFERENCES parroquias (id_parroquia)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- facturas = suscripciones contratadas.
CREATE TABLE facturas (
    id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo     VARCHAR(20)   NOT NULL UNIQUE,
    id_cliente INT           NOT NULL,
    id_estado  INT           NOT NULL,
    servicio   VARCHAR(100)  NOT NULL,
    fecha      DATE          NOT NULL DEFAULT CURRENT_DATE,
    total      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    activo     BOOLEAN       NOT NULL DEFAULT TRUE,
    creado_en  TIMESTAMP     NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_facturas_cliente
        FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_facturas_estado
        FOREIGN KEY (id_estado) REFERENCES estados (id_estado)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla intermedia de la relacion muchos a muchos entre facturas y productos.
CREATE TABLE detalle_factura (
    id_detalle      INTEGER PRIMARY KEY AUTOINCREMENT,
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

-- Boletines de ciberinteligencia que se publican en la pagina principal.
CREATE TABLE boletines (
    id_boletin   INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       VARCHAR(150) NOT NULL,
    resumen      VARCHAR(600) NOT NULL,
    nivel        VARCHAR(10)  NOT NULL,
    referencia   VARCHAR(200) NULL,
    fecha        DATE         NOT NULL DEFAULT CURRENT_DATE,
    id_categoria INT          NOT NULL,
    id_proveedor INT          NULL,
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en    TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_boletines_nivel CHECK (nivel IN ('Critico', 'Alto', 'Medio', 'Bajo')),
    CONSTRAINT fk_boletines_categoria
        FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_boletines_proveedor
        FOREIGN KEY (id_proveedor) REFERENCES proveedores (id_proveedor)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Solicitudes de informacion que llegan desde el formulario publico.
CREATE TABLE solicitudes (
    id_solicitud  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        VARCHAR(100) NOT NULL,
    organizacion  VARCHAR(120) NOT NULL,
    correo        VARCHAR(120) NOT NULL,
    telefono      VARCHAR(20)  NULL,
    id_producto   INT          NOT NULL,
    id_estado     INT          NOT NULL,
    mensaje       VARCHAR(600) NOT NULL,
    fecha         TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP,
    activo        BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_solicitudes_producto
        FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_solicitudes_estado
        FOREIGN KEY (id_estado) REFERENCES estados (id_estado)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 4. Usuarios y auditoria
CREATE TABLE usuarios (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario  VARCHAR(50)  UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    id_rol   INT          NOT NULL,
    CONSTRAINT fk_usuarios_rol
        FOREIGN KEY (id_rol) REFERENCES roles (id_rol)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Relacion uno a uno: cada usuario tiene un unico perfil con sus datos.
CREATE TABLE perfiles_usuario (
    id_perfil       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario      INT          NOT NULL UNIQUE,
    nombre_completo VARCHAR(120) NOT NULL,
    correo          VARCHAR(120) NULL,
    CONSTRAINT fk_perfil_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Pista de auditoria: quien hizo que y cuando.
CREATE TABLE bitacora (
    id_bitacora INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario  INT          NULL,
    usuario     VARCHAR(50)  NOT NULL,
    accion      VARCHAR(20)  NOT NULL,
    modulo      VARCHAR(40)  NOT NULL,
    detalle     VARCHAR(255) NOT NULL,
    fecha       TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bitacora_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios (id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Datos iniciales

INSERT INTO provincias (nombre) VALUES
    ('Pastaza'), ('Pichincha'), ('Guayas');

INSERT INTO cantones (nombre, id_provincia) VALUES
    ('Pastaza', 1), ('Mera', 1), ('Quito', 2), ('Guayaquil', 3);

INSERT INTO parroquias (nombre, id_canton) VALUES
    ('Puyo', 1), ('Tarqui', 1), ('Shell', 2),
    ('Iñaquito', 3), ('Tarqui de Guayaquil', 4);

INSERT INTO sectores (nombre, descripcion) VALUES
    ('Financiero',  'Cooperativas, bancos y entidades del sistema financiero.'),
    ('Educación',   'Universidades, institutos y unidades educativas.'),
    ('Tecnología',  'Empresas de desarrollo de software y servicios TI.'),
    ('Salud',       'Clínicas, hospitales y centros de salud.'),
    ('Público',     'Instituciones y entidades del sector público.');

INSERT INTO tipos_proveedor (nombre, descripcion) VALUES
    ('Información pública', 'Fuentes OSINT y portales abiertos de noticias.'),
    ('Investigación',       'Comunidades y laboratorios de investigación en seguridad.'),
    ('Documentación',       'Boletines oficiales y avisos de fabricantes.'),
    ('Plataforma',          'Plataformas comerciales de inteligencia de amenazas.');

INSERT INTO categorias (nombre, descripcion) VALUES
    ('Boletín',      'Boletines periódicos de ciberinteligencia.'),
    ('Alerta',       'Alertas puntuales sobre vulnerabilidades críticas.'),
    ('Noticias',     'Resúmenes de noticias de ciberseguridad.'),
    ('Informe',      'Informes técnicos y análisis de amenazas.'),
    ('Capacitación', 'Charlas y material de concienciación para el personal.'),
    ('Monitoreo',    'Vigilancia continua de la dark web, la marca y la superficie expuesta.'),
    ('Respuesta',    'Búsqueda proactiva de amenazas y apoyo ante incidentes.');

INSERT INTO estados (nombre, ambito) VALUES
    ('Disponible', 'producto'),
    ('Activo',     'producto'),
    ('Inactivo',   'producto'),
    ('Agotado',    'producto'),
    ('Emitida',    'factura'),
    ('Pendiente',  'factura'),
    ('Pagado',     'factura'),
    ('Anulada',    'factura'),
    ('Nueva',      'solicitud'),
    ('En gestión', 'solicitud'),
    ('Atendida',   'solicitud');

INSERT INTO roles (nombre, descripcion) VALUES
    ('Administrador', 'Acceso completo, incluida la gestión de usuarios y la bitácora.'),
    ('Analista',      'Registra y consulta servicios, boletines, organizaciones y suscripciones.'),
    ('Consulta',      'Solo puede revisar la información publicada.');

INSERT INTO proveedores (nombre, id_tipo, aporte, correo, telefono) VALUES
    ('Fuentes OSINT',            1, 'Recopilación de noticias, avisos y alertas abiertas de ciberseguridad.',  'contacto@osint.example',     '032885000'),
    ('Comunidades de seguridad', 2, 'Referencias sobre amenazas, actores y buenas prácticas de defensa.',      'info@comunidad.example',     '032885001'),
    ('Boletines oficiales',      3, 'Información técnica sobre vulnerabilidades y parches de fabricantes.',    'avisos@boletin.example',     '032885002'),
    ('Plataforma de amenazas',   4, 'Indicadores de compromiso y reportes de campañas activas en la región.',  'soporte@plataforma.example', '032885003');

INSERT INTO productos (nombre, id_categoria, id_estado, precio, stock, descripcion, id_proveedor, imagen) VALUES
    ('Boletín CTI semanal',                 1, 1,  45.00, 15, 'Resumen semanal de amenazas, vulnerabilidades y recomendaciones accionables para el equipo de TI.', 1, 'servicio-boletin.jpg'),
    ('Alertas de vulnerabilidades críticas', 2, 2,  30.00,  8, 'Aviso temprano cuando un fallo crítico afecta a la tecnología que usa la organización, con pasos de mitigación.', 3, 'servicio-alerta.jpg'),
    ('Reporte de noticias de seguridad',    3, 4,  20.00,  0, 'Noticias relevantes de ciberseguridad explicadas en lenguaje sencillo para la gerencia.', 2, 'servicio-noticias.jpg'),
    ('Informe mensual de amenazas',         4, 1,  90.00,  5, 'Análisis mensual de campañas, actores y técnicas observadas en Ecuador y la región.', 4, 'servicio-informe.jpg'),
    ('Taller de concienciación',            5, 2, 120.00,  3, 'Sesión práctica para que el personal reconozca el phishing y la ingeniería social.', 2, 'servicio-capacitacion.jpg'),
    ('Monitoreo de la dark web',            6, 1, 150.00,  6, 'Vigilancia de foros, mercados y filtraciones donde aparezcan credenciales o datos de la organización.', 4, 'servicio-darkweb.jpg'),
    ('Protección de marca y dominios',      6, 1, 110.00,  4, 'Detección de dominios parecidos, perfiles falsos y sitios de phishing que suplantan a la marca.', 1, 'servicio-marca.jpg'),
    ('Superficie de ataque externa',        6, 2, 130.00,  5, 'Inventario de activos expuestos en internet y priorización de los que presentan riesgo.', 4, 'servicio-infraestructura.jpg'),
    ('Búsqueda proactiva de amenazas',      7, 1, 200.00,  2, 'Threat hunting guiado por indicadores de compromiso para encontrar intrusiones que pasan desapercibidas.', 4, 'servicio-threat-hunting.jpg'),
    ('Apoyo en respuesta a incidentes',     7, 2, 250.00,  2, 'Acompañamiento técnico para contener, analizar y documentar un incidente de seguridad.', 2, 'servicio-incidentes.jpg');

INSERT INTO clientes (nombre, ruc, id_sector, id_parroquia, servicio, correo, telefono) VALUES
    ('Cooperativa Amazonía Segura',   '1690012345001', 1, 1, 'Boletín CTI semanal',            'sistemas@coopamazonia.example', '032880010'),
    ('Instituto Tecnológico del Puyo', '1690023456001', 2, 2, 'Reporte de noticias de seguridad', 'ti@itpuyo.example',            '032880011'),
    ('Software Andino',               '1790034567001', 3, 4, 'Alertas de vulnerabilidades críticas', 'seguridad@andino.example',  '022880012'),
    ('Clínica Shell Salud',           '1690045678001', 4, 3, 'Informe mensual de amenazas',    'soporte@clinicashell.example', '032880013');

INSERT INTO facturas (codigo, id_cliente, id_estado, servicio, fecha, total) VALUES
    ('FAC-001', 1, 7, 'Boletín CTI semanal',                  '2026-09-01',  90.00),
    ('FAC-002', 2, 6, 'Reporte de noticias de seguridad',     '2026-09-05',  20.00),
    ('FAC-003', 3, 5, 'Alertas de vulnerabilidades críticas', '2026-09-10',  60.00),
    ('FAC-004', 4, 6, 'Informe mensual de amenazas',          '2026-09-15', 240.00);

INSERT INTO detalle_factura (id_factura, id_producto, cantidad, precio_unitario) VALUES
    (1, 1, 2,  45.00),
    (2, 3, 1,  20.00),
    (3, 2, 2,  30.00),
    (4, 4, 1,  90.00),
    (4, 6, 1, 150.00);

INSERT INTO boletines (titulo, resumen, nivel, referencia, fecha, id_categoria, id_proveedor) VALUES
    ('Phishing que suplanta a entidades financieras del país',
     'Se observan correos y mensajes SMS que imitan a cooperativas y bancos para robar credenciales de banca en línea. Recomendación: activar doble factor, revisar el dominio del remitente y reportar los enlaces sospechosos.',
     'Alto', 'Campaña observada en Ecuador', '2026-09-28', 1, 1),
    ('Vulnerabilidad crítica en VPN SSL de uso empresarial',
     'Los fabricantes de soluciones VPN publicaron parches para fallos que permiten ejecutar código sin autenticación. Se recomienda actualizar de inmediato y revisar los registros de acceso remoto.',
     'Critico', 'Avisos de seguridad de fabricantes', '2026-09-24', 2, 3),
    ('Credenciales corporativas a la venta en foros clandestinos',
     'Los ladrones de información (infostealers) siguen alimentando mercados de la dark web con accesos a correo y VPN. Se aconseja forzar el cambio de contraseñas expuestas y monitorear inicios de sesión inusuales.',
     'Alto', 'Monitoreo de la dark web', '2026-09-19', 6, 4),
    ('Ransomware dirigido a instituciones educativas',
     'Grupos de ransomware aprovechan cuentas sin doble factor y servidores expuestos durante los periodos de matrícula. Mantener copias de seguridad fuera de línea y segmentar la red administrativa.',
     'Medio', 'Informe mensual de amenazas', '2026-09-12', 4, 2),
    ('Buenas prácticas de contraseñas para el personal',
     'Recordatorio para la concienciación interna: frases de paso largas, gestor de contraseñas y doble factor en todas las cuentas críticas.',
     'Bajo', 'Material de capacitación', '2026-09-05', 5, 2);

INSERT INTO solicitudes (nombre, organizacion, correo, telefono, id_producto, id_estado, mensaje) VALUES
    ('María Paredes', 'Cooperativa Río Pastaza', 'mparedes@riopastaza.example', '0991234567', 6, 9,
     'Queremos saber si nuestras credenciales aparecen en filtraciones recientes y el costo del monitoreo mensual.'),
    ('Luis Andrade', 'Municipio de Mera', 'landrade@mera.example', '0987654321', 5, 10,
     'Solicitamos un taller de concienciación para 30 funcionarios del área administrativa.');

-- Los usuarios se crean desde /registro con la contrasena en hash.
