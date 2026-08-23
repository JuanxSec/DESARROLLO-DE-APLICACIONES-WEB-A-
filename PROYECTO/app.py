from flask import Flask, render_template

app = Flask(__name__)

titulo_sitio = "JuansecCTI"
mensaje_bienvenida = "Boletines y noticias de ciberinteligencia para empresas y entidades"

productos = [
    {
        "nombre": "Boletín CTI semanal",
        "categoria": "Boletín",
        "estado": "Disponible",
        "stock": 15,
        "descripcion": "Resumen semanal de amenazas, vulnerabilidades y recomendaciones de seguridad."
    },
    {
        "nombre": "Alerta de vulnerabilidad",
        "categoria": "Alerta",
        "estado": "Activo",
        "stock": 8,
        "descripcion": "Información sobre vulnerabilidades críticas que pueden afectar a empresas."
    },
    {
        "nombre": "Reporte de noticias de seguridad",
        "categoria": "Noticias",
        "estado": "Disponible",
        "stock": 0,
        "descripcion": "Noticias relevantes de ciberseguridad explicadas de forma sencilla."
    }
]

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
    total_productos = len(productos)
    return render_template("index.html", titulo="Inicio", total_productos=total_productos, titulo_sitio=titulo_sitio)

@app.route("/productos")
def ver_productos():
    return render_template("productos.html", titulo="Productos", productos=productos, titulo_sitio=titulo_sitio)

@app.route("/clientes")
def ver_clientes():
    total_clientes = len(clientes)
    return render_template("clientes.html", titulo="Clientes", clientes=clientes, total_clientes=total_clientes, titulo_sitio=titulo_sitio)

@app.route("/proveedores")
def ver_proveedores():
    return render_template("proveedores.html", titulo="Proveedores", proveedores=proveedores, titulo_sitio=titulo_sitio)

@app.route("/facturacion")
def ver_facturacion():
    total_facturas = len(facturas)
    return render_template("facturacion.html", titulo="Facturación", facturas=facturas, total_facturas=total_facturas, titulo_sitio=titulo_sitio)

if __name__ == "__main__":
    app.run(debug=True)
