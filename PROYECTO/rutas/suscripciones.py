"""CRUD de suscripciones, detalle con control de cupos, comprobante y PDF."""

from datetime import date, datetime
from decimal import Decimal

from flask import Response, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensiones import app
from forms.detalle_form import DetalleFacturaForm
from forms.facturacion_form import FacturacionForm
from modelos.base import cambiar_activo, consultar, ejecutar, insertar
from modelos.bitacora import registrar
from modelos.opciones import opciones_clientes, opciones_estados, opciones_productos
from modelos.suscripcion import (datos_factura, lineas_factura, listar_facturas, recalcular_total, siguiente_codigo)
from rutas.comun import (filtro_dinero, filtro_fecha, pagina_pedida, paginar, texto_buscado, vista_pedida)
from rutas.reportes import generar_pdf


def cargar_opciones_factura(form):
    form.id_cliente.choices = opciones_clientes()
    form.id_estado.choices = opciones_estados('factura')


@app.route('/facturacion')
@login_required
def ver_facturacion():
    ver, q = vista_pedida(), texto_buscado()
    registros, paginacion = paginar(listar_facturas(ver, q), pagina_pedida())
    return render_template('facturacion.html', titulo='Suscripciones', facturas=registros,
                           paginacion=paginacion, total_facturas=paginacion['total'], ver=ver, q=q)


@app.route('/facturacion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_factura():
    form = FacturacionForm()
    cargar_opciones_factura(form)
    if request.method == 'GET':
        form.codigo.data = siguiente_codigo()
        form.fecha.data = date.today()

    if form.validate_on_submit():
        if consultar('SELECT id_factura FROM facturas WHERE codigo = %s', (form.codigo.data,), uno=True):
            form.codigo.errors.append('Ya existe una suscripción con ese código')
        else:
            nuevo_id = insertar(
                'INSERT INTO facturas (codigo, id_cliente, id_estado, servicio, fecha) '
                'VALUES (%s, %s, %s, %s, %s)',
                (form.codigo.data.upper(), form.id_cliente.data, form.id_estado.data,
                 form.servicio.data.strip(), form.fecha.data))
            registrar('CREAR', 'Suscripciones', form.codigo.data.upper())
            flash('Suscripción ' + form.codigo.data.upper() + ' registrada. Agregue ahora los servicios '
                  'que incluye.', 'success')
            return redirect(url_for('detalle_factura', id_factura=nuevo_id))
    return render_template('formulario_facturacion.html', titulo='Nueva suscripción', form=form, factura=None)


@app.route('/facturacion/editar/<int:id_factura>', methods=['GET', 'POST'])
@login_required
def editar_factura(id_factura):
    factura = consultar('SELECT * FROM facturas WHERE id_factura = %s', (id_factura,), uno=True)
    if factura is None:
        abort(404)

    form = FacturacionForm(data=factura)
    cargar_opciones_factura(form)
    form.enviar.label.text = 'Actualizar suscripción'

    if form.validate_on_submit():
        repetida = consultar('SELECT id_factura FROM facturas WHERE codigo = %s', (form.codigo.data,), uno=True)
        if repetida and repetida['id_factura'] != id_factura:
            form.codigo.errors.append('Ya existe una suscripción con ese código')
        else:
            ejecutar('UPDATE facturas SET codigo = %s, id_cliente = %s, id_estado = %s, servicio = %s, fecha = %s '
                     'WHERE id_factura = %s',
                     (form.codigo.data.upper(), form.id_cliente.data, form.id_estado.data,
                      form.servicio.data.strip(), form.fecha.data, id_factura))
            registrar('EDITAR', 'Suscripciones', form.codigo.data.upper())
            flash('Suscripción ' + form.codigo.data.upper() + ' actualizada correctamente.', 'success')
            return redirect(url_for('ver_facturacion'))

    return render_template('formulario_facturacion.html', titulo='Editar suscripción', form=form,
                           factura=factura)


@app.route('/facturacion/baja/<int:id_factura>', methods=['POST'])
@login_required
def baja_factura(id_factura):
    """Baja lógica: lo correcto en facturación, porque una factura no se borra."""
    if cambiar_activo('facturas', 'id_factura', id_factura, False):
        registrar('BAJA', 'Suscripciones', 'ID ' + str(id_factura))
        flash('Suscripción dada de baja. La factura se conserva como histórico.', 'warning')
    else:
        flash('La suscripción no existe.', 'danger')
    return redirect(url_for('ver_facturacion'))


@app.route('/facturacion/reactivar/<int:id_factura>', methods=['POST'])
@login_required
def reactivar_factura(id_factura):
    if cambiar_activo('facturas', 'id_factura', id_factura, True):
        registrar('REACTIVAR', 'Suscripciones', 'ID ' + str(id_factura))
        flash('Suscripción reactivada correctamente.', 'success')
    else:
        flash('La suscripción no existe.', 'danger')
    return redirect(url_for('ver_facturacion', ver='baja'))


@app.route('/facturacion/eliminar/<int:id_factura>', methods=['POST'])
@login_required
def eliminar_factura(id_factura):
    """Borrado definitivo con DELETE: devuelve los cupos y elimina el detalle en cascada."""
    for linea in consultar('SELECT id_producto, cantidad FROM detalle_factura WHERE id_factura = %s',
                           (id_factura,)):
        ejecutar('UPDATE productos SET stock = stock + %s WHERE id_producto = %s',
                 (linea['cantidad'], linea['id_producto']))
    if ejecutar('DELETE FROM facturas WHERE id_factura = %s', (id_factura,)):
        registrar('ELIMINAR', 'Suscripciones', 'ID ' + str(id_factura))
        flash('Suscripción eliminada junto con su detalle. Los cupos volvieron al catálogo.', 'warning')
    else:
        flash('La suscripción no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('ver_facturacion'))


@app.route('/facturacion/detalle/<int:id_factura>', methods=['GET', 'POST'])
@login_required
def detalle_factura(id_factura):
    """Gestiona la relación muchos a muchos entre suscripciones y servicios."""
    factura = datos_factura(id_factura)
    if factura is None:
        abort(404)

    form = DetalleFacturaForm()
    form.id_producto.choices = opciones_productos(con_cupos=True)

    if form.validate_on_submit():
        servicio = consultar('SELECT nombre, stock, precio FROM productos WHERE id_producto = %s',
                             (form.id_producto.data,), uno=True)
        repetido = consultar('SELECT id_detalle FROM detalle_factura WHERE id_factura = %s AND id_producto = %s',
                             (id_factura, form.id_producto.data), uno=True)
        if servicio is None:
            flash('El servicio seleccionado no existe.', 'danger')
        elif repetido:
            flash('Ese servicio ya forma parte del detalle de la suscripción.', 'danger')
        elif form.cantidad.data > servicio['stock']:
            # Control de cupos: no se puede vender más de lo disponible.
            flash('No hay cupos suficientes de "' + servicio['nombre'] + '": se pidieron ' +
                  str(form.cantidad.data) + ' y quedan ' + str(servicio['stock']) + '.', 'danger')
        else:
            precio = form.precio_unitario.data if form.precio_unitario.data is not None else servicio['precio']
            ejecutar('INSERT INTO detalle_factura (id_factura, id_producto, cantidad, precio_unitario) '
                     'VALUES (%s, %s, %s, %s)', (id_factura, form.id_producto.data, form.cantidad.data, precio))
            ejecutar('UPDATE productos SET stock = stock - %s WHERE id_producto = %s',
                     (form.cantidad.data, form.id_producto.data))
            recalcular_total(id_factura)
            registrar('CREAR', 'Suscripciones', 'Detalle de ' + factura['codigo'] + ': ' + servicio['nombre'])
            flash('Servicio agregado. Se descontaron ' + str(form.cantidad.data) + ' cupo(s) de "' +
                  servicio['nombre'] + '".', 'success')
        return redirect(url_for('detalle_factura', id_factura=id_factura))

    return render_template('detalle_factura.html', titulo='Detalle de la suscripción',
                           factura=factura, lineas=lineas_factura(id_factura), form=form)


@app.route('/facturacion/detalle/<int:id_factura>/eliminar/<int:id_detalle>', methods=['POST'])
@login_required
def eliminar_detalle(id_factura, id_detalle):
    linea = consultar('SELECT id_producto, cantidad FROM detalle_factura WHERE id_detalle = %s AND id_factura = %s',
                      (id_detalle, id_factura), uno=True)
    if linea and ejecutar('DELETE FROM detalle_factura WHERE id_detalle = %s AND id_factura = %s',
                          (id_detalle, id_factura)):
        ejecutar('UPDATE productos SET stock = stock + %s WHERE id_producto = %s',
                 (linea['cantidad'], linea['id_producto']))
        recalcular_total(id_factura)
        registrar('ELIMINAR', 'Suscripciones', 'Línea ' + str(id_detalle) + ' de la factura ' + str(id_factura))
        flash('Línea quitada del detalle. Los cupos volvieron al servicio.', 'warning')
    else:
        flash('La línea no existe o ya fue eliminada.', 'danger')
    return redirect(url_for('detalle_factura', id_factura=id_factura))


@app.route('/facturacion/<int:id_factura>/comprobante')
@login_required
def comprobante_factura(id_factura):
    """Comprobante imprimible de la suscripción (se imprime o guarda como PDF)."""
    factura = datos_factura(id_factura)
    if factura is None:
        abort(404)
    lineas = lineas_factura(id_factura)
    subtotal = sum(Decimal(str(l['subtotal'])) for l in lineas)
    return render_template('comprobante.html', titulo='Comprobante ' + factura['codigo'],
                           factura=factura, lineas=lineas, subtotal=subtotal,
                           emitido=datetime.now())


@app.route('/facturacion/<int:id_factura>/pdf')
@login_required
def pdf_factura(id_factura):
    factura = datos_factura(id_factura)
    if factura is None:
        abort(404)
    lineas = lineas_factura(id_factura)
    filas = [[str(i + 1), l['producto'], str(l['cantidad']), filtro_dinero(l['precio_unitario']),
              filtro_dinero(l['subtotal'])] for i, l in enumerate(lineas)]
    filas.append(['', '', '', 'TOTAL', filtro_dinero(factura['total'])])
    contenido = generar_pdf(
        'Comprobante de suscripción ' + factura['codigo'],
        ['Organización: ' + factura['cliente'] + ('  -  RUC ' + factura['ruc'] if factura['ruc'] else ''),
         'Ubicación: ' + factura['ubicacion'],
         'Fecha de emisión: ' + filtro_fecha(factura['fecha']) + '   Estado: ' + factura['estado']],
        ['#', 'Servicio', 'Cant.', 'P. unitario (USD)', 'Subtotal (USD)'], filas)
    registrar('EXPORTAR', 'Suscripciones', 'PDF de ' + factura['codigo'])
    return Response(contenido, mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment; filename=' + factura['codigo'] + '.pdf'})
