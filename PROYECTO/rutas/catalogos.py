"""CRUD de los catálogos (tablas padre)."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import login_required

from extensiones import app
from forms.catalogo_form import CatalogoForm
from modelos.base import consultar, ejecutar, insertar
from modelos.bitacora import registrar
from modelos.catalogo import CATALOGOS, catalogo_pedido, nombre_repetido, usos_catalogo
from rutas.comun import texto_buscado


@app.route('/catalogos')
@app.route('/catalogos/<clave>')
@login_required
def ver_catalogos(clave='categorias'):
    cat = catalogo_pedido(clave)
    q = texto_buscado()
    usos = ' + '.join('(SELECT COUNT(*) FROM ' + hija + ' h WHERE h.' + columna + ' = c.' + cat['id'] + ')'
                      for hija, columna in cat['usos'])
    sql = ('SELECT c.' + cat['id'] + ' AS id, c.nombre, c.descripcion, ' + usos + ' AS usos '
           'FROM ' + cat['tabla'] + ' c ')
    params = ()
    if q:
        sql += 'WHERE LOWER(c.nombre) LIKE LOWER(%s) '
        params = ('%' + q + '%',)
    registros = consultar(sql + 'ORDER BY c.nombre', params)
    return render_template('catalogos.html', titulo='Catálogos', catalogos=CATALOGOS, clave=clave,
                           cat=cat, registros=registros, q=q)


@app.route('/catalogos/<clave>/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_catalogo(clave):
    cat = catalogo_pedido(clave)
    form = CatalogoForm()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        if nombre_repetido(cat, nombre):
            form.nombre.errors.append('Ya existe un registro con ese nombre')
        else:
            insertar('INSERT INTO ' + cat['tabla'] + ' (nombre, descripcion) VALUES (%s, %s)',
                     (nombre, form.descripcion.data.strip()))
            registrar('CREAR', 'Catálogos', cat['singular'].capitalize() + ' ' + nombre)
            flash('Registro "' + nombre + '" agregado al catálogo.', 'success')
            return redirect(url_for('ver_catalogos', clave=clave))
    return render_template('formulario_catalogo.html', titulo='Catálogos', form=form, cat=cat,
                           clave=clave, registro=None)


@app.route('/catalogos/<clave>/editar/<int:id_registro>', methods=['GET', 'POST'])
@login_required
def editar_catalogo(clave, id_registro):
    cat = catalogo_pedido(clave)
    registro = consultar('SELECT ' + cat['id'] + ' AS id, nombre, descripcion FROM ' + cat['tabla'] +
                         ' WHERE ' + cat['id'] + ' = %s', (id_registro,), uno=True)
    if registro is None:
        abort(404)
    form = CatalogoForm(data=registro)
    form.enviar.label.text = 'Actualizar'
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        if nombre_repetido(cat, nombre, id_registro):
            form.nombre.errors.append('Ya existe un registro con ese nombre')
        else:
            ejecutar('UPDATE ' + cat['tabla'] + ' SET nombre = %s, descripcion = %s WHERE ' + cat['id'] + ' = %s',
                     (nombre, form.descripcion.data.strip(), id_registro))
            registrar('EDITAR', 'Catálogos', cat['singular'].capitalize() + ' ' + nombre)
            flash('Registro "' + nombre + '" actualizado correctamente.', 'success')
            return redirect(url_for('ver_catalogos', clave=clave))
    return render_template('formulario_catalogo.html', titulo='Catálogos', form=form, cat=cat,
                           clave=clave, registro=registro)


@app.route('/catalogos/<clave>/eliminar/<int:id_registro>', methods=['POST'])
@login_required
def eliminar_catalogo(clave, id_registro):
    cat = catalogo_pedido(clave)
    usados = usos_catalogo(cat, id_registro)
    if usados:
        flash('No se puede eliminar: lo usan ' + str(usados) + ' registro(s) relacionados. '
              'La clave foránea protege la integridad de los datos.', 'danger')
    elif ejecutar('DELETE FROM ' + cat['tabla'] + ' WHERE ' + cat['id'] + ' = %s', (id_registro,)):
        registrar('ELIMINAR', 'Catálogos', cat['singular'].capitalize() + ' ID ' + str(id_registro))
        flash('Registro eliminado definitivamente.', 'warning')
    else:
        flash('El registro no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_catalogos', clave=clave))
