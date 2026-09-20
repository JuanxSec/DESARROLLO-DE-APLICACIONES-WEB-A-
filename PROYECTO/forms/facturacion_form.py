from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, Regexp
from flask_wtf import FlaskForm


class FacturacionForm(FlaskForm):
    """Formulario del módulo de facturación, reutilizado para registrar y editar."""

    codigo = StringField('Código de factura', validators=[
        DataRequired(message='El código de factura es requerido'),
        Length(min=3, max=20, message='El código debe tener entre 3 y 20 caracteres'),
        Regexp(r'^[A-Za-z0-9\-]+$',
               message='El código solo admite letras, números y guiones')
    ])

    id_cliente = SelectField('Cliente', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un cliente')
    ])

    servicio = StringField('Servicio facturado', validators=[
        DataRequired(message='El servicio es requerido'),
        Length(min=3, max=100, message='El servicio debe tener entre 3 y 100 caracteres')
    ])

    id_estado = SelectField('Estado', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un estado')
    ])

    fecha = DateField('Fecha de emisión', validators=[
        DataRequired(message='La fecha de emisión es requerida')
    ])

    enviar = SubmitField('Guardar factura')
