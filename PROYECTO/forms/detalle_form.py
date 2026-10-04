from wtforms import IntegerField, DecimalField, SelectField, SubmitField
from wtforms.validators import InputRequired, NumberRange, Optional
from flask_wtf import FlaskForm


class DetalleFacturaForm(FlaskForm):
    """Servicios de una suscripción (tabla intermedia detalle_factura)."""

    id_producto = SelectField('Servicio', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un servicio')
    ])

    cantidad = IntegerField('Cantidad (cupos)', default=1, validators=[
        InputRequired(message='La cantidad es requerida'),
        NumberRange(min=1, max=999, message='La cantidad debe estar entre 1 y 999')
    ])

    # Si se deja vacío se toma el precio vigente del servicio.
    precio_unitario = DecimalField('Precio unitario (USD)', places=2, validators=[
        Optional(),
        NumberRange(min=0, max=100000, message='El precio debe estar entre 0 y 100000')
    ])

    enviar = SubmitField('Agregar al detalle')
