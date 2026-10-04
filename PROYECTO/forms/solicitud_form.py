from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, Email, Optional
from flask_wtf import FlaskForm

from forms.validadores import SOLO_LETRAS, TELEFONO_EC


class SolicitudForm(FlaskForm):
    """Solicitud de información de la página pública y del panel."""

    nombre = StringField('Nombre completo', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres'),
        SOLO_LETRAS
    ])

    organizacion = StringField('Organización', validators=[
        DataRequired(message='La organización es requerida'),
        Length(min=3, max=120, message='La organización debe tener entre 3 y 120 caracteres')
    ])

    correo = StringField('Correo electrónico', validators=[
        DataRequired(message='El correo es requerido'),
        Email(message='Debe ingresar un correo electrónico válido'),
        Length(max=120)
    ])

    telefono = StringField('Teléfono', validators=[
        Optional(),
        TELEFONO_EC
    ])

    id_producto = SelectField('Servicio de interés', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un servicio')
    ])

    id_estado = SelectField('Estado', coerce=int, validators=[Optional()])

    mensaje = TextAreaField('Mensaje', validators=[
        DataRequired(message='El mensaje es requerido'),
        Length(min=15, max=600, message='El mensaje debe tener entre 15 y 600 caracteres')
    ])

    enviar = SubmitField('Enviar solicitud')
