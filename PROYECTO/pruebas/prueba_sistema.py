"""Pruebas del sistema - Avance 16/16 (Semana 16).

Comprueba, contra la base de datos que esté configurada, que la aplicación
funciona de punta a punta: páginas públicas, registro e inicio de sesión,
protección de rutas y roles, CRUD completo con baja lógica en los seis módulos,
la relación muchos a muchos del detalle con control de cupos, reportes
exportables, comprobante en PDF y bitácora de auditoría.

La prueba es NO DESTRUCTIVA: crea sus propios registros con un prefijo
reconocible, los verifica y los borra al terminar. Los cupos de los servicios
existentes no se tocan porque se trabaja con un servicio creado por la prueba.

Uso, desde la carpeta PROYECTO:

    python pruebas/prueba_sistema.py

Lee la configuración del archivo .env o de las variables de entorno, igual que
la aplicación. Funciona con MySQL, PostgreSQL y SQLite (DB_ENGINE).
"""

import os
import sys
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

# La carga automática del esquema no debe dispararse al importar la aplicación.
os.environ["AUTO_INIT_DB"] = "0"

import init_db
init_db.cargar_dotenv()

import app as aplicacion
from werkzeug.security import generate_password_hash

aplicacion.app.config["WTF_CSRF_ENABLED"] = False
aplicacion.app.config["TESTING"] = True

# Prefijo de solo letras: los campos de nombre rechazan dígitos y guiones bajos.
MARCA = "Prueba Automatizada QA"
CLAVE = "Clave.Prueba2026"
resultados = []
creado = {"producto": [], "cliente": [], "proveedor": [], "factura": [], "usuario": [],
          "boletin": [], "solicitud": []}


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
    """Borra todo lo que creó esta prueba, respetando las claves foráneas."""
    with aplicacion.app.app_context():
        for id_solicitud in creado["solicitud"]:
            aplicacion.ejecutar("DELETE FROM solicitudes WHERE id_solicitud = %s", (id_solicitud,))
        aplicacion.ejecutar("DELETE FROM solicitudes WHERE organizacion LIKE %s", (MARCA + "%",))
        aplicacion.ejecutar("DELETE FROM sectores WHERE nombre LIKE %s", (MARCA + "%",))
        for id_boletin in creado["boletin"]:
            aplicacion.ejecutar("DELETE FROM boletines WHERE id_boletin = %s", (id_boletin,))
        for id_factura in creado["factura"]:
            aplicacion.ejecutar("DELETE FROM detalle_factura WHERE id_factura = %s", (id_factura,))
            aplicacion.ejecutar("DELETE FROM facturas WHERE id_factura = %s", (id_factura,))
        for id_producto in creado["producto"]:
            aplicacion.ejecutar("DELETE FROM solicitudes WHERE id_producto = %s", (id_producto,))
            aplicacion.ejecutar("DELETE FROM detalle_factura WHERE id_producto = %s", (id_producto,))
            aplicacion.ejecutar("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
        for id_cliente in creado["cliente"]:
            aplicacion.ejecutar("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
        for id_proveedor in creado["proveedor"]:
            aplicacion.ejecutar("DELETE FROM proveedores WHERE id_proveedor = %s", (id_proveedor,))
        usuarios = list(creado["usuario"])
        for fila in aplicacion.consultar("SELECT id FROM usuarios WHERE usuario LIKE %s", ("qa_%",)):
            if fila["id"] not in usuarios:
                usuarios.append(fila["id"])
        for id_usuario in usuarios:
            aplicacion.ejecutar("DELETE FROM perfiles_usuario WHERE id_usuario = %s", (id_usuario,))
            aplicacion.ejecutar("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        aplicacion.ejecutar("DELETE FROM bitacora WHERE usuario LIKE %s OR detalle LIKE %s",
                            ("qa_%", "%" + MARCA + "%"))


def pagina(cliente, ruta, nombre=None):
    r = cliente.get(ruta)
    check("GET " + (nombre or ruta), r.status_code == 200, "-> " + str(r.status_code))
    return r


def main():
    print("Motor: " + aplicacion.app.config["DB_ENGINE"])
    print()

    print("--- La base responde y tiene los catálogos y datos semilla ---")
    for tabla, minimo in [("roles", 3), ("categorias", 5), ("estados", 8), ("sectores", 1),
                          ("tipos_proveedor", 1), ("parroquias", 1), ("productos", 1),
                          ("boletines", 1)]:
        n = contar(tabla)
        check("tabla " + tabla + " con datos", n >= minimo, str(n) + " registros")

    def id_de(sql, params=()):
        return list(uno(sql, params).values())[0]

    rol_admin = id_de("SELECT id_rol FROM roles WHERE nombre = %s", ("Administrador",))
    rol_analista = id_de("SELECT id_rol FROM roles WHERE nombre = %s", ("Analista",))
    categoria = id_de("SELECT id_categoria FROM categorias ORDER BY id_categoria LIMIT 1")
    sector = id_de("SELECT id_sector FROM sectores ORDER BY id_sector LIMIT 1")
    parroquia = id_de("SELECT id_parroquia FROM parroquias ORDER BY id_parroquia LIMIT 1")
    tipo = id_de("SELECT id_tipo FROM tipos_proveedor ORDER BY id_tipo LIMIT 1")
    est_prod = id_de("SELECT id_estado FROM estados WHERE ambito = %s ORDER BY id_estado LIMIT 1", ("producto",))
    est_fact = id_de("SELECT id_estado FROM estados WHERE ambito = %s ORDER BY id_estado LIMIT 1", ("factura",))
    est_atendida = id_de("SELECT id_estado FROM estados WHERE ambito = %s AND nombre = %s",
                         ("solicitud", "Atendida"))
    servicio_existente = uno("SELECT id_producto, nombre FROM productos WHERE activo = TRUE ORDER BY id_producto LIMIT 1")

    publico = aplicacion.app.test_client()
    print("\n--- Sitio público (Semanas 2 a 10) ---")
    html = pagina(publico, "/", "/ (inicio)").get_data(as_text=True)
    for texto in ["<h1", "<h2", "Desarrollado por Juan Ram", "<nav", "<article", "<aside", "<footer",
                  "<section", "youtube", "id=\"contacto\"", "id=\"servicios\"", "id=\"quienes-somos\""]:
        check("La portada contiene " + texto, texto in html)
    pagina(publico, "/servicios")
    pagina(publico, "/servicios?categoria=" + str(categoria) + "&q=a", "/servicios filtrado")
    pagina(publico, "/boletines-publicos")
    pagina(publico, "/solicitar")
    pagina(publico, "/terminos")
    pagina(publico, "/login")
    pagina(publico, "/registro")
    check("Ruta inexistente responde 404 con página propia",
          publico.get("/no-existe").status_code == 404)

    print("\n--- Formulario público de solicitud (Semana 11) ---")
    antes = contar("solicitudes")
    publico.post("/solicitar", data={"nombre": "Ana", "organizacion": "", "correo": "no-es-correo",
                                     "id_producto": servicio_existente["id_producto"], "mensaje": "corto"})
    check("Rechaza una solicitud con datos inválidos", contar("solicitudes") == antes)
    publico.post("/solicitar", data={"nombre": "Ana Prueba", "organizacion": MARCA + " Solicitud",
                                     "correo": "ana@example.com", "telefono": "0991234567",
                                     "id_producto": servicio_existente["id_producto"],
                                     "mensaje": "Necesitamos información del servicio para la cooperativa."},
                 follow_redirects=True)
    sol = uno("SELECT id_solicitud, id_estado FROM solicitudes WHERE organizacion = %s", (MARCA + " Solicitud",))
    if sol:
        creado["solicitud"].append(sol["id_solicitud"])
    check("Guarda la solicitud válida en la base", contar("solicitudes") == antes + 1)

    print("\n--- Las rutas privadas están protegidas (Semana 14) ---")
    for ruta in ["/dashboard", "/productos", "/clientes", "/proveedores", "/facturacion",
                 "/boletines", "/solicitudes", "/reportes", "/usuarios", "/bitacora"]:
        check("sin sesión " + ruta + " redirige al login", publico.get(ruta).status_code == 302)

    print("\n--- Registro público con contraseña segura ---")
    antes = contar("usuarios")
    publico.post("/registro", data={"usuario": "qa_debil", "nombre_completo": "Usuario Debil",
                                    "correo": "debil@example.com", "id_rol": rol_analista,
                                    "password": "123", "confirmar": "123", "acepta": "y"})
    check("Rechaza una contraseña débil", contar("usuarios") == antes)
    publico.post("/registro", data={"usuario": "qa_analista", "nombre_completo": "Analista De Prueba",
                                    "correo": "qa.analista@example.com", "id_rol": rol_admin,
                                    "password": CLAVE, "confirmar": CLAVE, "acepta": "y"},
                 follow_redirects=True)
    nuevo = uno("SELECT u.id, u.password, r.nombre AS rol FROM usuarios u "
                "INNER JOIN roles r ON r.id_rol = u.id_rol WHERE u.usuario = %s", ("qa_analista",))
    if nuevo:
        creado["usuario"].append(nuevo["id"])
    check("Crea la cuenta válida", nuevo is not None)
    check("La contraseña se guarda con hash", nuevo and nuevo["password"] != CLAVE)
    check("El registro público asigna el rol Analista aunque se envíe otro",
          nuevo and (nuevo["rol"] == "Analista" or antes == 0))
    check("Se crea el perfil asociado (relación 1:1)",
          nuevo and uno("SELECT id_perfil FROM perfiles_usuario WHERE id_usuario = %s", (nuevo["id"],)) is not None)

    # Si la base estaba vacía, la primera cuenta nace como Administrador; para
    # probar las restricciones del rol se deja explícitamente como Analista.
    with aplicacion.app.app_context():
        aplicacion.ejecutar("UPDATE usuarios SET id_rol = %s WHERE id = %s", (rol_analista, nuevo["id"]))
    analista = aplicacion.app.test_client()
    r = analista.post("/login", data={"usuario": "qa_analista", "password": "otra"}, follow_redirects=True)
    check("Login con contraseña incorrecta no entra", analista.get("/dashboard").status_code == 302)
    analista.post("/login", data={"usuario": "qa.analista@example.com", "password": CLAVE})
    check("Login con correo y contraseña correctos", analista.get("/dashboard").status_code == 200)
    check("El rol Analista no entra a Usuarios", analista.get("/usuarios").status_code == 302)

    print("\n--- Sesión de administrador ---")
    with aplicacion.app.app_context():
        uid = aplicacion.insertar("INSERT INTO usuarios (usuario, password, id_rol) VALUES (%s, %s, %s)",
                                  ("qa_admin", generate_password_hash(CLAVE), rol_admin))
        aplicacion.ejecutar("INSERT INTO perfiles_usuario (id_usuario, nombre_completo, correo) VALUES (%s, %s, %s)",
                            (uid, "Administrador De Prueba", "qa.admin@example.com"))
    creado["usuario"].append(uid)
    c = aplicacion.app.test_client()
    c.post("/login", data={"usuario": "qa_admin", "password": CLAVE})

    for ruta in ["/dashboard", "/productos", "/productos/nuevo", "/clientes", "/clientes/nuevo",
                 "/proveedores", "/proveedores/nuevo", "/facturacion", "/facturacion/nueva",
                 "/boletines", "/boletines/nuevo", "/solicitudes", "/solicitudes?estado=" + str(est_atendida),
                 "/reportes", "/usuarios", "/usuarios/nuevo", "/bitacora", "/test_db",
                 "/productos?ver=baja", "/productos?ver=todos&q=a", "/clientes?pagina=2"]:
        pagina(c, ruta)

    tablas = c.get("/test_db").json
    check("La base tiene las 18 tablas del esquema", tablas["total_tablas"] >= 18,
          str(tablas["total_tablas"]) + " tablas")

    print("\n--- CREATE con validación (Semanas 11 y 15) ---")
    antes = contar("proveedores")
    c.post("/proveedores/nuevo", data={"nombre": MARCA + " Fuente", "id_tipo": tipo,
                                       "aporte": "Registro temporal de la prueba automática.",
                                       "correo": "prov@example.com", "telefono": "0320000001"})
    prov = uno("SELECT id_proveedor FROM proveedores WHERE nombre = %s", (MARCA + " Fuente",))
    if prov:
        creado["proveedor"].append(prov["id_proveedor"])
    check("CREATE fuente (proveedores)", contar("proveedores") == antes + 1)

    antes = contar("productos")
    c.post("/productos/nuevo", data={"nombre": MARCA + " Servicio", "id_categoria": categoria,
                                     "id_estado": est_prod, "precio": "45.00", "stock": 5,
                                     "id_proveedor": prov["id_proveedor"], "imagen": "servicio-boletin.jpg",
                                     "descripcion": "Registro temporal de la prueba automática."})
    prod = uno("SELECT id_producto, stock FROM productos WHERE nombre = %s", (MARCA + " Servicio",))
    if prod:
        creado["producto"].append(prod["id_producto"])
    check("CREATE servicio (productos)", contar("productos") == antes + 1)

    antes = contar("clientes")
    c.post("/clientes/nuevo", data={"nombre": "Cliente 3250", "ruc": "1600000000001", "id_sector": sector,
                                    "id_parroquia": parroquia, "servicio": servicio_existente["nombre"],
                                    "correo": "cli@example.com", "telefono": "0320000002"})
    check("Rechaza un nombre de organización con números", contar("clientes") == antes)
    c.post("/clientes/nuevo", data={"nombre": MARCA + " Cliente", "ruc": "9900000000001", "id_sector": sector,
                                    "id_parroquia": parroquia, "servicio": servicio_existente["nombre"],
                                    "correo": "cli@example.com", "telefono": "0320000002"})
    check("Rechaza un RUC con provincia inexistente", contar("clientes") == antes)
    c.post("/clientes/nuevo", data={"nombre": MARCA + " Cliente", "ruc": "1690000000001", "id_sector": sector,
                                    "id_parroquia": parroquia, "servicio": servicio_existente["nombre"],
                                    "correo": "cli@example.com", "telefono": "0320000002"})
    cli = uno("SELECT id_cliente FROM clientes WHERE nombre = %s", (MARCA + " Cliente",))
    if cli:
        creado["cliente"].append(cli["id_cliente"])
    check("CREATE organización (clientes)", contar("clientes") == antes + 1)

    codigo = "QA-" + date.today().strftime("%m%d") + "-" + str(uid)
    antes = contar("facturas")
    r = c.post("/facturacion/nueva", data={"codigo": codigo, "id_cliente": cli["id_cliente"],
                                           "servicio": "Suscripción de prueba", "id_estado": est_fact,
                                           "fecha": date.today().isoformat()})
    fact = uno("SELECT id_factura FROM facturas WHERE codigo = %s", (codigo,))
    if fact:
        creado["factura"].append(fact["id_factura"])
    check("CREATE suscripción (facturas)", contar("facturas") == antes + 1)
    check("Tras crear la suscripción se abre su detalle", "/facturacion/detalle/" in r.headers.get("Location", ""))

    antes = contar("boletines")
    c.post("/boletines/nuevo", data={"titulo": MARCA + " Boletín de prueba", "nivel": "Alto",
                                     "id_categoria": categoria, "id_proveedor": prov["id_proveedor"],
                                     "fecha": date.today().isoformat(), "referencia": "CVE-2026-0001",
                                     "resumen": "Resumen temporal creado por la prueba automática del sistema."})
    bol = uno("SELECT id_boletin FROM boletines WHERE titulo = %s", (MARCA + " Boletín de prueba",))
    if bol:
        creado["boletin"].append(bol["id_boletin"])
    check("CREATE boletín", contar("boletines") == antes + 1)
    check("El boletín activo se publica en la página pública",
          (MARCA + " Boletín de prueba") in publico.get("/boletines-publicos").get_data(as_text=True))

    print("\n--- READ de los formularios de edición ---")
    for ruta in ["/productos/editar/" + str(prod["id_producto"]), "/clientes/editar/" + str(cli["id_cliente"]),
                 "/proveedores/editar/" + str(prov["id_proveedor"]), "/facturacion/editar/" + str(fact["id_factura"]),
                 "/boletines/editar/" + str(bol["id_boletin"]), "/solicitudes/editar/" + str(sol["id_solicitud"]),
                 "/facturacion/detalle/" + str(fact["id_factura"])]:
        pagina(c, ruta)

    print("\n--- UPDATE (Semana 15) ---")
    c.post("/productos/editar/" + str(prod["id_producto"]),
           data={"nombre": MARCA + " Servicio Editado", "id_categoria": categoria, "id_estado": est_prod,
                 "precio": "99.99", "stock": 5, "id_proveedor": prov["id_proveedor"],
                 "imagen": "servicio-alerta.jpg", "descripcion": "Descripción modificada por la prueba."})
    p = uno("SELECT nombre, precio, imagen FROM productos WHERE id_producto = %s", (prod["id_producto"],))
    check("UPDATE servicio", p["nombre"].endswith("Editado") and float(p["precio"]) == 99.99
          and p["imagen"] == "servicio-alerta.jpg")

    c.post("/clientes/editar/" + str(cli["id_cliente"]),
           data={"nombre": MARCA + " Cliente Editado", "ruc": "1690000000001", "id_sector": sector,
                 "id_parroquia": parroquia, "servicio": servicio_existente["nombre"],
                 "correo": "cli2@example.com", "telefono": "0991234567"})
    check("UPDATE organización", uno("SELECT correo FROM clientes WHERE id_cliente = %s",
                                     (cli["id_cliente"],))["correo"] == "cli2@example.com")

    c.post("/proveedores/editar/" + str(prov["id_proveedor"]),
           data={"nombre": MARCA + " Fuente Editada", "id_tipo": tipo,
                 "aporte": "Aporte modificado por la prueba automática.",
                 "correo": "prov2@example.com", "telefono": "0320000009"})
    check("UPDATE fuente", uno("SELECT nombre FROM proveedores WHERE id_proveedor = %s",
                               (prov["id_proveedor"],))["nombre"].endswith("Editada"))

    c.post("/boletines/editar/" + str(bol["id_boletin"]),
           data={"titulo": MARCA + " Boletín de prueba", "nivel": "Critico", "id_categoria": categoria,
                 "id_proveedor": prov["id_proveedor"], "fecha": date.today().isoformat(), "referencia": "",
                 "resumen": "Resumen modificado por la prueba automática del sistema."})
    check("UPDATE boletín", uno("SELECT nivel FROM boletines WHERE id_boletin = %s",
                                (bol["id_boletin"],))["nivel"] == "Critico")

    c.post("/solicitudes/editar/" + str(sol["id_solicitud"]),
           data={"nombre": "Ana Prueba", "organizacion": MARCA + " Solicitud", "correo": "ana@example.com",
                 "telefono": "0991234567", "id_producto": servicio_existente["id_producto"],
                 "id_estado": est_atendida, "mensaje": "Necesitamos información del servicio para la cooperativa."})
    check("UPDATE estado de la solicitud", uno("SELECT id_estado FROM solicitudes WHERE id_solicitud = %s",
                                               (sol["id_solicitud"],))["id_estado"] == est_atendida)

    print("\n--- Relación N:N con control de cupos (Semanas 13 y 15) ---")
    url_detalle = "/facturacion/detalle/" + str(fact["id_factura"])
    antes = contar("detalle_factura")
    c.post(url_detalle, data={"id_producto": prod["id_producto"], "cantidad": 2, "precio_unitario": "99.99"})
    check("CREATE línea de detalle", contar("detalle_factura") == antes + 1)
    total = uno("SELECT total FROM facturas WHERE id_factura = %s", (fact["id_factura"],))["total"]
    check("El total de la suscripción se recalcula", float(total) == 199.98, "total = " + str(total))
    cupos = uno("SELECT stock FROM productos WHERE id_producto = %s", (prod["id_producto"],))["stock"]
    check("Se descuentan los cupos del servicio", cupos == 3, "cupos = " + str(cupos))
    c.post(url_detalle, data={"id_producto": prod["id_producto"], "cantidad": 10, "precio_unitario": ""})
    check("No deja contratar más cupos de los disponibles", contar("detalle_factura") == antes + 1)

    pagina(c, "/facturacion/" + str(fact["id_factura"]) + "/comprobante", "comprobante imprimible")
    r = c.get("/facturacion/" + str(fact["id_factura"]) + "/pdf")
    check("Comprobante en PDF", r.status_code == 200 and r.data[:4] == b"%PDF")

    print("\n--- Reportes exportables ---")
    html = c.get("/reportes").get_data(as_text=True)
    check("El reporte incluye el servicio contratado", MARCA + " Servicio Editado" in html)
    r = c.get("/reportes/exportar/csv")
    check("Exportar CSV", r.status_code == 200 and "csv" in r.headers.get("Content-Type", ""))
    r = c.get("/reportes/exportar/json")
    check("Exportar JSON", r.status_code == 200 and r.is_json)
    r = c.get("/reportes/exportar/pdf")
    check("Exportar PDF", r.status_code == 200 and r.data[:4] == b"%PDF")
    check("Formato de exportación desconocido responde 404", c.get("/reportes/exportar/xls").status_code == 404)

    print("\n--- Integridad referencial ---")
    antes = contar("productos")
    c.post("/productos/eliminar/" + str(prod["id_producto"]))
    check("No deja borrar un servicio incluido en una suscripción", contar("productos") == antes)

    print("\n--- Catálogos: tablas padre (categorías, sectores, tipos de fuente) ---")
    for clave in ["categorias", "sectores", "tipos-fuente"]:
        pagina(c, "/catalogos/" + clave)
    check("Catálogo inexistente responde 404", c.get("/catalogos/no-existe").status_code == 404)
    antes = contar("sectores")
    c.post("/catalogos/sectores/nuevo", data={"nombre": "Sector 123", "descripcion": "Nombre con números."})
    check("Rechaza un nombre de catálogo con números", contar("sectores") == antes)
    c.post("/catalogos/sectores/nuevo", data={"nombre": MARCA + " Sector",
                                              "descripcion": "Sector temporal creado por la prueba."})
    sec = uno("SELECT id_sector FROM sectores WHERE nombre = %s", (MARCA + " Sector",))
    check("CREATE en catálogo (sectores)", sec is not None)
    c.post("/catalogos/sectores/nuevo", data={"nombre": MARCA + " Sector",
                                              "descripcion": "Intento de registro duplicado."})
    check("No admite nombres repetidos en el catálogo", contar("sectores") == antes + 1)
    c.post("/catalogos/sectores/editar/" + str(sec["id_sector"]),
           data={"nombre": MARCA + " Sector", "descripcion": "Descripción editada por la prueba."})
    check("UPDATE en catálogo", uno("SELECT descripcion FROM sectores WHERE id_sector = %s",
                                    (sec["id_sector"],))["descripcion"].startswith("Descripción editada"))
    antes = contar("sectores")
    c.post("/catalogos/sectores/eliminar/" + str(sector))
    check("No deja borrar un sector que usan organizaciones", contar("sectores") == antes)
    c.post("/catalogos/sectores/eliminar/" + str(sec["id_sector"]))
    check("DELETE en catálogo", contar("sectores") == antes - 1)

    print("\n--- Baja lógica por cambio de estado (Semana 15) ---")
    antes = contar("productos")
    c.post("/productos/baja/" + str(prod["id_producto"]))
    fila = uno("SELECT activo FROM productos WHERE id_producto = %s", (prod["id_producto"],))
    check("Dar de baja un servicio hace UPDATE, no DELETE",
          contar("productos") == antes and fila is not None and not fila["activo"])
    check("El servicio dado de baja sale del listado de activos",
          (MARCA + " Servicio Editado") not in c.get("/productos").get_data(as_text=True))
    check("El servicio dado de baja aparece en el filtro 'Dados de baja'",
          (MARCA + " Servicio Editado") in c.get("/productos?ver=baja").get_data(as_text=True))
    check("El servicio dado de baja no aparece en el catálogo público",
          (MARCA + " Servicio Editado") not in publico.get("/servicios").get_data(as_text=True))
    c.post("/productos/reactivar/" + str(prod["id_producto"]))
    fila = uno("SELECT activo FROM productos WHERE id_producto = %s", (prod["id_producto"],))
    check("Reactivar devuelve el servicio al listado", bool(fila and fila["activo"]))

    for modulo, ruta, tabla, campo, ident in (
        ("organización", "clientes", "clientes", "id_cliente", cli["id_cliente"]),
        ("fuente", "proveedores", "proveedores", "id_proveedor", prov["id_proveedor"]),
        ("suscripción", "facturacion", "facturas", "id_factura", fact["id_factura"]),
        ("boletín", "boletines", "boletines", "id_boletin", bol["id_boletin"]),
        ("solicitud", "solicitudes", "solicitudes", "id_solicitud", sol["id_solicitud"]),
    ):
        antes = contar(tabla)
        c.post("/" + ruta + "/baja/" + str(ident))
        fila = uno("SELECT activo FROM " + tabla + " WHERE " + campo + " = %s", (ident,))
        ok_baja = contar(tabla) == antes and fila is not None and not fila["activo"]
        c.post("/" + ruta + "/reactivar/" + str(ident))
        fila = uno("SELECT activo FROM " + tabla + " WHERE " + campo + " = %s", (ident,))
        check("Baja y reactivación de " + modulo, ok_baja and bool(fila and fila["activo"]))

    print("\n--- DELETE (Semana 15) ---")
    det = uno("SELECT id_detalle FROM detalle_factura WHERE id_factura = %s", (fact["id_factura"],))
    antes = contar("detalle_factura")
    c.post(url_detalle + "/eliminar/" + str(det["id_detalle"]))
    check("DELETE línea de detalle", contar("detalle_factura") == antes - 1)
    cupos = uno("SELECT stock FROM productos WHERE id_producto = %s", (prod["id_producto"],))["stock"]
    check("Al quitar la línea se devuelven los cupos", cupos == 5, "cupos = " + str(cupos))

    for modulo, ruta, tabla, campo, ident, clave in (
        ("servicio", "productos", "productos", "id_producto", prod["id_producto"], "producto"),
        ("suscripción", "facturacion", "facturas", "id_factura", fact["id_factura"], "factura"),
        ("organización", "clientes", "clientes", "id_cliente", cli["id_cliente"], "cliente"),
        ("boletín", "boletines", "boletines", "id_boletin", bol["id_boletin"], "boletin"),
        ("solicitud", "solicitudes", "solicitudes", "id_solicitud", sol["id_solicitud"], "solicitud"),
        ("fuente", "proveedores", "proveedores", "id_proveedor", prov["id_proveedor"], "proveedor"),
    ):
        antes = contar(tabla)
        c.post("/" + ruta + "/eliminar/" + str(ident))
        borrado = contar(tabla) == antes - 1
        if borrado:
            creado[clave].remove(ident)
        check("DELETE " + modulo, borrado)

    print("\n--- Usuarios y bitácora (rol Administrador) ---")
    c.post("/usuarios/rol/" + str(nuevo["id"]), data={"id_rol": rol_admin})
    check("Cambiar el rol de un usuario", uno("SELECT id_rol FROM usuarios WHERE id = %s",
                                              (nuevo["id"],))["id_rol"] == rol_admin)
    c.post("/usuarios/rol/" + str(uid), data={"id_rol": rol_analista})
    check("Un administrador no puede quitarse su propio rol",
          uno("SELECT id_rol FROM usuarios WHERE id = %s", (uid,))["id_rol"] == rol_admin)
    eventos = contar("bitacora")
    check("La bitácora registró las operaciones", eventos > 0, str(eventos) + " eventos")
    check("La bitácora se puede filtrar por módulo", c.get("/bitacora?modulo=Servicios").status_code == 200)
    antes = contar("usuarios")
    c.post("/usuarios/eliminar/" + str(nuevo["id"]))
    if contar("usuarios") == antes - 1:
        creado["usuario"].remove(nuevo["id"])
    check("Eliminar usuario", contar("usuarios") == antes - 1)

    print("\n--- Cierre de sesión ---")
    c.get("/logout")
    check("Tras cerrar sesión el panel vuelve a estar protegido", c.get("/dashboard").status_code == 302)


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
