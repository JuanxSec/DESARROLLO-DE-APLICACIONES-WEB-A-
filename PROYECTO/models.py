from flask_login import UserMixin


class Usuario(UserMixin):
    """Representa un registro de la tabla usuarios para Flask-Login.

    Incluye el rol y los datos del perfil (relación uno a uno con
    perfiles_usuario) para mostrarlos en la interfaz mediante current_user.
    """

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
