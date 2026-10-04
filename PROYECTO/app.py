"""Punto de entrada del proyecto JuansecCTI (Desarrollo de Aplicaciones Web).

Las rutas están en rutas/, el acceso a datos en modelos/ y la configuración
en extensiones.py.
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
