"""Pista de auditoría: tabla bitacora."""

from flask_login import current_user

from extensiones import app
from modelos.base import ejecutar


def registrar(accion, modulo, detalle):
    """Pista de auditoría: guarda quién hizo qué y cuándo en la tabla bitacora."""
    try:
        if current_user.is_authenticated:
            id_usuario, nombre = current_user.id, current_user.usuario
        else:
            id_usuario, nombre = None, 'visitante'
        ejecutar('INSERT INTO bitacora (id_usuario, usuario, accion, modulo, detalle) '
                 'VALUES (%s, %s, %s, %s, %s)',
                 (id_usuario, nombre, accion, modulo, detalle[:255]))
    except Exception as error:  # noqa: BLE001
        # La auditoría nunca debe impedir la operación principal.
        app.logger.warning('No se pudo registrar en la bitácora: %s', error)
