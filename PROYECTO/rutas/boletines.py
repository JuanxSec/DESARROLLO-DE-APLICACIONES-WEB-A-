"""CRUD de boletines con baja lógica."""

from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensiones import app
from forms.boletin_form import BoletinForm
from modelos.base import cambiar_activo, consultar, ejecutar, insertar
from modelos.bitacora import registrar
from modelos.boletin import listar_boletines
from modelos.opciones import opciones_categorias, opciones_proveedores
from rutas.comun import pagina_pedida, paginar, texto_buscado, vista_pedida


def cargar_opciones_boletin(form):
    form.id_categoria.choices = opciones_categorias()
    form.id_proveedor.choices = opciones_proveedores()


@app.route('/boletines')
@login_required
def ver_boletines():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_boletines(ver, q), pagina_pedida())
    return render_template('boletines.html', titulo='Boletines', boletines=registros,
                           paginacion=paginacion, ver=ver, q=q)


@app.route('/boletines/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_boletin():
    form = BoletinForm()
    cargar_opciones_boletin(form)
    if request.method == 'GET':
        form.fecha.data = date.today()
    if form.validate_on_submit():
        insertar('INSERT INTO boletines (titulo, resumen, nivel, referencia, fecha, id_categoria, id_proveedor) '
                 'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                 (form.titulo.data.strip(), form.resumen.data.strip(), form.nivel.data,
                  form.referencia.data or None, form.fecha.data, form.id_categoria.data, form.id_proveedor.data))
        registrar('CREAR', 'Boletines', form.titulo.data.strip())
        flash('Boletín publicado. Ya aparece en la página principal.', 'success')
        return redirect(url_for('ver_boletines'))
    return render_template('formulario_boletin.html', titulo='Nuevo boletín', form=form, boletin=None)


@app.route('/boletines/editar/<int:id_boletin>', methods=['GET', 'POST'])
@login_required
def editar_boletin(id_boletin):
    boletin = consultar('SELECT * FROM boletines WHERE id_boletin = %s', (id_boletin,), uno=True)
    if boletin is None:
        abort(404)
    form = BoletinForm(data=boletin)
    cargar_opciones_boletin(form)
    form.enviar.label.text = 'Actualizar boletín'
    if form.validate_on_submit():
        ejecutar('UPDATE boletines SET titulo = %s, resumen = %s, nivel = %s, referencia = %s, fecha = %s, '
                 '       id_categoria = %s, id_proveedor = %s WHERE id_boletin = %s',
                 (form.titulo.data.strip(), form.resumen.data.strip(), form.nivel.data,
                  form.referencia.data or None, form.fecha.data, form.id_categoria.data,
                  form.id_proveedor.data, id_boletin))
        registrar('EDITAR', 'Boletines', form.titulo.data.strip())
        flash('Boletín actualizado correctamente.', 'success')
        return redirect(url_for('ver_boletines'))
    return render_template('formulario_boletin.html', titulo='Editar boletín', form=form, boletin=boletin)


@app.route('/boletines/baja/<int:id_boletin>', methods=['POST'])
@login_required
def baja_boletin(id_boletin):
    if cambiar_activo('boletines', 'id_boletin', id_boletin, False):
        registrar('BAJA', 'Boletines', 'ID ' + str(id_boletin))
        flash('Boletín retirado de la página pública. Se conserva como histórico.', 'warning')
    return redirect(url_for('ver_boletines'))


@app.route('/boletines/reactivar/<int:id_boletin>', methods=['POST'])
@login_required
def reactivar_boletin(id_boletin):
    if cambiar_activo('boletines', 'id_boletin', id_boletin, True):
        registrar('REACTIVAR', 'Boletines', 'ID ' + str(id_boletin))
        flash('Boletín publicado nuevamente.', 'success')
    return redirect(url_for('ver_boletines', ver='baja'))


@app.route('/boletines/eliminar/<int:id_boletin>', methods=['POST'])
@login_required
def eliminar_boletin(id_boletin):
    if ejecutar('DELETE FROM boletines WHERE id_boletin = %s', (id_boletin,)):
        registrar('ELIMINAR', 'Boletines', 'ID ' + str(id_boletin))
        flash('Boletín eliminado definitivamente.', 'warning')
    else:
        flash('El boletín no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_boletines'))
