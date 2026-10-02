from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, Email, Optional
from flask_wtf import FlaskForm

from forms.validadores import SOLO_LETRAS, TELEFONO_EC, ruc_ecuatoriano


class ClienteForm(FlaskForm):
    """Formulario de organizaciones suscritas, reutilizado para registrar y editar."""

    nombre = StringField('Nombre de la organización', validators=[
        DataRequired(message='El nombre de la organización es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres'),
        SOLO_LETRAS
    ])

    ruc = StringField('RUC', validators=[
        Optional(),
        ruc_ecuatoriano
    ])

    id_sector = SelectField('Sector', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un sector')
    ])

    id_parroquia = SelectField('Ubicación', coerce=int, validators=[
        InputRequired(message='Debe seleccionar la ubicación de la organización')
    ])

    # Las opciones se cargan desde la tabla de servicios activos.
    servicio = SelectField('Servicio de interés', validators=[
        DataRequired(message='Debe seleccionar un servicio')
    ])

    correo = StringField('Correo electrónico', validators=[
        DataRequired(message='El correo es requerido'),
        Email(message='Debe ingresar un correo electrónico válido'),
        Length(max=120, message='El correo no debe superar los 120 caracteres')
    ])

    telefono = StringField('Teléfono', validators=[
        Optional(),
        TELEFONO_EC
    ])

    enviar = SubmitField('Guardar organización')
