"""CRUD de fuentes de inteligencia con baja lógica."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import login_required

from extensiones import app
from forms.proveedor_form import ProveedorForm
from modelos.base import cambiar_activo, consultar, ejecutar, insertar
from modelos.bitacora import registrar
from modelos.fuente import listar_proveedores
from modelos.opciones import opciones_tipos_proveedor
from rutas.comun import pagina_pedida, paginar, texto_buscado, vista_pedida


@app.route('/proveedores')
@login_required
def ver_proveedores():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_proveedores(ver, q), pagina_pedida())
    return render_template('proveedores.html', titulo='Fuentes de inteligencia', proveedores=registros,
                           paginacion=paginacion, ver=ver, q=q)


@app.route('/proveedores/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_proveedor():
    form = ProveedorForm()
    form.id_tipo.choices = opciones_tipos_proveedor()
    if form.validate_on_submit():
        insertar('INSERT INTO proveedores (nombre, id_tipo, aporte, correo, telefono) '
                 'VALUES (%s, %s, %s, %s, %s)',
                 (form.nombre.data.strip(), form.id_tipo.data, form.aporte.data.strip(),
                  form.correo.data or None, form.telefono.data or None))
        registrar('CREAR', 'Fuentes', form.nombre.data.strip())
        flash('Fuente "' + form.nombre.data.strip() + '" agregada correctamente.', 'success')
        return redirect(url_for('ver_proveedores'))
    return render_template('formulario_proveedor.html', titulo='Nueva fuente', form=form, proveedor=None)


@app.route('/proveedores/editar/<int:id_proveedor>', methods=['GET', 'POST'])
@login_required
def editar_proveedor(id_proveedor):
    proveedor = consultar('SELECT * FROM proveedores WHERE id_proveedor = %s', (id_proveedor,), uno=True)
    if proveedor is None:
        abort(404)

    form = ProveedorForm(data=proveedor)
    form.id_tipo.choices = opciones_tipos_proveedor()
    form.enviar.label.text = 'Actualizar fuente'

    if form.validate_on_submit():
        ejecutar('UPDATE proveedores SET nombre = %s, id_tipo = %s, aporte = %s, correo = %s, telefono = %s '
                 'WHERE id_proveedor = %s',
                 (form.nombre.data.strip(), form.id_tipo.data, form.aporte.data.strip(),
                  form.correo.data or None, form.telefono.data or None, id_proveedor))
        registrar('EDITAR', 'Fuentes', form.nombre.data.strip())
        flash('Fuente "' + form.nombre.data.strip() + '" actualizada correctamente.', 'success')
        return redirect(url_for('ver_proveedores'))

    return render_template('formulario_proveedor.html', titulo='Editar fuente', form=form,
                           proveedor=proveedor)


@app.route('/proveedores/baja/<int:id_proveedor>', methods=['POST'])
@login_required
def baja_proveedor(id_proveedor):
    if cambiar_activo('proveedores', 'id_proveedor', id_proveedor, False):
        registrar('BAJA', 'Fuentes', 'ID ' + str(id_proveedor))
        flash('Fuente dada de baja. El registro se conserva como histórico.', 'warning')
    else:
        flash('La fuente no existe.', 'danger')
    return redirect(url_for('ver_proveedores'))


@app.route('/proveedores/reactivar/<int:id_proveedor>', methods=['POST'])
@login_required
def reactivar_proveedor(id_proveedor):
    if cambiar_activo('proveedores', 'id_proveedor', id_proveedor, True):
        registrar('REACTIVAR', 'Fuentes', 'ID ' + str(id_proveedor))
        flash('Fuente reactivada correctamente.', 'success')
    else:
        flash('La fuente no existe.', 'danger')
    return redirect(url_for('ver_proveedores', ver='baja'))


@app.route('/proveedores/eliminar/<int:id_proveedor>', methods=['POST'])
@login_required
def eliminar_proveedor(id_proveedor):
    """Borrado definitivo con DELETE. Los servicios y boletines quedan sin fuente."""
    if ejecutar('DELETE FROM proveedores WHERE id_proveedor = %s', (id_proveedor,)):
        registrar('ELIMINAR', 'Fuentes', 'ID ' + str(id_proveedor))
        flash('Fuente eliminada. Los servicios asociados quedaron sin fuente asignada.', 'warning')
    else:
        flash('La fuente no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_proveedores'))
