from wtforms import StringField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf import FlaskForm

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre del Producto', validators=[
        DataRequired(message='El nombre del producto es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])

    categoria = StringField('Categoría', validators=[
        DataRequired(message='La categoría es requerida'),
        Length(min=3, max=50, message='La categoría debe tener entre 3 y 50 caracteres')
    ])

    estado = SelectField('Estado', choices=[
        ('Disponible', 'Disponible'),
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo')
    ], validators=[DataRequired(message='Debe seleccionar un estado')])

    stock = IntegerField('Stock', validators=[
        DataRequired(message='El stock es requerido'),
        NumberRange(min=0, message='El stock no puede ser negativo')
    ])

    descripcion = TextAreaField('Descripción', validators=[
        DataRequired(message='La descripción es requerida'),
        Length(min=10, max=500, message='La descripción debe tener entre 10 y 500 caracteres')
    ])

    enviar = SubmitField('Guardar Producto')
