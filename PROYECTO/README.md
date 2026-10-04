# JuansecCTI - Proyecto Integrador

**Asignatura:** Desarrollo de Aplicaciones Web (A) - UEA-L-UFPTI-004-A
**Estudiante:** Juan Pablo Ramírez Benítez
**Docente:** Ing. Walter Rodrigo Nuñez Zamora
**Universidad Estatal Amazónica - Período 2026**

JuansecCTI es una empresa (ficticia, con fines académicos) que presta **servicios de
ciberinteligencia de amenazas (Cyber Threat Intelligence, CTI)** a organizaciones del
Ecuador: boletines, alertas de vulnerabilidades, monitoreo de la dark web, protección de
marca, superficie de ataque externa, búsqueda proactiva de amenazas y apoyo en incidentes.

El proyecto tiene dos caras:

- **Sitio público**: portada con quiénes somos, misión y visión, servicios con imagen y
  cupos disponibles, ciclo de inteligencia, boletines publicados, video, tecnologías del
  proyecto, contacto con
  mapa y un formulario de solicitud que se guarda en la base de datos.
- **Sistema interno** (con inicio de sesión): panel de control con indicadores y gráfico,
  CRUD de servicios, fuentes de inteligencia, boletines, organizaciones, suscripciones con
  su detalle y control de cupos, gestión de solicitudes, reportes exportables, usuarios
  con roles y bitácora de auditoría.

## Enlaces de la entrega

- Repositorio: <https://github.com/JuanxSec/DESARROLLO-DE-APLICACIONES-WEB-A-/tree/main/PROYECTO>
- Aplicación en producción (Render): <https://desarrollo-de-aplicaciones-web-a.onrender.com>
- GitHub Pages (versión estática, semanas 2 a 8): <https://juanxsec.github.io/DESARROLLO-DE-APLICACIONES-WEB-A-/PROYECTO/index.html>

GitHub Pages solo sirve contenido estático, por eso publica `index.html` (la versión de
las semanas 2 a 8, con su HTML, CSS y JavaScript). La aplicación completa con Flask, base
de datos y login está desplegada en Render y también se ejecuta en local.

## Funcionalidades

| Módulo | Qué permite |
|---|---|
| Sitio público | Portada, catálogo de servicios con filtro por categoría y búsqueda, boletines publicados, términos y privacidad, formulario de solicitud |
| Autenticación | Registro con contraseña segura, login con usuario o correo, "mantener sesión", logout, roles Administrador / Analista / Consulta |
| Panel de control | Indicadores en tiempo real, ingresos por mes (Chart.js), servicios más contratados, avisos de servicios sin cupos, solicitudes recientes |
| Servicios CTI | CRUD con imagen, categoría, fuente, precio y **cupos disponibles** (stock) |
| Fuentes | CRUD de las fuentes de inteligencia (proveedores) |
| Catálogos | CRUD de las tablas padre (categorías, sectores y tipos de fuente) con protección de claves foráneas |
| Boletines | CRUD; los activos se publican automáticamente en el sitio público |
| Organizaciones | CRUD con validación de RUC ecuatoriano, teléfono y nombre solo con letras |
| Suscripciones | Cabecera + detalle (relación N:N), descuento y devolución de cupos, comprobante imprimible y PDF |
| Solicitudes | Las enviadas desde el sitio público se gestionan por estado (Nueva, En gestión, Atendida) |
| Reportes | Por servicio, organización y mes, con filtro de fechas y exportación a CSV, JSON y PDF |
| Usuarios y bitácora | Solo Administrador: alta de usuarios, cambio de rol, eliminación y registro de cada operación |

Todos los listados tienen búsqueda, paginación, filtro de activos / dados de baja /
todos, **baja lógica**, reactivación y eliminación definitiva con confirmación en modal.

## Estructura del proyecto

```
PROYECTO/
├── app.py                      Punto de entrada: registra las rutas y migra la base al arrancar
├── extensiones.py              Creación de la app, configuración, CSRF y Flask-Login
├── init_db.py                  Carga el esquema en la base configurada
│
├── rutas/                      Vistas, un módulo por sección
│   ├── comun.py                Paginación, filtros de vista, roles y filtros de Jinja2
│   ├── publico.py              Portada, catálogo, boletines, solicitud y términos
│   ├── autenticacion.py        Registro, login y logout (Flask-Login)
│   ├── panel.py                Panel de control, prueba de conexión y páginas de error
│   ├── servicios.py, fuentes.py, boletines.py, organizaciones.py,
│   │   suscripciones.py, solicitudes.py, catalogos.py      CRUD de cada módulo
│   ├── reportes.py             Reportes y exportación a CSV, JSON y PDF
│   └── usuarios.py             Usuarios, roles y bitácora (Administrador)
│
├── modelos/                    Acceso a datos con SQL parametrizado, uno por entidad
│   ├── base.py                 consultar(), ejecutar(), insertar() y baja lógica
│   ├── usuario.py              Clase Usuario (Flask-Login) y consultas de usuarios
│   ├── servicio.py, fuente.py, boletin.py, organizacion.py,
│   │   suscripcion.py, solicitud.py, catalogo.py, reporte.py
│   ├── opciones.py             Catálogos para los SelectField de los formularios
│   ├── bitacora.py             Registro de auditoría
│   └── migracion.py            Actualización automática de la base desplegada
│
├── index.html                  Versión estática publicada en GitHub Pages
├── requirements.txt            Dependencias con versión fija
├── .python-version             Versión de Python del despliegue
├── .env.example                Plantilla de variables de entorno
│
├── conexion/conexion.py        Conexión única para MySQL, PostgreSQL y SQLite
├── sql/
│   ├── esquema.sql             Modelo relacional MySQL (18 tablas + datos)
│   ├── esquema_postgres.sql    El mismo modelo para PostgreSQL (Render)
│   └── esquema_sqlite.sql      El mismo modelo para SQLite (Semana 12)
├── data/juanseccti.db          Base local SQLite
├── forms/                      Formularios Flask-WTF y validadores propios
├── pruebas/prueba_sistema.py   Pruebas del sistema (Semana 16)
│
├── templates/
│   ├── base.html               Plantilla principal: modos público, acceso y panel
│   ├── components/             navbar, footer, sidebar y macros de formularios
│   ├── index.html, servicios.html, boletines_publicos.html, solicitar.html,
│   │   terminos.html, error.html                    Sitio público
│   ├── login.html, registro.html                     Acceso
│   └── dashboard.html, productos.html, clientes.html, proveedores.html,
│       facturacion.html, detalle_factura.html, comprobante.html,
│       boletines.html, solicitudes.html, reportes.html, usuarios.html,
│       bitacora.html y sus formulario_*.html         Sistema interno
│
└── static/
    ├── css/style.css           Estilos propios (variables, grid, flex, media queries, impresión)
    ├── js/script.js            DOM, eventos, validaciones y componentes
    └── img/                    Logo propio (SVG) y fotografías
```

## Modelo relacional

La base de datos `juanseccti` tiene **18 tablas**:

| Grupo | Tablas |
|---|---|
| Ubicación geográfica | `provincias` → `cantones` → `parroquias` |
| Catálogos | `sectores`, `tipos_proveedor`, `categorias`, `estados`, `roles` |
| Negocio | `proveedores`, `productos`, `clientes`, `facturas`, `boletines`, `solicitudes` |
| Relación N:N | `detalle_factura` (facturas ↔ productos) |
| Usuarios y auditoría | `usuarios`, `perfiles_usuario` (relación 1:1), `bitacora` |

- **1:1**: `usuarios` ↔ `perfiles_usuario`
- **1:N**: `provincias` → `cantones` → `parroquias`, `categorias` → `productos`,
  `clientes` → `facturas`, `proveedores` → `boletines`, `productos` → `solicitudes`, entre otras
- **N:N**: `facturas` ↔ `productos` a través de `detalle_factura`

Restricciones destacadas: `CHECK (stock >= 0)`, `CHECK` del nivel de riesgo del boletín,
RUC `UNIQUE`, claves foráneas con `ON UPDATE CASCADE` y columna `activo` para la baja lógica.

## Cómo ejecutar el proyecto en local

```bash
# 1. Entorno virtual y dependencias
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Configuración: copie .env.example como .env y complete los datos
#    (DB_ENGINE=mysql para MySQL o DB_ENGINE=sqlite para usar data/juanseccti.db)

# 3. Crear la base de datos (MySQL)
mysql --host=127.0.0.1 --user=root -p < sql/esquema.sql
#    o bien, con cualquier motor:
python init_db.py

# 4. Ejecutar
python app.py
```

La aplicación queda disponible en <http://127.0.0.1:5000>. La ruta `/test_db` comprueba
la conexión y lista las tablas. La **primera cuenta** que se registre en `/registro`
queda como Administrador; las siguientes nacen como Analista y el administrador puede
cambiarles el rol desde **Usuarios**.

## Despliegue en producción (Render)

El servicio web se construye desde la rama `main` en cada commit.

| Parámetro | Valor |
|---|---|
| Root Directory | `PROYECTO` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT` |

| Variable | Para qué sirve |
|---|---|
| `SECRET_KEY` | Firma la sesión y los tokens CSRF |
| `DB_ENGINE` | `postgres` en Render |
| `DATABASE_URL` | Cadena de conexión que entrega la base PostgreSQL de Render |
| `AUTO_INIT_DB` | `1` para cargar el esquema si la base está vacía |

Además, al arrancar, `migrar_base()` actualiza de forma idempotente una base creada con
una versión anterior del proyecto (columnas nuevas, tablas `boletines`, `solicitudes` y
`bitacora`, nuevas categorías y estados), sin borrar los datos existentes.

### Tres motores, un mismo código

`DB_ENGINE` elige el motor y `conexion/conexion.py` adapta las diferencias, de modo que
las funciones `consultar()`, `ejecutar()` e `insertar()` de `modelos/base.py` no cambian:

- **MySQL**: motor de la asignatura y de desarrollo local (valor por defecto).
- **PostgreSQL**: motor del despliegue en Render; el identificador nuevo se obtiene con `lastval()`.
- **SQLite**: persistencia local en `data/juanseccti.db`; los `%s` se traducen a `?` y
  las fechas y decimales se convierten a los tipos de Python.

## Pruebas del sistema

```bash
python pruebas/prueba_sistema.py
```

`pruebas/prueba_sistema.py` recorre la aplicación de punta a punta: páginas públicas y su
estructura (h1, h2, autor, nav, article, aside, footer, video, contacto), formulario de
solicitud, protección de las diez rutas privadas, registro con contraseña segura y hash,
login con usuario y con correo, restricción por rol, lectura de todas las pantallas,
validaciones del servidor (nombre con números, RUC inválido), CREATE, UPDATE, baja
lógica, reactivación y DELETE en los seis módulos, detalle con descuento y devolución de
cupos, comprobante en PDF, reportes en CSV, JSON y PDF, integridad referencial, CRUD de
catálogos con nombres únicos y claves foráneas protegidas, usuarios,
bitácora y cierre de sesión.

La prueba es **no destructiva**: crea sus propios registros, los verifica y los borra al
terminar. Resultado de la última ejecución: **138 de 138 comprobaciones correctas** con
MySQL y **138 de 138** con SQLite.

## Correspondencia con los avances de la asignatura

| Semana | Avance | Dónde se evidencia |
|---|---|---|
| 1 | Cliente-servidor, HTTP y HTTPS | La aplicación sigue el modelo cliente-servidor y se publica sobre HTTPS en Render |
| 2 | Herramientas y primera página HTML | `index.html`: `h1` del proyecto, `h2` del propósito, `h3` con el autor y sección de herramientas de desarrollo |
| 3 | HTML5 semántico | `header`, `nav`, `main`, `section`, `article`, `aside`, `footer`, lista `ul/li`, video de YouTube |
| 4 | CSS3, responsivo y Bootstrap | `style.css` (variables, grid, flex, selectores avanzados, media queries), Bootstrap 5 por CDN, formulario de contacto |
| 5 | JavaScript, DOM y eventos | `script.js`: `createElement`, `appendChild`, `addEventListener`, `preventDefault`, registro con conteo y eliminación |
| 6 | Validaciones dinámicas | Eventos `input`, `blur` y `submit`, clases `is-valid` / `is-invalid`, alertas de éxito y error |
| 7 | Plantillas y contenido dinámico | Arreglo `boletinesCTI` recorrido con bucle y condición; secciones comentadas en `base.html` |
| 8 | Interfaces con Bootstrap | Navbar, grid, cards, tabla, alertas, modal, spinner, carrusel, dropdown y tooltips |
| 9 | Proyecto Flask y rutas | `app.py`, carpetas `rutas/`, `modelos/`, `templates/` y `static/`, un módulo de rutas por sección |
| 10 | Jinja2 | Herencia de `base.html`, bloques, `include`, macros, filtros propios, `for`, `if` |
| 11 | Flask-WTF | Carpeta `forms/`, validadores propios, `validate_on_submit()`, CSRF |
| 12 | Persistencia local | `DB_ENGINE=sqlite`, `sql/esquema_sqlite.sql`, `data/juanseccti.db` |
| 13 | Base de datos relacional | `sql/esquema.sql` con 18 tablas, consultas parametrizadas con `JOIN` |
| 14 | Login | Flask-Login, Werkzeug, `@login_required`, roles, logout |
| 15 | CRUD completo | Seis módulos con alta, consulta, edición, baja lógica y eliminación; reportes exportables |
| 16 | Pruebas y entrega | `pruebas/prueba_sistema.py` (138 comprobaciones), repositorio organizado en carpetas de rutas, modelos, plantillas y módulos, README, script SQL y despliegue en Render |

## Seguridad

- Consultas SQL parametrizadas; `UPDATE` y `DELETE` siempre con `WHERE` por identificador.
- Contraseñas con hash (`generate_password_hash` / `check_password_hash`) y política de
  contraseña segura (8 caracteres con mayúscula, minúscula, número y carácter especial).
- `CSRFProtect` en todos los formularios y `SECRET_KEY` por variable de entorno.
- Redirección segura tras el login (solo rutas internas en `next`).
- Rutas de usuarios y bitácora restringidas al rol Administrador.
- Credenciales de la base de datos fuera del repositorio (`.env` en `.gitignore`).

## Créditos de imágenes

El logotipo es un SVG propio. Las fotografías provienen de [Unsplash](https://unsplash.com)
y se usan bajo la [licencia de Unsplash](https://unsplash.com/license), que permite su uso
libre sin atribución obligatoria. El video embebido pertenece a su autor en YouTube.
