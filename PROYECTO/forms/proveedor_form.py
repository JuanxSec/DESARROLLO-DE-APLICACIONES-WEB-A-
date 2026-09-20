from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import (DataRequired, InputRequired, Length, Email,
                                Optional, Regexp)
from flask_wtf import FlaskForm


class ProveedorForm(FlaskForm):
    """Formulario del módulo de proveedores, reutilizado para registrar y editar."""

    nombre = StringField('Nombre del proveedor', validators=[
        DataRequired(message='El nombre del proveedor es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])

    id_tipo = SelectField('Tipo de proveedor', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un tipo de proveedor')
    ])

    aporte = TextAreaField('Aporte', validators=[
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
        Regexp(r'^[0-9]{7,10}$', message='El teléfono debe contener entre 7 y 10 dígitos')
    ])

    enviar = SubmitField('Guardar proveedor')
