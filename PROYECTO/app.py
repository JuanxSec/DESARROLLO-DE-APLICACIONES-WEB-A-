import os
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_wtf.csrf import CSRFProtect
from conexion.conexion import get_db_connection
from forms.producto_form import ProductoForm
from forms.cliente_form import ClienteForm
from forms.proveedor_form import ProveedorForm
from forms.facturacion_form import FacturacionForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_segura_2026'
csrf = CSRFProtect(app)

# Configuración de la base de datos MySQL (Semana 13).
# Las credenciales reales se toman de variables de entorno para no subirlas al repositorio.
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', '3306'))
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DATABASE'] = os.environ.get('MYSQL_DATABASE', 'juanseccti')

titulo_sitio = "JuansecCTI"
mensaje_bienvenida = "Boletines y noticias de ciberinteligencia para empresas y entidades"


def consultar(sql, params=(), uno=False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    resultado = cursor.fetchone() if uno else cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


def ejecutar(sql, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas


def opciones_proveedores():
    proveedores = consultar('SELECT id_proveedor, nombre FROM proveedores ORDER BY nombre')
    return [(p['id_proveedor'], p['nombre']) for p in proveedores]


def opciones_clientes():
    clientes = consultar('SELECT id_cliente, nombre FROM clientes ORDER BY nombre')
    return [(c['id_cliente'], c['nombre']) for c in clientes]


@app.route("/test_db")
def test_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tablas = [t[0] for t in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"base_de_datos": app.config['MYSQL_DATABASE'], "tablas": tablas}


@app.route("/")
def inicio():
    total_productos = consultar('SELECT COUNT(*) AS total FROM productos', uno=True)['total']
    return render_template("index.html", titulo="Inicio", total_productos=total_productos, titulo_sitio=titulo_sitio)


# ---------------- PRODUCTOS: SELECT / INSERT / UPDATE / DELETE sobre MySQL ----------------

@app.route("/productos", methods=['GET', 'POST'])
def ver_productos():
    form = ProductoForm()
    form.id_proveedor.choices = opciones_proveedores()

    if form.validate_on_submit():
        ejecutar(
            'INSERT INTO productos (nombre, categoria, estado, stock, descripcion, id_proveedor) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (form.nombre.data, form.categoria.data, form.estado.data,
             form.stock.data, form.descripcion.data, form.id_proveedor.data)
        )
        flash(f'Producto "{form.nombre.data}" agregado correctamente.', 'success')
        return redirect(url_for('ver_productos'))

    productos = consultar(
        'SELECT p.id_producto, p.nombre, p.categoria, p.estado, p.stock, p.descripcion, '
        '       pr.nombre AS proveedor '
        'FROM productos p '
        'LEFT JOIN proveedores pr ON pr.id_proveedor = p.id_proveedor '
        'ORDER BY p.id_producto'
    )
    return render_template("productos.html", titulo="Productos", productos=productos, form=form, titulo_sitio=titulo_sitio)


@app.route("/productos/editar/<int:id_producto>", methods=['GET', 'POST'])
def editar_producto(id_producto):
    producto = consultar('SELECT * FROM productos WHERE id_producto = %s', (id_producto,), uno=True)
    if producto is None:
        abort(404)

    form = ProductoForm(data=producto)
    form.id_proveedor.choices = opciones_proveedores()
    form.enviar.label.text = 'Actualizar Producto'

    if form.validate_on_submit():
        ejecutar(
            'UPDATE productos SET nombre = %s, categoria = %s, estado = %s, stock = %s, '
            'descripcion = %s, id_proveedor = %s WHERE id_producto = %s',
            (form.nombre.data, form.categoria.data, form.estado.data, form.stock.data,
             form.descripcion.data, form.id_proveedor.data, id_producto)
        )
        flash(f'Producto "{form.nombre.data}" actualizado correctamente.', 'success')
        return redirect(url_for('ver_productos'))

    return render_template("formulario_producto.html", titulo="Editar producto", form=form,
                           producto=producto, titulo_sitio=titulo_sitio)


@app.route("/productos/eliminar/<int:id_producto>", methods=['POST'])
def eliminar_producto(id_producto):
    filas = ejecutar('DELETE FROM productos WHERE id_producto = %s', (id_producto,))
    if filas:
        flash('Producto eliminado correctamente.', 'warning')
    else:
        flash('El producto no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_productos'))


# ---------------- CLIENTES ----------------

@app.route("/clientes", methods=['GET', 'POST'])
def ver_clientes():
    form = ClienteForm()
    if form.validate_on_submit():
        ejecutar(
            'INSERT INTO clientes (nombre, sector, servicio) VALUES (%s, %s, %s)',
            (form.nombre.data, form.sector.data, form.servicio.data)
        )
        flash(f'Cliente "{form.nombre.data}" agregado correctamente.', 'success')
        return redirect(url_for('ver_clientes'))

    clientes = consultar('SELECT * FROM clientes ORDER BY id_cliente')
    return render_template("clientes.html", titulo="Clientes", clientes=clientes,
                           total_clientes=len(clientes), form=form, titulo_sitio=titulo_sitio)


# ---------------- PROVEEDORES ----------------

@app.route("/proveedores", methods=['GET', 'POST'])
def ver_proveedores():
    form = ProveedorForm()
    if form.validate_on_submit():
        ejecutar(
            'INSERT INTO proveedores (nombre, tipo, aporte) VALUES (%s, %s, %s)',
            (form.nombre.data, form.tipo.data, form.aporte.data)
        )
        flash(f'Proveedor "{form.nombre.data}" agregado correctamente.', 'success')
        return redirect(url_for('ver_proveedores'))

    proveedores = consultar(
        'SELECT pr.*, COUNT(p.id_producto) AS total_productos '
        'FROM proveedores pr '
        'LEFT JOIN productos p ON p.id_proveedor = pr.id_proveedor '
        'GROUP BY pr.id_proveedor ORDER BY pr.id_proveedor'
    )
    return render_template("proveedores.html", titulo="Proveedores", proveedores=proveedores, form=form, titulo_sitio=titulo_sitio)


# ---------------- FACTURACIÓN ----------------

@app.route("/facturacion", methods=['GET', 'POST'])
def ver_facturacion():
    form = FacturacionForm()
    form.id_cliente.choices = opciones_clientes()

    if form.validate_on_submit():
        ejecutar(
            'INSERT INTO facturas (codigo, id_cliente, servicio, estado) VALUES (%s, %s, %s, %s)',
            (form.codigo.data, form.id_cliente.data, form.servicio.data, form.estado.data)
        )
        flash(f'Factura {form.codigo.data} registrada correctamente.', 'success')
        return redirect(url_for('ver_facturacion'))

    facturas = consultar(
        'SELECT f.id_factura, f.codigo, f.servicio, f.estado, f.fecha, c.nombre AS cliente '
        'FROM facturas f '
        'INNER JOIN clientes c ON c.id_cliente = f.id_cliente '
        'ORDER BY f.id_factura'
    )
    return render_template("facturacion.html", titulo="Facturación", facturas=facturas,
                           total_facturas=len(facturas), form=form, titulo_sitio=titulo_sitio)


if __name__ == "__main__":
    app.run(debug=True)
