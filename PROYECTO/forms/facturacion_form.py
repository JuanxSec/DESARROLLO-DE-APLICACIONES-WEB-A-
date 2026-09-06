from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm

class FacturacionForm(FlaskForm):
    codigo = StringField('Código de Factura', validators=[
        DataRequired(message='El código de factura es requerido'),
        Length(min=3, max=20, message='El código debe tener entre 3 y 20 caracteres')
    ])

    cliente = StringField('Cliente', validators=[
        DataRequired(message='El cliente es requerido'),
        Length(min=3, max=100, message='El cliente debe tener entre 3 y 100 caracteres')
    ])

    servicio = StringField('Servicio', validators=[
        DataRequired(message='El servicio es requerido'),
        Length(min=3, max=100, message='El servicio debe tener entre 3 y 100 caracteres')
    ])

    estado = SelectField('Estado', choices=[
        ('Pagado', 'Pagado'),
        ('Pendiente', 'Pendiente'),
        ('Emitida', 'Emitida')
    ], validators=[DataRequired(message='Debe seleccionar un estado')])

    enviar = SubmitField('Guardar Factura')
