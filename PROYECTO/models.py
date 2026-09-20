from flask_login import UserMixin


class Usuario(UserMixin):
    """Representa un registro de la tabla usuarios para Flask-Login.

    Incluye el rol y el nombre del perfil (relación uno a uno con
    perfiles_usuario) para poder mostrarlos en la interfaz con current_user.
    """

    def __init__(self, id, usuario, password, rol=None, nombre_completo=None):
        self.id = id
        self.usuario = usuario
        self.password = password
        self.rol = rol
        self.nombre_completo = nombre_completo
