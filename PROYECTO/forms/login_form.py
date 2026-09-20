from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm


class LoginForm(FlaskForm):
    usuario = StringField('Usuario', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=3, max=50, message='El usuario debe tener entre 3 y 50 caracteres')
    ])

    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida')
    ])

    enviar = SubmitField('Iniciar sesión')
