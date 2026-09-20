from wtforms import (StringField, IntegerField, DecimalField, TextAreaField,
                     SelectField, SubmitField)
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange
from flask_wtf import FlaskForm


class ProductoForm(FlaskForm):
    """Formulario del módulo de servicios CTI.

    La misma clase se reutiliza para registrar y para editar un registro: la
    ruta de edición carga los datos actuales con ProductoForm(data=producto).
    Las opciones de los SelectField se llenan desde las tablas de catálogo.
    """

    nombre = StringField('Nombre del servicio', validators=[
        DataRequired(message='El nombre del servicio es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])

    id_categoria = SelectField('Categoría', coerce=int, validators=[
        InputRequired(message='Debe seleccionar una categoría')
    ])

    id_estado = SelectField('Estado', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un estado')
    ])

    precio = DecimalField('Precio (USD)', places=2, validators=[
        InputRequired(message='El precio es requerido'),
        NumberRange(min=0, max=100000, message='El precio debe estar entre 0 y 100000')
    ])

    stock = IntegerField('Stock', validators=[
        InputRequired(message='El stock es requerido'),
        NumberRange(min=0, message='El stock no puede ser negativo')
    ])

    id_proveedor = SelectField('Proveedor', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un proveedor')
    ])

    descripcion = TextAreaField('Descripción', validators=[
        DataRequired(message='La descripción es requerida'),
        Length(min=10, max=500, message='La descripción debe tener entre 10 y 500 caracteres')
    ])

    enviar = SubmitField('Guardar servicio')
