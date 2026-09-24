"""Proyecto Integrador JuansecCTI - Desarrollo de Aplicaciones Web.

Aplicación Flask que integra los avances de las semanas 9 a 14:
  * Semana 9  : proyecto Flask, carpetas templates/static y rutas por módulo.
  * Semana 10 : contenido dinámico con Jinja2 (variables, for, if, filtros)
                y componentes reutilizables.
  * Semana 11 : formularios con Flask-WTF / WTForms, validaciones y CSRF.
  * Semana 12 : persistencia local (el esquema SQLite queda documentado en
                sql/esquema_sqlite.sql y la base local en data/).
  * Semana 13 : base de datos relacional MySQL con SELECT, INSERT, UPDATE y
                DELETE parametrizados sobre los cuatro módulos.
  * Semana 14 : login funcional con Flask-Login y Werkzeug.
"""

import os
from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_wtf.csrf import CSRFProtect
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from conexion.conexion import get_db_connection
from models import Usuario
from forms.producto_form import ProductoForm
from forms.cliente_form import ClienteForm
from forms.proveedor_form import ProveedorForm
from forms.facturacion_form import FacturacionForm
from forms.detalle_form import DetalleFacturaForm
from forms.login_form import LoginForm
from forms.usuario_form import UsuarioForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_segura_2026')
csrf = CSRFProtect(app)

# Motor de base de datos. 'mysql' es el de la asignatura y el que se usa en
# local; 'postgres' es el del despliegue en Render, que entrega la cadena de
# conexión ya armada en DATABASE_URL.
app.config['DB_ENGINE'] = os.environ.get('DB_ENGINE', 'mysql').lower()
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')

# Configuración de la base de datos MySQL (Semana 13).
# Las credenciales reales se toman de variables de entorno para no subirlas al repositorio.
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', '3306'))
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DATABASE'] = os.environ.get('MYSQL_DATABASE', 'juanseccti')
# En producción el servidor MySQL gestionado obliga a cifrar la conexión.
app.config['MYSQL_SSL'] = os.environ.get('MYSQL_SSL', '0') == '1'
app.config['MYSQL_SSL_CA'] = os.environ.get('MYSQL_SSL_CA', '')

# En el despliegue la base de datos nace vacía y el plan gratuito no da consola
# donde ejecutar init_db.py a mano, así que el esquema se carga en el primer
# arranque. El script solo actúa si todavía no hay tablas, de modo que los
# reinicios posteriores no tocan los datos. Si algo falla no se corta el
# arranque: la portada sigue en pie y /test_db permite ver qué pasó.
if os.environ.get('AUTO_INIT_DB', '0') == '1':
    try:
        import init_db
        init_db.main()
    except Exception as error:
        app.logger.error('No se pudo preparar el esquema: %s', error)

# Gestión de sesiones de usuario (Semana 14).
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Debe iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'

titulo_sitio = "JuansecCTI"
mensaje_bienvenida = "Boletines y noticias de ciberinteligencia para empresas y entidades"


# ---------------- Acceso a datos: consultas parametrizadas ----------------

def consultar(sql, params=(), uno=False):
    """Ejecuta un SELECT y cierra siempre el cursor y la conexión."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    resultado = cursor.fetchone() if uno else cursor.fetchall()
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


def recalcular_total(id_factura):
    """Actualiza el total de la factura a partir de su detalle (relación N:N)."""
    fila = consultar(
        'SELECT COALESCE(SUM(cantidad * precio_unitario), 0) AS total '
        'FROM detalle_factura WHERE id_factura = %s',
        (id_factura,), uno=True
    )
    ejecutar('UPDATE facturas SET total = %s WHERE id_factura = %s',
             (fila['total'], id_factura))


# ---------------- Catálogos: alimentan los SelectField de los formularios ----------------

def opciones(sql, clave, etiqueta, params=()):
    return [(fila[clave], fila[etiqueta]) for fila in consultar(sql, params)]


def opciones_proveedores():
    return opciones('SELECT id_proveedor, nombre FROM proveedores ORDER BY nombre',
                    'id_proveedor', 'nombre')


def opciones_clientes():
    return opciones('SELECT id_cliente, nombre FROM clientes ORDER BY nombre',
                    'id_cliente', 'nombre')


def opciones_categorias():
    return opciones('SELECT id_categoria, nombre FROM categorias ORDER BY nombre',
                    'id_categoria', 'nombre')


def opciones_estados(ambito):
    return opciones('SELECT id_estado, nombre FROM estados WHERE ambito = %s ORDER BY id_estado',
                    'id_estado', 'nombre', (ambito,))


def opciones_sectores():
    return opciones('SELECT id_sector, nombre FROM sectores ORDER BY nombre',
                    'id_sector', 'nombre')


def opciones_tipos_proveedor():
    return opciones('SELECT id_tipo, nombre FROM tipos_proveedor ORDER BY nombre',
                    'id_tipo', 'nombre')


def opciones_roles():
    return opciones('SELECT id_rol, nombre FROM roles ORDER BY id_rol',
                    'id_rol', 'nombre')


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


def opciones_productos():
    return opciones('SELECT id_producto, nombre FROM productos ORDER BY nombre',
                    'id_producto', 'nombre')


# ---------------- AUTENTICACIÓN: registro, login, sesión y logout ----------------

@login_manager.user_loader
def load_user(user_id):
    """Reconstruye el usuario autenticado a partir de su identificador."""
    data = consultar(
        'SELECT u.id, u.usuario, u.password, r.nombre AS rol, p.nombre_completo '
        'FROM usuarios u '
        'INNER JOIN roles r ON r.id_rol = u.id_rol '
        'LEFT JOIN perfiles_usuario p ON p.id_usuario = u.id '
        'WHERE u.id = %s',
        (user_id,), uno=True
    )
    if data:
        return Usuario(data['id'], data['usuario'], data['password'],
                       data['rol'], data['nombre_completo'])
    return None


@app.route("/registro", methods=['GET', 'POST'])
def registro():
    form = UsuarioForm()
    form.id_rol.choices = opciones_roles()

    if form.validate_on_submit():
        existente = consultar('SELECT id FROM usuarios WHERE usuario = %s',
                              (form.usuario.data,), uno=True)
        if existente:
            flash('El usuario "' + form.usuario.data + '" ya está registrado.', 'danger')
        else:
            # La contraseña se transforma con hash: nunca se almacena en texto plano.
            nuevo_id = insertar(
                'INSERT INTO usuarios (usuario, password, id_rol) VALUES (%s, %s, %s)',
                (form.usuario.data, generate_password_hash(form.password.data),
                 form.id_rol.data)
            )
            # Relación uno a uno: el perfil del usuario recién creado.
            ejecutar(
                'INSERT INTO perfiles_usuario (id_usuario, nombre_completo, correo) '
                'VALUES (%s, %s, %s)',
                (nuevo_id, form.nombre_completo.data, form.correo.data or None)
            )
            flash('Usuario "' + form.usuario.data + '" registrado correctamente. Ya puede iniciar sesión.', 'success')
            return redirect(url_for('login'))

    return render_template("registro.html", titulo="Registro", form=form, titulo_sitio=titulo_sitio)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        data = consultar(
            'SELECT u.id, u.usuario, u.password, r.nombre AS rol, p.nombre_completo '
            'FROM usuarios u '
            'INNER JOIN roles r ON r.id_rol = u.id_rol '
            'LEFT JOIN perfiles_usuario p ON p.id_usuario = u.id '
            'WHERE u.usuario = %s',
            (form.usuario.data,), uno=True
        )
        # La contraseña escrita nunca se compara directamente con la almacenada.
        if data and check_password_hash(data['password'], form.password.data):
            login_user(Usuario(data['id'], data['usuario'], data['password'],
                               data['rol'], data['nombre_completo']))
            flash('Bienvenido, ' + data['usuario'] + '.', 'success')
            siguiente = request.args.get('next')
            return redirect(siguiente or url_for('dashboard'))
        flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template("login.html", titulo="Iniciar sesión", form=form, titulo_sitio=titulo_sitio)


@app.route("/dashboard")
@login_required
def dashboard():
    resumen = {
        'productos': consultar('SELECT COUNT(*) AS t FROM productos', uno=True)['t'],
        'clientes': consultar('SELECT COUNT(*) AS t FROM clientes', uno=True)['t'],
        'proveedores': consultar('SELECT COUNT(*) AS t FROM proveedores', uno=True)['t'],
        'facturas': consultar('SELECT COUNT(*) AS t FROM facturas', uno=True)['t'],
    }
    # Consulta relacionada: servicios más facturados (facturas + detalle + productos).
    mas_facturados = consultar(
        'SELECT p.nombre, SUM(d.cantidad) AS unidades '
        'FROM detalle_factura d '
        'INNER JOIN productos p ON p.id_producto = d.id_producto '
        'GROUP BY p.id_producto, p.nombre '
        'ORDER BY unidades DESC LIMIT 5'
    )
    facturado = consultar('SELECT COALESCE(SUM(total), 0) AS total FROM facturas', uno=True)['total']
    return render_template("dashboard.html", titulo="Panel de control", resumen=resumen,
                           mas_facturados=mas_facturados, facturado=facturado,
                           titulo_sitio=titulo_sitio)


@app.route("/logout")
@login_required
def logout():
    nombre = current_user.usuario
    logout_user()
    flash('Sesión cerrada correctamente. Hasta pronto, ' + nombre + '.', 'info')
    return redirect(url_for('login'))


@app.route("/test_db")
@login_required
def test_db():
    # Cada motor lista sus tablas de una forma distinta: MySQL con SHOW TABLES
    # y PostgreSQL consultando el catálogo del esquema público.
    if app.config['DB_ENGINE'] == 'postgres':
        sql = ("SELECT table_name FROM information_schema.tables "
               "WHERE table_schema = 'public' ORDER BY table_name")
        nombre_base = 'PostgreSQL (Render)'
    else:
        sql = "SHOW TABLES"
        nombre_base = app.config['MYSQL_DATABASE']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    tablas = [t[0] for t in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"motor": app.config['DB_ENGINE'],
            "base_de_datos": nombre_base,
            "total_tablas": len(tablas),
            "tablas": tablas}


@app.route("/")
def inicio():
    # La portada es pública, así que no debe caerse si la base de datos aún
    # no responde: en ese caso simplemente se muestra sin el contador.
    try:
        total_productos = consultar('SELECT COUNT(*) AS total FROM productos', uno=True)['total']
    except Exception:
        total_productos = None
    return render_template("index.html", titulo="Inicio", total_productos=total_productos,
                           titulo_sitio=titulo_sitio)


# ---------------- PRODUCTOS: SELECT / INSERT / UPDATE / DELETE sobre MySQL ----------------

def cargar_opciones_producto(form):
    form.id_categoria.choices = opciones_categorias()
    form.id_estado.choices = opciones_estados('producto')
    form.id_proveedor.choices = opciones_proveedores()


def listar_productos():
    """SELECT con JOIN a proveedores, categorías y estados."""
    return consultar(
        'SELECT p.id_producto, p.nombre, p.precio, p.stock, p.descripcion, '
        '       c.nombre AS categoria, e.nombre AS estado, pr.nombre AS proveedor '
        'FROM productos p '
        'INNER JOIN categorias c ON c.id_categoria = p.id_categoria '
        'INNER JOIN estados e ON e.id_estado = p.id_estado '
        'LEFT JOIN proveedores pr ON pr.id_proveedor = p.id_proveedor '
        'ORDER BY p.id_producto'
    )


@app.route("/productos", methods=['GET', 'POST'])
@login_required
def ver_productos():
    form = ProductoForm()
    cargar_opciones_producto(form)

    if form.validate_on_submit():
        ejecutar(
            'INSERT INTO productos (nombre, id_categoria, id_estado, precio, stock, '
            '                       descripcion, id_proveedor) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (form.nombre.data, form.id_categoria.data, form.id_estado.data,
             form.precio.data, form.stock.data, form.descripcion.data,
             form.id_proveedor.data)
        )
        flash(f'Servicio "{form.nombre.data}" agregado correctamente.', 'success')
        return redirect(url_for('ver_productos'))

    return render_template("productos.html", titulo="Servicios CTI",
                           productos=listar_productos(), form=form, titulo_sitio=titulo_sitio)


@app.route("/productos/editar/<int:id_producto>", methods=['GET', 'POST'])
@login_required
def editar_producto(id_producto):
    producto = consultar('SELECT * FROM productos WHERE id_producto = %s',
                         (id_producto,), uno=True)
    if producto is None:
        abort(404)

    form = ProductoForm(data=producto)
    cargar_opciones_producto(form)
    form.enviar.label.text = 'Actualizar servicio'

    if form.validate_on_submit():
        ejecutar(
            'UPDATE productos SET nombre = %s, id_categoria = %s, id_estado = %s, '
            '       precio = %s, stock = %s, descripcion = %s, id_proveedor = %s '
            'WHERE id_producto = %s',
            (form.nombre.data, form.id_categoria.data, form.id_estado.data,
             form.precio.data, form.stock.data, form.descripcion.data,
             form.id_proveedor.data, id_producto)
        )
        flash(f'Servicio "{form.nombre.data}" actualizado correctamente.', 'success')
        return redirect(url_for('ver_productos'))

    return render_template("formulario_producto.html", titulo="Editar servicio", form=form,
                           producto=producto, titulo_sitio=titulo_sitio)


@app.route("/productos/eliminar/<int:id_producto>", methods=['POST'])
@login_required
def eliminar_producto(id_producto):
    usado = consultar('SELECT COUNT(*) AS t FROM detalle_factura WHERE id_producto = %s',
                      (id_producto,), uno=True)['t']
    if usado:
        flash('No se puede eliminar: el servicio está incluido en una factura.', 'danger')
        return redirect(url_for('ver_productos'))

    filas = ejecutar('DELETE FROM productos WHERE id_producto = %s', (id_producto,))
    if filas:
        flash('Servicio eliminado correctamente.', 'warning')
    else:
        flash('El servicio no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_productos'))


# ---------------- CLIENTES ----------------

def cargar_opciones_cliente(form):
    form.id_sector.choices = opciones_sectores()
    form.id_parroquia.choices = opciones_parroquias()


def listar_clientes():
    """SELECT con JOIN a sectores y a las tres tablas de ubicación geográfica."""
    return consultar(
        'SELECT c.id_cliente, c.nombre, c.servicio, c.correo, c.telefono, '
        '       s.nombre AS sector, pa.nombre AS parroquia, ca.nombre AS canton, '
        '       pr.nombre AS provincia '
        'FROM clientes c '
        'INNER JOIN sectores s ON s.id_sector = c.id_sector '
        'INNER JOIN parroquias pa ON pa.id_parroquia = c.id_parroquia '
        'INNER JOIN cantones ca ON ca.id_canton = pa.id_canton '
        'INNER JOIN provincias pr ON pr.id_provincia = ca.id_provincia '
        'ORDER BY c.id_cliente'
    )


@app.route("/clientes", methods=['GET', 'POST'])
@login_required
def ver_clientes():
    form = ClienteForm()
    cargar_opciones_cliente(form)

    if form.validate_on_submit():
        ejecutar(
            'INSERT INTO clientes (nombre, id_sector, id_parroquia, servicio, correo, telefono) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (form.nombre.data, form.id_sector.data, form.id_parroquia.data,
             form.servicio.data, form.correo.data or None, form.telefono.data or None)
        )
        flash(f'Cliente "{form.nombre.data}" agregado correctamente.', 'success')
        return redirect(url_for('ver_clientes'))

    clientes = listar_clientes()
    return render_template("clientes.html", titulo="Clientes", clientes=clientes,
                           total_clientes=len(clientes), form=form, titulo_sitio=titulo_sitio)


@app.route("/clientes/editar/<int:id_cliente>", methods=['GET', 'POST'])
@login_required
def editar_cliente(id_cliente):
    cliente = consultar('SELECT * FROM clientes WHERE id_cliente = %s',
                        (id_cliente,), uno=True)
    if cliente is None:
        abort(404)

    form = ClienteForm(data=cliente)
    cargar_opciones_cliente(form)
    form.enviar.label.text = 'Actualizar cliente'

    if form.validate_on_submit():
        ejecutar(
            'UPDATE clientes SET nombre = %s, id_sector = %s, id_parroquia = %s, '
            '       servicio = %s, correo = %s, telefono = %s '
            'WHERE id_cliente = %s',
            (form.nombre.data, form.id_sector.data, form.id_parroquia.data,
             form.servicio.data, form.correo.data or None, form.telefono.data or None,
             id_cliente)
        )
        flash(f'Cliente "{form.nombre.data}" actualizado correctamente.', 'success')
        return redirect(url_for('ver_clientes'))

    return render_template("formulario_cliente.html", titulo="Editar cliente", form=form,
                           cliente=cliente, titulo_sitio=titulo_sitio)


@app.route("/clientes/eliminar/<int:id_cliente>", methods=['POST'])
@login_required
def eliminar_cliente(id_cliente):
    usado = consultar('SELECT COUNT(*) AS t FROM facturas WHERE id_cliente = %s',
                      (id_cliente,), uno=True)['t']
    if usado:
        flash('No se puede eliminar: el cliente tiene facturas registradas.', 'danger')
        return redirect(url_for('ver_clientes'))

    filas = ejecutar('DELETE FROM clientes WHERE id_cliente = %s', (id_cliente,))
    if filas:
        flash('Cliente eliminado correctamente.', 'warning')
    else:
        flash('El cliente no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_clientes'))


# ---------------- PROVEEDORES ----------------

def listar_proveedores():
    """SELECT con JOIN al catálogo de tipos y conteo de servicios asociados."""
    return consultar(
        'SELECT pr.id_proveedor, pr.nombre, pr.aporte, pr.correo, pr.telefono, '
        '       t.nombre AS tipo, COUNT(p.id_producto) AS total_productos '
        'FROM proveedores pr '
        'INNER JOIN tipos_proveedor t ON t.id_tipo = pr.id_tipo '
        'LEFT JOIN productos p ON p.id_proveedor = pr.id_proveedor '
        'GROUP BY pr.id_proveedor, pr.nombre, pr.aporte, pr.correo, pr.telefono, t.nombre '
        'ORDER BY pr.id_proveedor'
    )


@app.route("/proveedores", methods=['GET', 'POST'])
@login_required
def ver_proveedores():
    form = ProveedorForm()
    form.id_tipo.choices = opciones_tipos_proveedor()

    if form.validate_on_submit():
        ejecutar(
            'INSERT INTO proveedores (nombre, id_tipo, aporte, correo, telefono) '
            'VALUES (%s, %s, %s, %s, %s)',
            (form.nombre.data, form.id_tipo.data, form.aporte.data,
             form.correo.data or None, form.telefono.data or None)
        )
        flash(f'Proveedor "{form.nombre.data}" agregado correctamente.', 'success')
        return redirect(url_for('ver_proveedores'))

    return render_template("proveedores.html", titulo="Proveedores",
                           proveedores=listar_proveedores(), form=form,
                           titulo_sitio=titulo_sitio)


@app.route("/proveedores/editar/<int:id_proveedor>", methods=['GET', 'POST'])
@login_required
def editar_proveedor(id_proveedor):
    proveedor = consultar('SELECT * FROM proveedores WHERE id_proveedor = %s',
                          (id_proveedor,), uno=True)
    if proveedor is None:
        abort(404)

    form = ProveedorForm(data=proveedor)
    form.id_tipo.choices = opciones_tipos_proveedor()
    form.enviar.label.text = 'Actualizar proveedor'

    if form.validate_on_submit():
        ejecutar(
            'UPDATE proveedores SET nombre = %s, id_tipo = %s, aporte = %s, '
            '       correo = %s, telefono = %s '
            'WHERE id_proveedor = %s',
            (form.nombre.data, form.id_tipo.data, form.aporte.data,
             form.correo.data or None, form.telefono.data or None, id_proveedor)
        )
        flash(f'Proveedor "{form.nombre.data}" actualizado correctamente.', 'success')
        return redirect(url_for('ver_proveedores'))

    return render_template("formulario_proveedor.html", titulo="Editar proveedor", form=form,
                           proveedor=proveedor, titulo_sitio=titulo_sitio)


@app.route("/proveedores/eliminar/<int:id_proveedor>", methods=['POST'])
@login_required
def eliminar_proveedor(id_proveedor):
    filas = ejecutar('DELETE FROM proveedores WHERE id_proveedor = %s', (id_proveedor,))
    if filas:
        flash('Proveedor eliminado correctamente. Los servicios quedaron sin proveedor asignado.', 'warning')
    else:
        flash('El proveedor no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_proveedores'))


# ---------------- FACTURACIÓN ----------------

def cargar_opciones_factura(form):
    form.id_cliente.choices = opciones_clientes()
    form.id_estado.choices = opciones_estados('factura')


def listar_facturas():
    """SELECT con JOIN a clientes y estados, y conteo de líneas de detalle."""
    return consultar(
        'SELECT f.id_factura, f.codigo, f.servicio, f.fecha, f.total, '
        '       c.nombre AS cliente, e.nombre AS estado, '
        '       COUNT(d.id_detalle) AS lineas '
        'FROM facturas f '
        'INNER JOIN clientes c ON c.id_cliente = f.id_cliente '
        'INNER JOIN estados e ON e.id_estado = f.id_estado '
        'LEFT JOIN detalle_factura d ON d.id_factura = f.id_factura '
        'GROUP BY f.id_factura, f.codigo, f.servicio, f.fecha, f.total, c.nombre, e.nombre '
        'ORDER BY f.id_factura'
    )


@app.route("/facturacion", methods=['GET', 'POST'])
@login_required
def ver_facturacion():
    form = FacturacionForm()
    cargar_opciones_factura(form)

    if form.validate_on_submit():
        duplicado = consultar('SELECT id_factura FROM facturas WHERE codigo = %s',
                              (form.codigo.data,), uno=True)
        if duplicado:
            flash(f'Ya existe una factura con el código {form.codigo.data}.', 'danger')
        else:
            ejecutar(
                'INSERT INTO facturas (codigo, id_cliente, id_estado, servicio, fecha) '
                'VALUES (%s, %s, %s, %s, %s)',
                (form.codigo.data, form.id_cliente.data, form.id_estado.data,
                 form.servicio.data, form.fecha.data)
            )
            flash(f'Factura {form.codigo.data} registrada correctamente.', 'success')
            return redirect(url_for('ver_facturacion'))

    facturas = listar_facturas()
    return render_template("facturacion.html", titulo="Facturación", facturas=facturas,
                           total_facturas=len(facturas), form=form, titulo_sitio=titulo_sitio)


@app.route("/facturacion/editar/<int:id_factura>", methods=['GET', 'POST'])
@login_required
def editar_factura(id_factura):
    factura = consultar('SELECT * FROM facturas WHERE id_factura = %s',
                        (id_factura,), uno=True)
    if factura is None:
        abort(404)

    form = FacturacionForm(data=factura)
    cargar_opciones_factura(form)
    form.enviar.label.text = 'Actualizar factura'

    if form.validate_on_submit():
        ejecutar(
            'UPDATE facturas SET codigo = %s, id_cliente = %s, id_estado = %s, '
            '       servicio = %s, fecha = %s '
            'WHERE id_factura = %s',
            (form.codigo.data, form.id_cliente.data, form.id_estado.data,
             form.servicio.data, form.fecha.data, id_factura)
        )
        flash(f'Factura {form.codigo.data} actualizada correctamente.', 'success')
        return redirect(url_for('ver_facturacion'))

    return render_template("formulario_facturacion.html", titulo="Editar factura", form=form,
                           factura=factura, titulo_sitio=titulo_sitio)


@app.route("/facturacion/eliminar/<int:id_factura>", methods=['POST'])
@login_required
def eliminar_factura(id_factura):
    filas = ejecutar('DELETE FROM facturas WHERE id_factura = %s', (id_factura,))
    if filas:
        flash('Factura eliminada correctamente junto con su detalle.', 'warning')
    else:
        flash('La factura no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_facturacion'))


@app.route("/facturacion/detalle/<int:id_factura>", methods=['GET', 'POST'])
@login_required
def detalle_factura(id_factura):
    """Gestiona la relación muchos a muchos entre facturas y servicios."""
    factura = consultar(
        'SELECT f.id_factura, f.codigo, f.servicio, f.fecha, f.total, '
        '       c.nombre AS cliente, e.nombre AS estado '
        'FROM facturas f '
        'INNER JOIN clientes c ON c.id_cliente = f.id_cliente '
        'INNER JOIN estados e ON e.id_estado = f.id_estado '
        'WHERE f.id_factura = %s',
        (id_factura,), uno=True
    )
    if factura is None:
        abort(404)

    form = DetalleFacturaForm()
    form.id_producto.choices = opciones_productos()

    if form.validate_on_submit():
        repetido = consultar(
            'SELECT id_detalle FROM detalle_factura WHERE id_factura = %s AND id_producto = %s',
            (id_factura, form.id_producto.data), uno=True
        )
        if repetido:
            flash('Ese servicio ya forma parte del detalle de la factura.', 'danger')
        else:
            ejecutar(
                'INSERT INTO detalle_factura (id_factura, id_producto, cantidad, precio_unitario) '
                'VALUES (%s, %s, %s, %s)',
                (id_factura, form.id_producto.data, form.cantidad.data,
                 form.precio_unitario.data)
            )
            recalcular_total(id_factura)
            flash('Servicio agregado al detalle de la factura.', 'success')
        return redirect(url_for('detalle_factura', id_factura=id_factura))

    lineas = consultar(
        'SELECT d.id_detalle, d.cantidad, d.precio_unitario, '
        '       (d.cantidad * d.precio_unitario) AS subtotal, p.nombre AS producto '
        'FROM detalle_factura d '
        'INNER JOIN productos p ON p.id_producto = d.id_producto '
        'WHERE d.id_factura = %s ORDER BY d.id_detalle',
        (id_factura,)
    )
    return render_template("detalle_factura.html", titulo="Detalle de factura",
                           factura=factura, lineas=lineas, form=form,
                           titulo_sitio=titulo_sitio)


@app.route("/facturacion/detalle/<int:id_factura>/eliminar/<int:id_detalle>", methods=['POST'])
@login_required
def eliminar_detalle(id_factura, id_detalle):
    filas = ejecutar('DELETE FROM detalle_factura WHERE id_detalle = %s AND id_factura = %s',
                     (id_detalle, id_factura))
    if filas:
        recalcular_total(id_factura)
        flash('Línea eliminada del detalle.', 'warning')
    else:
        flash('La línea no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('detalle_factura', id_factura=id_factura))


if __name__ == "__main__":
    # En producción el servidor lo levanta gunicorn, así que este bloque solo
    # se usa en desarrollo. El modo depuración queda apagado salvo que se pida
    # de forma explícita, porque expone una consola interactiva.
    puerto = int(os.environ.get('PORT', '5000'))
    depuracion = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=puerto, debug=depuracion)
