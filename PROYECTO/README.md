# JuansecCTI - Proyecto Integrador

**Asignatura:** Desarrollo de Aplicaciones Web (A) - UEA-L-UFPTI-004-A
**Estudiante:** Juan Pablo Ramírez Benítez
**Docente:** Ing. Walter Rodrigo Nuñez Zamora
**Universidad Estatal Amazónica - Período 2026**

JuansecCTI es una aplicación web para la gestión de **servicios de ciberinteligencia
(CTI)**: boletines, alertas de vulnerabilidad, noticias de seguridad, informes de
amenazas y capacitaciones. La parte pública presenta la información del proyecto y la
parte administrativa, protegida con inicio de sesión, permite gestionar los servicios,
los clientes, los proveedores de información y la facturación.

## Enlaces de la entrega

- Repositorio: <https://github.com/JuanxSec/DESARROLLO-DE-APLICACIONES-WEB-A-/tree/main/PROYECTO>
- Aplicación en producción (Render): <https://desarrollo-de-aplicaciones-web-a.onrender.com>
- GitHub Pages (frontend estático): <https://juanxsec.github.io/DESARROLLO-DE-APLICACIONES-WEB-A-/PROYECTO/index.html>

GitHub Pages publica únicamente la página informativa `index.html` de la raíz, que es
contenido estático. La aplicación completa, con el backend Flask, la base de datos MySQL
y el sistema de login, está desplegada en Render y también puede ejecutarse en local.

## Estructura del proyecto

```
PROYECTO/
├── app.py                      Rutas, lógica y consultas SQL
├── models.py                   Clase Usuario para Flask-Login
├── init_db.py                  Carga el esquema en la base configurada
├── requirements.txt            Dependencias del proyecto
├── .python-version             Versión de Python usada en el despliegue
├── .env.example                Plantilla de variables de entorno
├── index.html                  Página informativa publicada en GitHub Pages
│
├── conexion/
│   ├── __init__.py
│   └── conexion.py             Conexión centralizada con MySQL
│
├── sql/
│   ├── esquema.sql             Modelo relacional MySQL (15 tablas)
│   └── esquema_sqlite.sql      Persistencia local SQLite (Semana 12)
│
├── data/
│   └── juanseccti.db           Base local SQLite (Semana 12)
│
├── forms/                      Formularios Flask-WTF / WTForms
│   ├── __init__.py
│   ├── producto_form.py
│   ├── cliente_form.py
│   ├── proveedor_form.py
│   ├── facturacion_form.py
│   ├── detalle_form.py
│   ├── login_form.py
│   └── usuario_form.py
│
├── templates/
│   ├── base.html               Plantilla principal (herencia Jinja2)
│   ├── index.html              Inicio del sistema
│   ├── login.html
│   ├── registro.html
│   ├── dashboard.html
│   ├── productos.html          + formulario_producto.html
│   ├── clientes.html           + formulario_cliente.html
│   ├── proveedores.html        + formulario_proveedor.html
│   ├── facturacion.html        + formulario_facturacion.html
│   ├── detalle_factura.html    Relación muchos a muchos
│   └── components/
│       ├── navbar.html
│       ├── footer.html
│       └── campos_formulario.html
│
└── static/
    ├── css/style.css
    ├── js/script.js
    └── img/ciberinteligencia.jpg
```

## Modelo relacional

La base de datos `juanseccti` tiene **15 tablas** y **14 claves foráneas**, separando
las tablas de catálogo (tablas padre) de las tablas de movimiento:

| Grupo | Tablas |
|---|---|
| Ubicación geográfica | `provincias` → `cantones` → `parroquias` |
| Catálogos | `sectores`, `tipos_proveedor`, `categorias`, `estados`, `roles` |
| Entidades | `proveedores`, `productos`, `clientes`, `facturas` |
| Relación N:N | `detalle_factura` (facturas ↔ productos) |
| Autenticación | `usuarios`, `perfiles_usuario` (relación 1:1) |

Tipos de relación implementados:

- **1:1** — `usuarios` ↔ `perfiles_usuario`
- **1:N** — `provincias` → `cantones` → `parroquias`, `categorias` → `productos`,
  `clientes` → `facturas`, entre otras
- **N:N** — `facturas` ↔ `productos` a través de `detalle_factura`

## Cómo ejecutar el proyecto

```bash
# 1. Entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Crear la base de datos MySQL
mysql --host=127.0.0.1 --user=root -p < sql/esquema.sql

# 3. Credenciales por variable de entorno (no se suben al repositorio)
set MYSQL_USER=root
set MYSQL_PASSWORD=tu_password
set SECRET_KEY=una_clave_larga

# 4. Ejecutar
python app.py
```

La aplicación queda disponible en <http://127.0.0.1:5000>. La ruta `/test_db` comprueba
la conexión y lista las tablas creadas.

El primer paso es registrar un usuario en `/registro`; la contraseña se guarda con
`generate_password_hash()` y nunca en texto plano.

## Despliegue en producción (Render)

La aplicación se publica como servicio web en Render a partir de la rama `main` de este
repositorio. Cada vez que se sube un commit, Render vuelve a construir y desplegar.

Configuración del servicio:

| Parámetro | Valor |
|---|---|
| Root Directory | `PROYECTO` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Versión de Python | la fijada en `.python-version` |

Variables de entorno que debe tener el servicio:

| Variable | Para qué sirve |
|---|---|
| `SECRET_KEY` | Firma la sesión y los tokens CSRF |
| `MYSQL_HOST` | Servidor MySQL gestionado |
| `MYSQL_PORT` | Puerto del servidor MySQL |
| `MYSQL_USER` | Usuario de la base de datos |
| `MYSQL_PASSWORD` | Contraseña de la base de datos |
| `MYSQL_DATABASE` | Nombre de la base de datos |
| `MYSQL_SSL` | `1` para exigir conexión cifrada con TLS |

La base de datos no vive dentro del servicio web: es un servidor MySQL gestionado
externo, de modo que la información persiste aunque el servicio se reinicie.

El esquema se carga una sola vez con `init_db.py`. El script existe porque
`sql/esquema.sql` está escrito para un MySQL propio: empieza con `DROP DATABASE` y
`CREATE DATABASE`, y en un servidor gestionado la base ya viene creada y el usuario no
tiene permiso para borrarla. `init_db.py` descarta esas tres sentencias y ejecuta el
resto contra la base que indican las variables de entorno.

```bash
# Copie .env.example como .env y complete los datos del servidor gestionado.
python init_db.py           # carga las 15 tablas y los datos de catálogo
python init_db.py --reset   # borra lo existente y vuelve a cargar
```

Al terminar, el script lista cada tabla con su número de registros, de modo que sirve
también como comprobación de que la carga fue correcta.

## Correspondencia con los avances de la asignatura

| Semana | Avance | Dónde se evidencia |
|---|---|---|
| 1 | Cliente-servidor, HTTP y HTTPS | Contenido teórico de la semana; el proyecto aplica el modelo cliente-servidor y se publica sobre HTTPS en Render |
| 2 | Herramientas y primera página HTML | `index.html` |
| 3 | HTML5 y etiquetas semánticas | `index.html` (`header`, `nav`, `main`, `section`, `article`, `aside`, `footer`) |
| 4 | CSS3, responsivo y Bootstrap | `static/css/style.css` (incluye media query), Bootstrap por CDN |
| 5 | JavaScript, DOM y eventos | `static/js/script.js` (`createElement`, `appendChild`, `addEventListener`, `preventDefault`) |
| 6 | Validaciones dinámicas | Validaciones en `input`, `blur` y `submit` con `is-valid` / `is-invalid` |
| 7 | Plantillas y contenido dinámico | Secciones reutilizables y renderizado desde arreglos de objetos |
| 8 | Mejora de interfaces con Bootstrap | Navbar, grid, cards, tabla, alertas, modal y spinner |
| 9 | Proyecto Flask y rutas | `app.py`, `templates/`, `static/`, `base.html` |
| 10 | Contenido dinámico con Jinja2 | Variables, `for`, `if`, filtros y `components/` |
| 11 | Formularios con Flask-WTF | Carpeta `forms/`, validadores, `validate_on_submit()`, CSRF |
| 12 | Persistencia local | `sql/esquema_sqlite.sql` y `data/juanseccti.db` |
| 13 | Base de datos relacional | `conexion/conexion.py`, `sql/esquema.sql`, CRUD completo en los cuatro módulos |
| 14 | Sistema de login | Flask-Login, `models.py`, `@login_required`, `current_user`, logout |
| 15 | CRUD completo de la aplicación | `crear`, `leer`, `actualizar` y `eliminar` en los módulos de servicios, clientes, proveedores y facturación, incluido el detalle de factura |

## Seguridad

- Todas las consultas SQL son parametrizadas; nunca se concatenan valores del formulario.
- `UPDATE` y `DELETE` siempre usan la cláusula `WHERE` con el identificador del registro.
- Las contraseñas se almacenan con hash (`generate_password_hash` / `check_password_hash`).
- Los formularios incluyen `form.hidden_tag()` y la aplicación tiene `SECRET_KEY` y `CSRFProtect`.
- Las credenciales de la base de datos se leen de variables de entorno.
