from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField
from wtforms.validators import (DataRequired, InputRequired, Length, EqualTo,
                                Email, Regexp)
from flask_wtf import FlaskForm

from forms.validadores import SOLO_LETRAS, contrasena_segura


class UsuarioForm(FlaskForm):
    """Registro de usuarios del sistema (Semana 14).

    Además del usuario y la contraseña recoge los datos del perfil, que se
    guardan en la tabla perfiles_usuario (relación uno a uno con usuarios).
    """

    usuario = StringField('Usuario', validators=[
        DataRequired(message='El usuario es requerido'),
        Length(min=4, max=50, message='El usuario debe tener entre 4 y 50 caracteres'),
        Regexp(r'^[A-Za-z0-9._]+$',
               message='El usuario solo admite letras, números, punto y guion bajo')
    ])

    nombre_completo = StringField('Nombre completo', validators=[
        DataRequired(message='El nombre completo es requerido'),
        Length(min=3, max=120, message='El nombre debe tener entre 3 y 120 caracteres'),
        SOLO_LETRAS
    ])

    correo = StringField('Correo electrónico', validators=[
        DataRequired(message='El correo es requerido'),
        Email(message='Debe ingresar un correo electrónico válido'),
        Length(max=120, message='El correo no debe superar los 120 caracteres')
    ])

    # Solo un administrador puede elegir el rol; en el registro público se
    # asigna el rol Analista.
    id_rol = SelectField('Rol', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un rol')
    ])

    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        contrasena_segura
    ])

    confirmar = PasswordField('Confirmar contraseña', validators=[
        DataRequired(message='Debe confirmar la contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])

    acepta = BooleanField('Acepto los términos de uso y la política de privacidad', validators=[
        DataRequired(message='Debe aceptar los términos para crear la cuenta')
    ])

    enviar = SubmitField('Crear cuenta')
