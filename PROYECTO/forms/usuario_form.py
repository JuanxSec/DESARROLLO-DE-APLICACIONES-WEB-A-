from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_wtf import FlaskForm


class UsuarioForm(FlaskForm):
    usuario = StringField('Usuario', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=3, max=50, message='El usuario debe tener entre 3 y 50 caracteres')
    ])

    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])

    confirmar = PasswordField('Confirmar contraseña', validators=[
        DataRequired(message='Debe confirmar la contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])

    enviar = SubmitField('Registrar usuario')
