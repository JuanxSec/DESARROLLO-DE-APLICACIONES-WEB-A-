"""CRUD de organizaciones con baja lógica."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import login_required

from extensiones import app
from forms.cliente_form import ClienteForm
from modelos.base import cambiar_activo, consultar, contar, ejecutar, insertar
from modelos.bitacora import registrar
from modelos.opciones import opciones_nombre_servicios, opciones_parroquias, opciones_sectores
from modelos.organizacion import listar_clientes, ruc_repetido
from rutas.comun import pagina_pedida, paginar, texto_buscado, vista_pedida


def cargar_opciones_cliente(form, actual=None):
    form.id_sector.choices = opciones_sectores()
    form.id_parroquia.choices = opciones_parroquias()
    form.servicio.choices = opciones_nombre_servicios()
    # Un registro antiguo puede tener un servicio que ya no está en el catálogo:
    # se conserva como opción para que se pueda editar sin perder el dato.
    if actual and actual not in [valor for valor, _ in form.servicio.choices]:
        form.servicio.choices.insert(0, (actual, actual))


@app.route('/clientes')
@login_required
def ver_clientes():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_clientes(ver, q), pagina_pedida())
    return render_template('clientes.html', titulo='Organizaciones', clientes=registros,
                           paginacion=paginacion, total_clientes=paginacion['total'], ver=ver, q=q)


@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    form = ClienteForm()
    cargar_opciones_cliente(form)
    if form.validate_on_submit():
        if ruc_repetido(form.ruc.data):
            form.ruc.errors.append('Ya existe una organización con ese RUC')
        else:
            insertar(
                'INSERT INTO clientes (nombre, ruc, id_sector, id_parroquia, servicio, correo, telefono) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (form.nombre.data.strip(), form.ruc.data or None, form.id_sector.data,
                 form.id_parroquia.data, form.servicio.data, form.correo.data.strip(),
                 form.telefono.data or None)
            )
            registrar('CREAR', 'Organizaciones', form.nombre.data.strip())
            flash('Organización "' + form.nombre.data.strip() + '" agregada correctamente.', 'success')
            return redirect(url_for('ver_clientes'))
    return render_template('formulario_cliente.html', titulo='Nueva organización', form=form, cliente=None)


@app.route('/clientes/editar/<int:id_cliente>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id_cliente):
    cliente = consultar('SELECT * FROM clientes WHERE id_cliente = %s', (id_cliente,), uno=True)
    if cliente is None:
        abort(404)

    form = ClienteForm(data=cliente)
    cargar_opciones_cliente(form, cliente['servicio'])
    form.enviar.label.text = 'Actualizar organización'

    if form.validate_on_submit():
        if ruc_repetido(form.ruc.data, id_cliente):
            form.ruc.errors.append('Ya existe una organización con ese RUC')
        else:
            ejecutar(
                'UPDATE clientes SET nombre = %s, ruc = %s, id_sector = %s, id_parroquia = %s, '
                '       servicio = %s, correo = %s, telefono = %s '
                'WHERE id_cliente = %s',
                (form.nombre.data.strip(), form.ruc.data or None, form.id_sector.data,
                 form.id_parroquia.data, form.servicio.data, form.correo.data.strip(),
                 form.telefono.data or None, id_cliente)
            )
            registrar('EDITAR', 'Organizaciones', form.nombre.data.strip())
            flash('Organización "' + form.nombre.data.strip() + '" actualizada correctamente.', 'success')
            return redirect(url_for('ver_clientes'))

    return render_template('formulario_cliente.html', titulo='Editar organización', form=form,
                           cliente=cliente)


@app.route('/clientes/baja/<int:id_cliente>', methods=['POST'])
@login_required
def baja_cliente(id_cliente):
    if cambiar_activo('clientes', 'id_cliente', id_cliente, False):
        registrar('BAJA', 'Organizaciones', 'ID ' + str(id_cliente))
        flash('Organización dada de baja. El registro se conserva como histórico.', 'warning')
    else:
        flash('La organización no existe.', 'danger')
    return redirect(url_for('ver_clientes'))


@app.route('/clientes/reactivar/<int:id_cliente>', methods=['POST'])
@login_required
def reactivar_cliente(id_cliente):
    if cambiar_activo('clientes', 'id_cliente', id_cliente, True):
        registrar('REACTIVAR', 'Organizaciones', 'ID ' + str(id_cliente))
        flash('Organización reactivada correctamente.', 'success')
    else:
        flash('La organización no existe.', 'danger')
    return redirect(url_for('ver_clientes', ver='baja'))


@app.route('/clientes/eliminar/<int:id_cliente>', methods=['POST'])
@login_required
def eliminar_cliente(id_cliente):
    """Borrado definitivo con DELETE, el que piden las guías de la Semana 13."""
    if contar('SELECT COUNT(*) AS t FROM facturas WHERE id_cliente = %s', (id_cliente,)):
        flash('No se puede eliminar: la organización tiene suscripciones registradas. '
              'Use "Dar de baja" para conservar el histórico.', 'danger')
        return redirect(url_for('ver_clientes'))

    if ejecutar('DELETE FROM clientes WHERE id_cliente = %s', (id_cliente,)):
        registrar('ELIMINAR', 'Organizaciones', 'ID ' + str(id_cliente))
        flash('Organización eliminada definitivamente.', 'warning')
    else:
        flash('La organización no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_clientes'))
