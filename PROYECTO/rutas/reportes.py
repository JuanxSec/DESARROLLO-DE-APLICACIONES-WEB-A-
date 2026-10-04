"""Reportes con exportación a CSV, JSON y PDF (Semana 15)."""

import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

from flask import Response, abort, render_template, request
from flask_login import login_required

from extensiones import app
from modelos.bitacora import registrar
from modelos.reporte import datos_reporte
from rutas.comun import filtro_dinero, filtro_fecha


def rango_reporte():
    """Lee las fechas del filtro; por defecto, desde el primer día del año."""
    hoy = date.today()
    try:
        desde = date.fromisoformat(request.args.get('desde', ''))
    except ValueError:
        desde = date(hoy.year, 1, 1)
    try:
        hasta = date.fromisoformat(request.args.get('hasta', ''))
    except ValueError:
        hasta = hoy
    if hasta < desde:
        desde, hasta = hasta, desde
    return desde, hasta


@app.route('/reportes')
@login_required
def reportes():
    desde, hasta = rango_reporte()
    por_servicio, por_organizacion, por_mes, total = datos_reporte(desde, hasta)
    return render_template('reportes.html', titulo='Reportes', desde=desde, hasta=hasta,
                           por_servicio=por_servicio, por_organizacion=por_organizacion,
                           por_mes=por_mes, total=total)


def a_texto(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


@app.route('/reportes/exportar/<formato>')
@login_required
def exportar_reporte(formato):
    desde, hasta = rango_reporte()
    por_servicio, _, _, total = datos_reporte(desde, hasta)
    nombre = 'reporte_servicios_%s_%s' % (desde.isoformat(), hasta.isoformat())
    registrar('EXPORTAR', 'Reportes', formato.upper() + ' ' + desde.isoformat() + ' a ' + hasta.isoformat())

    if formato == 'csv':
        salida = io.StringIO()
        escritor = csv.writer(salida)
        escritor.writerow(['Servicio', 'Categoría', 'Suscripciones', 'Cupos', 'Ingresos (USD)'])
        for fila in por_servicio:
            escritor.writerow([fila['servicio'], fila['categoria'], fila['suscripciones'],
                               fila['cupos'], '%.2f' % float(fila['ingresos'] or 0)])
        escritor.writerow(['TOTAL', '', '', '', '%.2f' % float(total)])
        # El BOM permite que Excel abra el archivo con tildes correctas.
        return Response('﻿' + salida.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=' + nombre + '.csv'})

    if formato == 'json':
        cuerpo = {'desde': desde.isoformat(), 'hasta': hasta.isoformat(), 'total': float(total),
                  'servicios': [{k: a_texto(v) for k, v in fila.items()} for fila in por_servicio]}
        return Response(json.dumps(cuerpo, ensure_ascii=False, indent=2), mimetype='application/json',
                        headers={'Content-Disposition': 'attachment; filename=' + nombre + '.json'})

    if formato == 'pdf':
        filas = [[f['servicio'], f['categoria'], str(f['suscripciones']), str(f['cupos']),
                  filtro_dinero(f['ingresos'])] for f in por_servicio]
        filas.append(['TOTAL', '', '', '', filtro_dinero(total)])
        contenido = generar_pdf('Reporte de servicios contratados',
                                ['Periodo: ' + filtro_fecha(desde) + ' al ' + filtro_fecha(hasta)],
                                ['Servicio', 'Categoría', 'Suscripciones', 'Cupos', 'Ingresos (USD)'], filas)
        return Response(contenido, mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename=' + nombre + '.pdf'})

    abort(404)


def generar_pdf(titulo, lineas, encabezados, filas):
    """Arma un PDF con reportlab: título, datos de cabecera y una tabla."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    memoria = io.BytesIO()
    documento = SimpleDocTemplate(memoria, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                  topMargin=1.8 * cm, bottomMargin=1.8 * cm, title=titulo,
                                  author='JuansecCTI')
    estilos = getSampleStyleSheet()
    partes = [Paragraph('<b>JuansecCTI</b> - Servicios de ciberinteligencia', estilos['Normal']),
              Spacer(1, 6), Paragraph(titulo, estilos['Title'])]
    partes += [Paragraph(texto, estilos['Normal']) for texto in lineas]
    partes.append(Spacer(1, 12))
    tabla = Table([encabezados] + filas, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b1f3a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f1f5f9')]),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
    ]))
    partes.append(tabla)
    partes.append(Spacer(1, 16))
    partes.append(Paragraph('Generado el ' + datetime.now().strftime('%d/%m/%Y %H:%M') +
                            ' desde el sistema JuansecCTI.', estilos['Italic']))
    documento.build(partes)
    return memoria.getvalue()
