from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm

from forms.validadores import SOLO_LETRAS


class CatalogoForm(FlaskForm):
    """Formulario de los catálogos: categorías, sectores y tipos de fuente."""

    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=3, max=60, message='El nombre debe tener entre 3 y 60 caracteres'),
        SOLO_LETRAS
    ])

    descripcion = TextAreaField('Descripción', validators=[
        DataRequired(message='La descripción es requerida'),
        Length(min=10, max=200, message='La descripción debe tener entre 10 y 200 caracteres')
    ])

    enviar = SubmitField('Guardar')
