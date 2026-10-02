"""Validadores reutilizables de WTForms.

Repiten en el servidor las mismas reglas que static/js/script.js aplica en el
navegador: la validación del cliente da respuesta inmediata y la del servidor
garantiza que a la base de datos solo llegue información limpia.
"""

import re

from wtforms.validators import ValidationError, Regexp

# Letras (con tildes y ñ), espacios y los signos habituales en nombres de
# organizaciones. No admite dígitos: el docente pidió que un campo de nombre
# rechace valores como "3250".
SOLO_LETRAS = Regexp(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ .,&\-]*$",
    message='Solo se admiten letras, espacios y los signos . , & -'
)

# Teléfono ecuatoriano: fijo de 9 dígitos (032885000) o celular de 10
# (0991234567). Se guarda como texto para no perder el cero inicial.
TELEFONO_EC = Regexp(
    r'^0[0-9]{8,9}$',
    message='El teléfono debe empezar con 0 y tener 9 o 10 dígitos, solo números'
)


def ruc_ecuatoriano(form, field):
    """RUC de 13 dígitos: provincia válida (01-24 o 30) y terminación 001."""
    valor = (field.data or '').strip()
    if not valor:
        return
    if not re.fullmatch(r'[0-9]{13}', valor):
        raise ValidationError('El RUC debe tener exactamente 13 dígitos')
    provincia = int(valor[:2])
    if not (1 <= provincia <= 24 or provincia == 30):
        raise ValidationError('Los dos primeros dígitos del RUC no corresponden a una provincia')
    if not valor.endswith('001'):
        raise ValidationError('El RUC de una organización termina en 001')


def contrasena_segura(form, field):
    """Mínimo 8 caracteres con mayúscula, minúscula, número y carácter especial."""
    clave = field.data or ''
    faltan = []
    if len(clave) < 8:
        faltan.append('8 caracteres')
    if not re.search(r'[A-Z]', clave):
        faltan.append('una mayúscula')
    if not re.search(r'[a-z]', clave):
        faltan.append('una minúscula')
    if not re.search(r'[0-9]', clave):
        faltan.append('un número')
    if not re.search(r'[^A-Za-z0-9]', clave):
        faltan.append('un carácter especial')
    if faltan:
        raise ValidationError('La contraseña necesita al menos: ' + ', '.join(faltan))
