from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import (DataRequired, InputRequired, Length, EqualTo,
                                Email, Optional)
from flask_wtf import FlaskForm


class UsuarioForm(FlaskForm):
    """Registro de usuarios del sistema (Semana 14).

    Además del usuario y la contraseña recoge los datos del perfil, que se
    guardan en la tabla perfiles_usuario (relación uno a uno con usuarios).
    """

    usuario = StringField('Usuario', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=3, max=50, message='El usuario debe tener entre 3 y 50 caracteres')
    ])

    nombre_completo = StringField('Nombre completo', validators=[
        DataRequired(message='El nombre completo es requerido'),
        Length(min=3, max=120, message='El nombre debe tener entre 3 y 120 caracteres')
    ])

    correo = StringField('Correo electrónico', validators=[
        Optional(),
        Email(message='Debe ingresar un correo electrónico válido'),
        Length(max=120, message='El correo no debe superar los 120 caracteres')
    ])

    id_rol = SelectField('Rol', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un rol')
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
