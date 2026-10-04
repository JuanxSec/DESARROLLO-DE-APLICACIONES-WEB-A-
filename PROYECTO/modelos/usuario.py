"""Modelo de usuario para Flask-Login y consultas de las tablas usuarios y perfiles_usuario (1:1)."""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash

from modelos.base import consultar, ejecutar, insertar


class Usuario(UserMixin):
    """Usuario de Flask-Login con su rol y los datos del perfil."""

    def __init__(self, id, usuario, password, rol=None, nombre_completo=None, correo=None):
        self.id = id
        self.usuario = usuario
        self.password = password
        self.rol = rol
        self.nombre_completo = nombre_completo
        self.correo = correo

    @property
    def iniciales(self):
        """Dos letras para el avatar del menú lateral."""
        base = (self.nombre_completo or self.usuario or '?').split()
        return ''.join(parte[0] for parte in base[:2]).upper()


SQL_USUARIO = ('SELECT u.id, u.usuario, u.password, r.nombre AS rol, p.nombre_completo, p.correo '
               'FROM usuarios u '
               'INNER JOIN roles r ON r.id_rol = u.id_rol '
               'LEFT JOIN perfiles_usuario p ON p.id_usuario = u.id ')


def usuario_desde_fila(data):
    return Usuario(data['id'], data['usuario'], data['password'], data['rol'],
                   data['nombre_completo'], data.get('correo'))


def crear_usuario(form, id_rol):
    """INSERT del usuario con la contraseña cifrada y de su perfil (relación 1:1)."""
    nuevo_id = insertar(
        'INSERT INTO usuarios (usuario, password, id_rol) VALUES (%s, %s, %s)',
        (form.usuario.data, generate_password_hash(form.password.data), id_rol)
    )
    ejecutar('INSERT INTO perfiles_usuario (id_usuario, nombre_completo, correo) VALUES (%s, %s, %s)',
             (nuevo_id, form.nombre_completo.data.strip(), form.correo.data.strip()))
    return nuevo_id


def datos_duplicados(form):
    if consultar('SELECT id FROM usuarios WHERE usuario = %s', (form.usuario.data,), uno=True):
        return 'El usuario "' + form.usuario.data + '" ya está registrado.'
    if consultar('SELECT id_perfil FROM perfiles_usuario WHERE correo = %s', (form.correo.data,), uno=True):
        return 'El correo ' + form.correo.data + ' ya pertenece a otra cuenta.'
    return None
