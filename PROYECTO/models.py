from flask_login import UserMixin


class Usuario(UserMixin):
    """Representa un registro de la tabla usuarios para Flask-Login."""

    def __init__(self, id, usuario, password):
        self.id = id
        self.usuario = usuario
        self.password = password
