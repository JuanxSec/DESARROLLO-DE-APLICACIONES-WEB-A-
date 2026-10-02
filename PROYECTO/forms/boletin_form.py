from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, Optional
from flask_wtf import FlaskForm

NIVELES = [('Critico', 'Crítico'), ('Alto', 'Alto'), ('Medio', 'Medio'), ('Bajo', 'Bajo')]


class BoletinForm(FlaskForm):
    """Boletines de ciberinteligencia que se publican en la página principal."""

    titulo = StringField('Título', validators=[
        DataRequired(message='El título es requerido'),
        Length(min=10, max=150, message='El título debe tener entre 10 y 150 caracteres')
    ])

    nivel = SelectField('Nivel de riesgo', choices=NIVELES, validators=[
        DataRequired(message='Debe seleccionar el nivel de riesgo')
    ])

    id_categoria = SelectField('Categoría', coerce=int, validators=[
        InputRequired(message='Debe seleccionar una categoría')
    ])

    id_proveedor = SelectField('Fuente', coerce=int, validators=[
        InputRequired(message='Debe seleccionar una fuente')
    ])

    fecha = DateField('Fecha de publicación', validators=[
        DataRequired(message='La fecha es requerida')
    ])

    referencia = StringField('Referencia', validators=[
        Optional(),
        Length(max=200, message='La referencia no debe superar los 200 caracteres')
    ])

    resumen = TextAreaField('Resumen y recomendación', validators=[
        DataRequired(message='El resumen es requerido'),
        Length(min=30, max=600, message='El resumen debe tener entre 30 y 600 caracteres')
    ])

    enviar = SubmitField('Guardar boletín')
