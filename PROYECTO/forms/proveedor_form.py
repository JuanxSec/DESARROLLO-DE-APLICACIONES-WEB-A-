from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, Email, Optional
from flask_wtf import FlaskForm

from forms.validadores import TELEFONO_EC


class ProveedorForm(FlaskForm):
    """Formulario de fuentes de inteligencia, reutilizado para registrar y editar."""

    nombre = StringField('Nombre de la fuente', validators=[
        DataRequired(message='El nombre de la fuente es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])

    id_tipo = SelectField('Tipo de fuente', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un tipo de fuente')
    ])

    aporte = TextAreaField('Aporte al servicio', validators=[
        DataRequired(message='El aporte es requerido'),
        Length(min=10, max=300, message='El aporte debe tener entre 10 y 300 caracteres')
    ])

    correo = StringField('Correo electrónico', validators=[
        Optional(),
        Email(message='Debe ingresar un correo electrónico válido'),
        Length(max=120, message='El correo no debe superar los 120 caracteres')
    ])

    telefono = StringField('Teléfono', validators=[
        Optional(),
        TELEFONO_EC
    ])

    enviar = SubmitField('Guardar fuente')
