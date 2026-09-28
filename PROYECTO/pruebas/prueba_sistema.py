"""Pruebas del sistema - Avance 16/16 (Semana 16).

Comprueba, contra la base de datos que este configurada, que la aplicacion
funciona de punta a punta: autenticacion, las cuatro operaciones CRUD en los
cuatro modulos, la relacion muchos a muchos del detalle de factura y la
proteccion de las rutas privadas.

La prueba es NO DESTRUCTIVA: crea sus propios registros con un prefijo
reconocible, los verifica y los borra al terminar. No toca los datos que ya
existan en la base.

Uso, desde la carpeta PROYECTO:

    python pruebas/prueba_sistema.py

Lee la configuracion del archivo .env o de las variables de entorno, igual que
la aplicacion. Funciona tanto con MySQL como con PostgreSQL.
"""

import os
import sys
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

# La carga automatica del esquema no debe dispararse al importar la aplicacion.
os.environ["AUTO_INIT_DB"] = "0"

import init_db
init_db.cargar_dotenv()

import app as aplicacion
from werkzeug.security import generate_password_hash

aplicacion.app.config["WTF_CSRF_ENABLED"] = False
aplicacion.app.config["TESTING"] = True

MARCA = "__prueba_sistema__"
resultados = []
creado = {"producto": [], "cliente": [], "proveedor": [], "factura": [], "usuario": []}


def check(nombre, condicion, detalle=""):
    resultados.append((nombre, bool(condicion)))
    print(("  [OK]    " if condicion else "  [FALLA] ") + nombre + ("  " + detalle if detalle else ""))


def contar(tabla):
    with aplicacion.app.app_context():
        return aplicacion.consultar("SELECT COUNT(*) AS t FROM " + tabla, uno=True)["t"]


def uno(sql, params=()):
    with aplicacion.app.app_context():
        return aplicacion.consultar(sql, params, uno=True)


def limpiar():
    """Borra todo lo que creo esta prueba, respetando las claves foraneas."""
    with aplicacion.app.app_context():
        for id_factura in creado["factura"]:
            aplicacion.ejecutar("DELETE FROM detalle_factura WHERE id_factura = %s", (id_factura,))
            aplicacion.ejecutar("DELETE FROM facturas WHERE id_factura = %s", (id_factura,))
        for id_producto in creado["producto"]:
            aplicacion.ejecutar("DELETE FROM detalle_factura WHERE id_producto = %s", (id_producto,))
            aplicacion.ejecutar("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
        for id_cliente in creado["cliente"]:
            aplicacion.ejecutar("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
        for id_proveedor in creado["proveedor"]:
            aplicacion.ejecutar("DELETE FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
        for id_usuario in creado["usuario"]:
            aplicacion.ejecutar("DELETE FROM perfiles_usuario WHERE id_usuario = %s", (id_usuario,))
            aplicacion.ejecutar("DELETE FROM usuarios WHERE id = %s", (id_usuario,))


def main():
    print("Motor: " + aplicacion.app.config["DB_ENGINE"])
    print()

    print("--- La base responde y tiene los catalogos cargados ---")
    for tabla, minimo in [("roles", 1), ("categorias", 1), ("estados", 2),
                          ("sectores", 1), ("tipos_proveedor", 1), ("parroquias", 1)]:
        n = contar(tabla)
        check("catalogo " + tabla + " con datos", n >= minimo, str(n) + " registros")

    rol = uno("SELECT id_rol FROM roles ORDER BY id_rol LIMIT 1")["id_rol"]
    categoria = uno("SELECT id_categoria FROM categorias ORDER BY id_categoria LIMIT 1")["id_categoria"]
    sector = uno("SELECT id_sector FROM sectores ORDER BY id_sector LIMIT 1")["id_sector"]
    parroquia = uno("SELECT id_parroquia FROM parroquias ORDER BY id_parroquia LIMIT 1")["id_parroquia"]
    tipo = uno("SELECT id_tipo FROM tipos_proveedor ORDER BY id_tipo LIMIT 1")["id_tipo"]
    est_prod = uno("SELECT id_estado FROM estados WHERE ambito = %s ORDER BY id_estado LIMIT 1",
                   ("producto",))["id_estado"]
    est_fact = uno("SELECT id_estado FROM estados WHERE ambito = %s ORDER BY id_estado LIMIT 1",
                   ("factura",))["id_estado"]

    print("\n--- Autenticacion (Semana 14) ---")
    with aplicacion.app.app_context():
        uid = aplicacion.insertar(
            "INSERT INTO usuarios (usuario, password, id_rol) VALUES (%s, %s, %s)",
            (MARCA, generate_password_hash("clave-temporal-de-prueba"), rol))
        aplicacion.ejecutar(
            "INSERT INTO perfiles_usuario (id_usuario, nombre_completo, correo) VALUES (%s, %s, %s)",
            (uid, "Usuario de prueba automatica", "prueba@example.com"))
    creado["usuario"].append(uid)
    check("insertar() devuelve el id autogenerado", isinstance(uid, int) and uid > 0, "id=" + str(uid))
    check("La contrasena se almacena con hash",
          uno("SELECT password FROM usuarios WHERE id = %s", (uid,))["password"] != "clave-temporal-de-prueba")
    check("Se crea el perfil asociado (relacion 1:1)",
          uno("SELECT id_perfil FROM perfiles_usuario WHERE id_usuario = %s", (uid,)) is not None)

    anonimo = aplicacion.app.test_client()
    print("\n--- Las rutas privadas estan protegidas ---")
    for ruta in ["/dashboard", "/productos", "/clientes", "/proveedores", "/facturacion"]:
        check("sin sesion " + ruta + " redirige", anonimo.get(ruta).status_code == 302)

    c = aplicacion.app.test_client()
    with c.session_transaction() as sesion:
        sesion["_user_id"] = str(uid)
        sesion["_fresh"] = True

    print("\n--- Lectura de las pantallas privadas (Semanas 9 y 10) ---")
    for ruta in ["/dashboard", "/productos", "/clientes", "/proveedores", "/facturacion", "/test_db"]:
        r = c.get(ruta)
        check("GET " + ruta, r.status_code == 200, "-> " + str(r.status_code))

    tablas = c.get("/test_db").json
    check("La base tiene al menos 3 tablas relacionadas", tablas["total_tablas"] >= 3,
          str(tablas["total_tablas"]) + " tablas")

    print("\n--- CREATE (Semana 15) ---")
    antes = contar("proveedores")
    c.post("/proveedores", data={"nombre": MARCA + " proveedor", "id_tipo": tipo,
                                 "aporte": "Registro temporal de la prueba automatica.",
                                 "correo": "prov@example.com", "telefono": "0320000001"},
           follow_redirects=True)
    prov = uno("SELECT id_proveedor FROM proveedores WHERE nombre = %s", (MARCA + " proveedor",))
    if prov:
        creado["proveedor"].append(prov["id_proveedor"])
    check("CREATE proveedor", contar("proveedores") == antes + 1,
          str(antes) + " -> " + str(contar("proveedores")))

    antes = contar("productos")
    c.post("/productos", data={"nombre": MARCA + " servicio", "id_categoria": categoria,
                               "id_estado": est_prod, "precio": "45.00", "stock": 5,
                               "id_proveedor": prov["id_proveedor"],
                               "descripcion": "Registro temporal de la prueba automatica."},
           follow_redirects=True)
    prod = uno("SELECT id_producto FROM productos WHERE nombre = %s", (MARCA + " servicio",))
    if prod:
        creado["producto"].append(prod["id_producto"])
    check("CREATE producto", contar("productos") == antes + 1,
          str(antes) + " -> " + str(contar("productos")))

    antes = contar("clientes")
    c.post("/clientes", data={"nombre": MARCA + " cliente", "id_sector": sector,
                              "id_parroquia": parroquia, "servicio": "Boletines CTI",
                              "correo": "cli@example.com", "telefono": "0320000002"},
           follow_redirects=True)
    cli = uno("SELECT id_cliente FROM clientes WHERE nombre = %s", (MARCA + " cliente",))
    if cli:
        creado["cliente"].append(cli["id_cliente"])
    check("CREATE cliente", contar("clientes") == antes + 1,
          str(antes) + " -> " + str(contar("clientes")))

    codigo = "QA-" + date.today().strftime("%m%d") + "-" + str(uid)
    antes = contar("facturas")
    c.post("/facturacion", data={"codigo": codigo, "id_cliente": cli["id_cliente"],
                                 "servicio": "Servicio de prueba", "id_estado": est_fact,
                                 "fecha": date.today().isoformat()}, follow_redirects=True)
    fact = uno("SELECT id_factura FROM facturas WHERE codigo = %s", (codigo,))
    if fact:
        creado["factura"].append(fact["id_factura"])
    check("CREATE factura", contar("facturas") == antes + 1,
          str(antes) + " -> " + str(contar("facturas")))

    print("\n--- UPDATE (Semana 15) ---")
    c.post("/productos/editar/" + str(prod["id_producto"]),
           data={"nombre": MARCA + " servicio editado", "id_categoria": categoria,
                 "id_estado": est_prod, "precio": "99.99", "stock": 2,
                 "id_proveedor": prov["id_proveedor"],
                 "descripcion": "Descripcion modificada por la prueba."}, follow_redirects=True)
    p = uno("SELECT nombre, precio FROM productos WHERE id_producto = %s", (prod["id_producto"],))
    check("UPDATE producto", p["nombre"].endswith("editado") and str(p["precio"]) == "99.99",
          p["nombre"] + " / " + str(p["precio"]))

    c.post("/clientes/editar/" + str(cli["id_cliente"]),
           data={"nombre": MARCA + " cliente editado", "id_sector": sector,
                 "id_parroquia": parroquia, "servicio": "Informe mensual",
                 "correo": "cli2@example.com", "telefono": "0320000003"}, follow_redirects=True)
    check("UPDATE cliente",
          uno("SELECT servicio FROM clientes WHERE id_cliente = %s",
              (cli["id_cliente"],))["servicio"] == "Informe mensual")

    print("\n--- Relacion N:N: detalle de factura (Semana 13) ---")
    antes = contar("detalle_factura")
    c.post("/facturacion/detalle/" + str(fact["id_factura"]),
           data={"id_producto": prod["id_producto"], "cantidad": 2, "precio_unitario": "99.99"},
           follow_redirects=True)
    check("CREATE linea de detalle", contar("detalle_factura") == antes + 1,
          str(antes) + " -> " + str(contar("detalle_factura")))
    total = uno("SELECT total FROM facturas WHERE id_factura = %s", (fact["id_factura"],))["total"]
    check("El total de la factura se recalcula", str(total) == "199.98", "total = " + str(total))

    print("\n--- Integridad referencial ---")
    antes = contar("productos")
    c.post("/productos/eliminar/" + str(prod["id_producto"]), follow_redirects=True)
    check("No deja borrar un servicio incluido en una factura", contar("productos") == antes)

    print("\n--- DELETE (Semana 15) ---")
    det = uno("SELECT id_detalle FROM detalle_factura WHERE id_factura = %s", (fact["id_factura"],))
    antes = contar("detalle_factura")
    c.post("/facturacion/detalle/" + str(fact["id_factura"]) + "/eliminar/" + str(det["id_detalle"]),
           follow_redirects=True)
    check("DELETE linea de detalle", contar("detalle_factura") == antes - 1)

    antes = contar("productos")
    c.post("/productos/eliminar/" + str(prod["id_producto"]), follow_redirects=True)
    if contar("productos") == antes - 1:
        creado["producto"].remove(prod["id_producto"])
    check("DELETE producto", contar("productos") == antes - 1)

    antes = contar("facturas")
    c.post("/facturacion/eliminar/" + str(fact["id_factura"]), follow_redirects=True)
    if contar("facturas") == antes - 1:
        creado["factura"].remove(fact["id_factura"])
    check("DELETE factura", contar("facturas") == antes - 1)

    antes = contar("clientes")
    c.post("/clientes/eliminar/" + str(cli["id_cliente"]), follow_redirects=True)
    if contar("clientes") == antes - 1:
        creado["cliente"].remove(cli["id_cliente"])
    check("DELETE cliente", contar("clientes") == antes - 1)

    antes = contar("proveedores")
    c.post("/proveedores/eliminar/" + str(prov["id_proveedor"]), follow_redirects=True)
    if contar("proveedores") == antes - 1:
        creado["proveedor"].remove(prov["id_proveedor"])
    check("DELETE proveedor", contar("proveedores") == antes - 1)

    print("\n--- Cierre de sesion ---")
    c.get("/logout")
    check("Tras cerrar sesion el panel vuelve a estar protegido", c.get("/dashboard").status_code == 302)


if __name__ == "__main__":
    try:
        main()
    finally:
        limpiar()
        print("\nRegistros temporales eliminados.")

    ok = sum(1 for _, v in resultados if v)
    print("=" * 62)
    print("RESULTADO: " + str(ok) + " de " + str(len(resultados)) + " comprobaciones correctas")
    fallidas = [n for n, v in resultados if not v]
    if fallidas:
        print("Fallaron:")
        for f in fallidas:
            print("  - " + f)
        sys.exit(1)
    print("EL SISTEMA FUNCIONA CORRECTAMENTE")
