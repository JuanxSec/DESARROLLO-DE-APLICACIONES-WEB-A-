-- Esquema relacional del Proyecto Integrador JuansecCTI (Semana 13)
-- Motor: MySQL. Ejecutar: mysql -u root -p < sql/esquema.sql

CREATE DATABASE IF NOT EXISTS juanseccti CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE juanseccti;

CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    tipo         VARCHAR(50)  NOT NULL,
    aporte       VARCHAR(300) NOT NULL
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto  INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    categoria    VARCHAR(50)  NOT NULL,
    estado       VARCHAR(20)  NOT NULL,
    stock        INT          NOT NULL DEFAULT 0,
    descripcion  VARCHAR(500) NOT NULL,
    id_proveedor INT          NULL,
    CONSTRAINT fk_productos_proveedor
        FOREIGN KEY (id_proveedor) REFERENCES proveedores (id_proveedor)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre     VARCHAR(100) NOT NULL,
    sector     VARCHAR(50)  NOT NULL,
    servicio   VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS facturas (
    id_factura INT AUTO_INCREMENT PRIMARY KEY,
    codigo     VARCHAR(20)  NOT NULL UNIQUE,
    id_cliente INT          NOT NULL,
    servicio   VARCHAR(100) NOT NULL,
    estado     VARCHAR(20)  NOT NULL,
    fecha      DATE         NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_facturas_cliente
        FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Datos iniciales (los mismos que se manejaban en las semanas anteriores)
INSERT INTO proveedores (nombre, tipo, aporte) VALUES
    ('Fuentes OSINT', 'Información pública', 'Apoyo para recopilar noticias y alertas de ciberseguridad.'),
    ('Comunidades de seguridad', 'Investigación', 'Referencias sobre amenazas y buenas prácticas.'),
    ('Boletines oficiales', 'Documentación', 'Información técnica sobre vulnerabilidades y actualizaciones.');

INSERT INTO productos (nombre, categoria, estado, stock, descripcion, id_proveedor) VALUES
    ('Boletín CTI semanal', 'Boletín', 'Disponible', 15, 'Resumen semanal de amenazas, vulnerabilidades y recomendaciones de seguridad.', 1),
    ('Alerta de vulnerabilidad', 'Alerta', 'Activo', 8, 'Información sobre vulnerabilidades críticas que pueden afectar a empresas.', 3),
    ('Reporte de noticias de seguridad', 'Noticias', 'Disponible', 0, 'Noticias relevantes de ciberseguridad explicadas de forma sencilla.', 2);

INSERT INTO clientes (nombre, sector, servicio) VALUES
    ('Empresa demostrativa A', 'Financiero', 'Boletines CTI'),
    ('Entidad demostrativa B', 'Educación', 'Noticias de seguridad'),
    ('Organización demostrativa C', 'Tecnología', 'Alertas de vulnerabilidad');

INSERT INTO facturas (codigo, id_cliente, servicio, estado) VALUES
    ('FAC-001', 1, 'Boletín CTI semanal', 'Pagado'),
    ('FAC-002', 2, 'Noticias de seguridad', 'Pendiente'),
    ('FAC-003', 3, 'Alerta de vulnerabilidad', 'Emitida');
