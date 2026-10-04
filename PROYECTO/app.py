"""Proyecto Integrador JuansecCTI - Desarrollo de Aplicaciones Web.

JuansecCTI es una empresa (ficticia, con fines académicos) que presta servicios
de ciberinteligencia de amenazas (Cyber Threat Intelligence): boletines,
alertas de vulnerabilidades, monitoreo de la dark web, protección de marca,
búsqueda proactiva de amenazas y apoyo en incidentes.

Punto de entrada de la aplicación. El código está organizado en carpetas:

  extensiones.py  creación de la aplicación, configuración, CSRF y Flask-Login.
  rutas/          una vista por módulo (público, autenticación, panel, CRUD,
                  reportes, catálogos y usuarios).
  modelos/        acceso a datos con consultas SQL parametrizadas por entidad.
  forms/          formularios Flask-WTF / WTForms.
  conexion/       conexión con MySQL, PostgreSQL o SQLite.
  templates/ y static/  plantillas Jinja2, CSS, JavaScript e imágenes.

Avances de la asignatura que integra:
  * Semana 9  : proyecto Flask, carpetas templates/static y rutas por módulo.
  * Semana 10 : contenido dinámico con Jinja2 (variables, for, if, filtros,
                herencia de base.html y componentes reutilizables).
  * Semana 11 : formularios con Flask-WTF / WTForms, validaciones y CSRF.
  * Semana 12 : persistencia local con SQLite (DB_ENGINE=sqlite).
  * Semana 13 : base de datos relacional MySQL con SELECT, INSERT, UPDATE y
                DELETE parametrizados.
  * Semana 14 : login funcional con Flask-Login y Werkzeug.
  * Semana 15 : CRUD completo sobre PostgreSQL desplegado en Render, consultas
                JOIN, baja lógica y reportes exportables.
  * Semana 16 : pruebas del sistema (pruebas/prueba_sistema.py).
"""

import os

from extensiones import app
import rutas  # noqa: F401  (importar el paquete registra todas las rutas)
from modelos.base import consultar, ejecutar, insertar, contar  # noqa: F401  (usadas por las pruebas)
from modelos.migracion import migrar_base

with app.app_context():
    # La migración nunca impide que la aplicación arranque: si la base todavía
    # no responde, las rutas que la necesiten ya avisarán.
    try:
        migrar_base()
    except Exception as error:  # noqa: BLE001
        print('[migracion] no se pudo completar: ' + str(error))


if __name__ == '__main__':
    # En producción el servidor lo levanta gunicorn, así que este bloque solo se
    # usa en desarrollo. El modo depuración queda apagado salvo que se pida.
    puerto = int(os.environ.get('PORT', '5000'))
    depuracion = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=puerto, debug=depuracion)
