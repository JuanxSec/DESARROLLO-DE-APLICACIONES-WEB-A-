"""Gestión de las solicitudes recibidas desde la página pública."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensiones import app
from forms.solicitud_form import SolicitudForm
from modelos.base import cambiar_activo, consultar, ejecutar
from modelos.bitacora import registrar
from modelos.opciones import opciones_estados, opciones_productos
from modelos.solicitud import listar_solicitudes
from rutas.comun import pagina_pedida, paginar, texto_buscado, vista_pedida


@app.route('/solicitudes')
@login_required
def ver_solicitudes():
    ver, q = vista_pedida(), texto_buscado()
    estado = request.args.get('estado', type=int)
    registros, paginacion = paginar(listar_solicitudes(ver, q, estado), pagina_pedida())
    return render_template('solicitudes.html', titulo='Solicitudes', solicitudes=registros,
                           paginacion=paginacion, ver=ver, q=q, estado_filtro=estado,
                           estados=opciones_estados('solicitud'))


@app.route('/solicitudes/editar/<int:id_solicitud>', methods=['GET', 'POST'])
@login_required
def editar_solicitud(id_solicitud):
    solicitud = consultar('SELECT * FROM solicitudes WHERE id_solicitud = %s', (id_solicitud,), uno=True)
    if solicitud is None:
        abort(404)
    form = SolicitudForm(data=solicitud)
    form.id_producto.choices = opciones_productos()
    form.id_estado.choices = opciones_estados('solicitud')
    form.enviar.label.text = 'Actualizar solicitud'
    if form.validate_on_submit():
        ejecutar('UPDATE solicitudes SET nombre = %s, organizacion = %s, correo = %s, telefono = %s, '
                 '       id_producto = %s, id_estado = %s, mensaje = %s WHERE id_solicitud = %s',
                 (form.nombre.data.strip(), form.organizacion.data.strip(), form.correo.data.strip(),
                  form.telefono.data or None, form.id_producto.data, form.id_estado.data,
                  form.mensaje.data.strip(), id_solicitud))
        registrar('EDITAR', 'Solicitudes', form.organizacion.data.strip())
        flash('Solicitud actualizada correctamente.', 'success')
        return redirect(url_for('ver_solicitudes'))
    return render_template('formulario_solicitud.html', titulo='Gestionar solicitud', form=form,
                           solicitud=solicitud)


@app.route('/solicitudes/baja/<int:id_solicitud>', methods=['POST'])
@login_required
def baja_solicitud(id_solicitud):
    if cambiar_activo('solicitudes', 'id_solicitud', id_solicitud, False):
        registrar('BAJA', 'Solicitudes', 'ID ' + str(id_solicitud))
        flash('Solicitud archivada. Se conserva como histórico.', 'warning')
    return redirect(url_for('ver_solicitudes'))


@app.route('/solicitudes/reactivar/<int:id_solicitud>', methods=['POST'])
@login_required
def reactivar_solicitud(id_solicitud):
    if cambiar_activo('solicitudes', 'id_solicitud', id_solicitud, True):
        registrar('REACTIVAR', 'Solicitudes', 'ID ' + str(id_solicitud))
        flash('Solicitud reactivada.', 'success')
    return redirect(url_for('ver_solicitudes', ver='baja'))


@app.route('/solicitudes/eliminar/<int:id_solicitud>', methods=['POST'])
@login_required
def eliminar_solicitud(id_solicitud):
    if ejecutar('DELETE FROM solicitudes WHERE id_solicitud = %s', (id_solicitud,)):
        registrar('ELIMINAR', 'Solicitudes', 'ID ' + str(id_solicitud))
        flash('Solicitud eliminada definitivamente.', 'warning')
    else:
        flash('La solicitud no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_solicitudes'))
