from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import (DataRequired, InputRequired, Length, Email,
                                Optional, Regexp)
from flask_wtf import FlaskForm


class ClienteForm(FlaskForm):
    """Formulario del módulo de clientes, reutilizado para registrar y editar."""

    nombre = StringField('Nombre del cliente', validators=[
        DataRequired(message='El nombre del cliente es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])

    id_sector = SelectField('Sector', coerce=int, validators=[
        InputRequired(message='Debe seleccionar un sector')
    ])

    id_parroquia = SelectField('Ubicación', coerce=int, validators=[
        InputRequired(message='Debe seleccionar la ubicación del cliente')
    ])

    servicio = SelectField('Servicio contratado', choices=[
        ('Boletines CTI', 'Boletines CTI'),
        ('Noticias de seguridad', 'Noticias de seguridad'),
        ('Alertas de vulnerabilidad', 'Alertas de vulnerabilidad'),
        ('Informe mensual', 'Informe mensual'),
        ('Capacitación', 'Capacitación')
    ], validators=[DataRequired(message='Debe seleccionar un servicio')])

    correo = StringField('Correo electrónico', validators=[
        Optional(),
        Email(message='Debe ingresar un correo electrónico válido'),
        Length(max=120, message='El correo no debe superar los 120 caracteres')
    ])

    telefono = StringField('Teléfono', validators=[
        Optional(),
        Regexp(r'^[0-9]{7,10}$', message='El teléfono debe contener entre 7 y 10 dígitos')
    ])

    enviar = SubmitField('Guardar cliente')
