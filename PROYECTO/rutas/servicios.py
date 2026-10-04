"""CRUD de servicios CTI con baja lógica."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import login_required

from extensiones import app
from forms.producto_form import ProductoForm
from modelos.base import cambiar_activo, consultar, contar, ejecutar, insertar
from modelos.bitacora import registrar
from modelos.opciones import opciones_categorias, opciones_estados, opciones_proveedores
from modelos.servicio import listar_productos
from rutas.comun import IMAGENES_SERVICIO, pagina_pedida, paginar, texto_buscado, vista_pedida


def cargar_opciones_producto(form):
    form.id_categoria.choices = opciones_categorias()
    form.id_estado.choices = opciones_estados('producto')
    form.id_proveedor.choices = opciones_proveedores()
    form.imagen.choices = IMAGENES_SERVICIO


@app.route('/productos')
@login_required
def ver_productos():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_productos(ver, q), pagina_pedida())
    return render_template('productos.html', titulo='Servicios CTI', productos=registros,
                           paginacion=paginacion, ver=ver, q=q)


@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    form = ProductoForm()
    cargar_opciones_producto(form)
    if form.validate_on_submit():
        insertar(
            'INSERT INTO productos (nombre, id_categoria, id_estado, precio, stock, '
            '                       descripcion, id_proveedor, imagen) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (form.nombre.data.strip(), form.id_categoria.data, form.id_estado.data, form.precio.data,
             form.stock.data, form.descripcion.data.strip(), form.id_proveedor.data, form.imagen.data)
        )
        registrar('CREAR', 'Servicios', form.nombre.data.strip())
        flash('Servicio "' + form.nombre.data.strip() + '" agregado correctamente.', 'success')
        return redirect(url_for('ver_productos'))
    return render_template('formulario_producto.html', titulo='Nuevo servicio', form=form, producto=None)


@app.route('/productos/editar/<int:id_producto>', methods=['GET', 'POST'])
@login_required
def editar_producto(id_producto):
    producto = consultar('SELECT * FROM productos WHERE id_producto = %s', (id_producto,), uno=True)
    if producto is None:
        abort(404)

    form = ProductoForm(data=producto)
    cargar_opciones_producto(form)
    form.enviar.label.text = 'Actualizar servicio'

    if form.validate_on_submit():
        ejecutar(
            'UPDATE productos SET nombre = %s, id_categoria = %s, id_estado = %s, precio = %s, '
            '       stock = %s, descripcion = %s, id_proveedor = %s, imagen = %s '
            'WHERE id_producto = %s',
            (form.nombre.data.strip(), form.id_categoria.data, form.id_estado.data, form.precio.data,
             form.stock.data, form.descripcion.data.strip(), form.id_proveedor.data, form.imagen.data,
             id_producto)
        )
        registrar('EDITAR', 'Servicios', form.nombre.data.strip())
        flash('Servicio "' + form.nombre.data.strip() + '" actualizado correctamente.', 'success')
        return redirect(url_for('ver_productos'))

    return render_template('formulario_producto.html', titulo='Editar servicio', form=form,
                           producto=producto)


@app.route('/productos/baja/<int:id_producto>', methods=['POST'])
@login_required
def baja_producto(id_producto):
    """Baja lógica: el servicio sale del catálogo pero se conserva en la base."""
    if cambiar_activo('productos', 'id_producto', id_producto, False):
        registrar('BAJA', 'Servicios', 'ID ' + str(id_producto))
        flash('Servicio dado de baja. El registro se conserva como histórico.', 'warning')
    else:
        flash('El servicio no existe.', 'danger')
    return redirect(url_for('ver_productos'))


@app.route('/productos/reactivar/<int:id_producto>', methods=['POST'])
@login_required
def reactivar_producto(id_producto):
    if cambiar_activo('productos', 'id_producto', id_producto, True):
        registrar('REACTIVAR', 'Servicios', 'ID ' + str(id_producto))
        flash('Servicio reactivado correctamente.', 'success')
    else:
        flash('El servicio no existe.', 'danger')
    return redirect(url_for('ver_productos', ver='baja'))


@app.route('/productos/eliminar/<int:id_producto>', methods=['POST'])
@login_required
def eliminar_producto(id_producto):
    """Borrado definitivo con DELETE, el que piden las guías de la Semana 13."""
    if contar('SELECT COUNT(*) AS t FROM detalle_factura WHERE id_producto = %s', (id_producto,)) or \
            contar('SELECT COUNT(*) AS t FROM solicitudes WHERE id_producto = %s', (id_producto,)):
        flash('No se puede eliminar: el servicio está en una suscripción o una solicitud. '
              'Use "Dar de baja" para conservar el histórico.', 'danger')
        return redirect(url_for('ver_productos'))

    if ejecutar('DELETE FROM productos WHERE id_producto = %s', (id_producto,)):
        registrar('ELIMINAR', 'Servicios', 'ID ' + str(id_producto))
        flash('Servicio eliminado definitivamente.', 'warning')
    else:
        flash('El servicio no existe o ya fue eliminado.', 'danger')
    return redirect(url_for('ver_productos'))
