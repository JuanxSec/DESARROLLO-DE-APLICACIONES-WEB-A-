from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm


class LoginForm(FlaskForm):
    """Inicio de sesión con el nombre de usuario o con el correo del perfil."""

    usuario = StringField('Usuario o correo', validators=[
        DataRequired(message='El usuario o correo es requerido'),
        Length(min=3, max=120, message='Debe tener entre 3 y 120 caracteres')
    ])

    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida')
    ])

    recordar = BooleanField('Mantener la sesión iniciada')

    enviar = SubmitField('Ingresar')
