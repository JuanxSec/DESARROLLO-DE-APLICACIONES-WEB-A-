from wtforms import IntegerField, DecimalField, SelectField, SubmitField
from wtforms.validators import InputRequired, NumberRange
from flask_wtf import FlaskForm


class DetalleFacturaForm(FlaskForm):
    """Formulario de la tabla intermedia detalle_factura (relación N:N).

    Permite agregar los servicios que componen una factura: una factura puede
    incluir varios servicios y un mismo servicio puede estar en varias facturas.
    """

    id_producto = SelectField('Servicio', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un servicio')
    ])

    cantidad = IntegerField('Cantidad', default=1, validators=[
        InputRequired(message='La cantidad es requerida'),
        NumberRange(min=1, max=999, message='La cantidad debe estar entre 1 y 999')
    ])

    precio_unitario = DecimalField('Precio unitario (USD)', places=2, validators=[
        InputRequired(message='El precio unitario es requerido'),
        NumberRange(min=0, max=100000, message='El precio debe estar entre 0 y 100000')
    ])

    enviar = SubmitField('Agregar al detalle')
