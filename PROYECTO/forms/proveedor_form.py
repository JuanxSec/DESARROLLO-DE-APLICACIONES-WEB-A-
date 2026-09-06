from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm

class ProveedorForm(FlaskForm):
    nombre = StringField('Nombre del Proveedor', validators=[
        DataRequired(message='El nombre del proveedor es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])

    tipo = StringField('Tipo de Proveedor', validators=[
        DataRequired(message='El tipo de proveedor es requerido'),
        Length(min=3, max=50, message='El tipo debe tener entre 3 y 50 caracteres')
    ])

    aporte = TextAreaField('Aporte', validators=[
        DataRequired(message='El aporte es requerido'),
        Length(min=10, max=300, message='El aporte debe tener entre 10 y 300 caracteres')
    ])

    enviar = SubmitField('Guardar Proveedor')
