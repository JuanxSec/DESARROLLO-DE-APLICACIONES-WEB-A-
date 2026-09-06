from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre del Cliente', validators=[
        DataRequired(message='El nombre del cliente es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])

    sector = StringField('Sector', validators=[
        DataRequired(message='El sector es requerido'),
        Length(min=3, max=50, message='El sector debe tener entre 3 y 50 caracteres')
    ])

    servicio = SelectField('Servicio', choices=[
        ('Boletines CTI', 'Boletines CTI'),
        ('Noticias de seguridad', 'Noticias de seguridad'),
        ('Alertas de vulnerabilidad', 'Alertas de vulnerabilidad')
    ], validators=[DataRequired(message='Debe seleccionar un servicio')])

    enviar = SubmitField('Guardar Cliente')
