from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from forms.producto_form import ProductoForm
from forms.cliente_form import ClienteForm
from forms.proveedor_form import ProveedorForm
from forms.facturacion_form import FacturacionForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_segura_2026'

titulo_sitio = "JuanzecCTI"
mensaje_bienvenida = "Boletines y noticias de ciberinteligencia para empresas y entidades"

DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'ferreteria.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'data')):
        os.makedirs(os.path.join(os.path.dirname(__file__), 'data'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        estado TEXT NOT NULL,
        stock INTEGER NOT NULL,
        descripcion TEXT NOT NULL
    )''')

    conn.commit()
    conn.close()

clientes = [
    {
        "nombre": "Empresa demostrativa A",
        "sector": "Financiero",
        "servicio": "Boletines CTI"
    },
    {
        "nombre": "Entidad demostrativa B",
        "sector": "Educación",
        "servicio": "Noticias de seguridad"
    },
    {
        "nombre": "Organización demostrativa C",
        "sector": "Tecnología",
        "servicio": "Alertas de vulnerabilidad"
    }
]

proveedores = [
    {
        "nombre": "Fuentes OSINT",
        "tipo": "Información pública",
        "aporte": "Apoyo para recopilar noticias y alertas de ciberseguridad."
    },
    {
        "nombre": "Comunidades de seguridad",
        "tipo": "Investigación",
        "aporte": "Referencias sobre amenazas y buenas prácticas."
    },
    {
        "nombre": "Boletines oficiales",
        "tipo": "Documentación",
        "aporte": "Información técnica sobre vulnerabilidades y actualizaciones."
    }
]

facturas = [
    {
        "codigo": "FAC-001",
        "cliente": "Empresa demostrativa A",
        "servicio": "Boletín CTI semanal",
        "estado": "Pagado"
    },
    {
        "codigo": "FAC-002",
        "cliente": "Entidad demostrativa B",
        "servicio": "Noticias de seguridad",
        "estado": "Pendiente"
    },
    {
        "codigo": "FAC-003",
        "cliente": "Organización demostrativa C",
        "servicio": "Alerta de vulnerabilidad",
        "estado": "Emitida"
    }
]

@app.route("/")
def inicio():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM productos')
    total_productos = cursor.fetchone()['total']
    conn.close()
    return render_template("index.html", titulo="Inicio", total_productos=total_productos, titulo_sitio=titulo_sitio)

@app.route("/productos", methods=['GET', 'POST'])
def ver_productos():
    form = ProductoForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO productos (nombre, categoria, estado, stock, descripcion) VALUES (?, ?, ?, ?, ?)',
            (form.nombre.data, form.categoria.data, form.estado.data, form.stock.data, form.descripcion.data)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('ver_productos'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    conn.close()

    return render_template("productos.html", titulo="Productos", productos=productos, form=form, titulo_sitio=titulo_sitio)

@app.route("/clientes", methods=['GET', 'POST'])
def ver_clientes():
    form = ClienteForm()
    if form.validate_on_submit():
        clientes.append({
            "nombre": form.nombre.data,
            "sector": form.sector.data,
            "servicio": form.servicio.data
        })
        return redirect(url_for('ver_clientes'))

    total_clientes = len(clientes)
    return render_template("clientes.html", titulo="Clientes", clientes=clientes, total_clientes=total_clientes, form=form, titulo_sitio=titulo_sitio)

@app.route("/proveedores", methods=['GET', 'POST'])
def ver_proveedores():
    form = ProveedorForm()
    if form.validate_on_submit():
        proveedores.append({
            "nombre": form.nombre.data,
            "tipo": form.tipo.data,
            "aporte": form.aporte.data
        })
        return redirect(url_for('ver_proveedores'))

    return render_template("proveedores.html", titulo="Proveedores", proveedores=proveedores, form=form, titulo_sitio=titulo_sitio)

@app.route("/facturacion", methods=['GET', 'POST'])
def ver_facturacion():
    form = FacturacionForm()
    if form.validate_on_submit():
        facturas.append({
            "codigo": form.codigo.data,
            "cliente": form.cliente.data,
            "servicio": form.servicio.data,
            "estado": form.estado.data
        })
        return redirect(url_for('ver_facturacion'))

    total_facturas = len(facturas)
    return render_template("facturacion.html", titulo="Facturación", facturas=facturas, total_facturas=total_facturas, form=form, titulo_sitio=titulo_sitio)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
