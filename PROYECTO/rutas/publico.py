"""Páginas públicas: portada, catálogo de servicios, boletines, solicitud y términos."""

from flask import flash, redirect, render_template, request, url_for

from extensiones import app
from forms.solicitud_form import SolicitudForm
from modelos.base import contar, id_por_nombre, insertar
from modelos.bitacora import registrar
from modelos.boletin import boletines_publicos
from modelos.opciones import opciones_categorias, opciones_estados, opciones_productos
from modelos.servicio import servicios_publicos
from rutas.comun import PILARES, texto_buscado


def formulario_solicitud():
    form = SolicitudForm()
    form.id_producto.choices = opciones_productos()
    form.id_estado.choices = opciones_estados('solicitud')
    return form


@app.route('/')
def inicio():
    # La portada es pública, así que no debe caerse si la base de datos aún no
    # responde: en ese caso se muestra sin el contenido dinámico.
    try:
        servicios = servicios_publicos(limite=6)
        boletines = boletines_publicos(limite=3)
        cifras = {
            'servicios': contar('SELECT COUNT(*) AS t FROM productos WHERE activo = TRUE'),
            'organizaciones': contar('SELECT COUNT(*) AS t FROM clientes WHERE activo = TRUE'),
            'boletines': contar('SELECT COUNT(*) AS t FROM boletines WHERE activo = TRUE'),
            'fuentes': contar('SELECT COUNT(*) AS t FROM proveedores WHERE activo = TRUE'),
        }
        form = formulario_solicitud()
    except Exception as error:  # noqa: BLE001
        app.logger.error('Portada sin base de datos: %s', error)
        servicios, boletines, cifras, form = [], [], None, None
    return render_template('index.html', titulo='Inicio', servicios=servicios,
                           boletines=boletines, cifras=cifras, pilares=PILARES, form=form)


@app.route('/servicios')
def catalogo_servicios():
    categoria = request.args.get('categoria', type=int)
    q = texto_buscado()
    return render_template('servicios.html', titulo='Servicios CTI',
                           servicios=servicios_publicos(categoria=categoria, q=q),
                           categorias=opciones_categorias(), categoria=categoria, q=q)


@app.route('/boletines-publicos')
def boletines_publicados():
    return render_template('boletines_publicos.html', titulo='Boletines',
                           boletines=boletines_publicos())


@app.route('/solicitar', methods=['GET', 'POST'])
def solicitar():
    """Formulario público de solicitud de información (se guarda en la base)."""
    form = formulario_solicitud()
    if request.method == 'GET' and request.args.get('servicio', type=int):
        form.id_producto.data = request.args.get('servicio', type=int)

    if form.validate_on_submit():
        id_nueva = id_por_nombre('estados', 'id_estado', 'Nueva', " AND ambito = 'solicitud'")
        insertar('INSERT INTO solicitudes (nombre, organizacion, correo, telefono, id_producto, '
                 'id_estado, mensaje) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                 (form.nombre.data.strip(), form.organizacion.data.strip(), form.correo.data.strip(),
                  form.telefono.data or None, form.id_producto.data, id_nueva, form.mensaje.data.strip()))
        registrar('CREAR', 'Solicitudes', 'Solicitud pública de ' + form.organizacion.data.strip())
        flash('Gracias, ' + form.nombre.data.split()[0] + '. Recibimos su solicitud y un analista '
              'le escribirá en menos de 24 horas.', 'success')
        return redirect(url_for('solicitar'))

    return render_template('solicitar.html', titulo='Solicitar información', form=form)


@app.route('/terminos')
def terminos():
    return render_template('terminos.html', titulo='Términos y privacidad')
