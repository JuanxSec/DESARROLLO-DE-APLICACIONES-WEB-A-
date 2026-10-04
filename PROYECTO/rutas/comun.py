"""Utilidades compartidas por las vistas: paginación, filtros, roles y datos globales de Jinja2."""

import math
from datetime import date
from functools import wraps

from flask import flash, redirect, request, url_for
from flask_login import current_user

from extensiones import app
from forms.boletin_form import NIVELES
from modelos.base import VISTAS, contar


titulo_sitio = 'JuansecCTI'


POR_PAGINA = 8


# Datos de la página pública que no cambian con la base de datos. Se envían a
# la plantilla como lista de diccionarios y se recorren con un for de Jinja2.
PILARES = [
    {'icono': 'bi-binoculars', 'titulo': 'Recolección',
     'texto': 'Fuentes abiertas, comunidades de investigación, avisos de fabricantes y plataformas de amenazas.'},
    {'icono': 'bi-diagram-3', 'titulo': 'Análisis',
     'texto': 'Correlación de indicadores y técnicas de ataque con la realidad de cada organización.'},
    {'icono': 'bi-megaphone', 'titulo': 'Difusión',
     'texto': 'Boletines y alertas en lenguaje claro, con recomendaciones que se pueden aplicar el mismo día.'},
    {'icono': 'bi-arrow-repeat', 'titulo': 'Retroalimentación',
     'texto': 'Cada incidente atendido mejora las reglas de detección y las fuentes que se vigilan.'},
]


IMAGENES_SERVICIO = [
    ('servicio-boletin.jpg', 'Boletín'),
    ('servicio-alerta.jpg', 'Alerta'),
    ('servicio-noticias.jpg', 'Noticias'),
    ('servicio-informe.jpg', 'Informe'),
    ('servicio-capacitacion.jpg', 'Capacitación'),
    ('servicio-darkweb.jpg', 'Dark web'),
    ('servicio-marca.jpg', 'Protección de marca'),
    ('servicio-infraestructura.jpg', 'Superficie de ataque'),
    ('servicio-threat-hunting.jpg', 'Threat hunting'),
    ('servicio-incidentes.jpg', 'Respuesta a incidentes'),
]


NIVEL_ETIQUETA = dict(NIVELES)


NIVEL_COLOR = {'Critico': 'danger', 'Alto': 'warning', 'Medio': 'info', 'Bajo': 'secondary'}


def paginar(registros, pagina):
    """Divide una lista en páginas de POR_PAGINA elementos."""
    total = len(registros)
    paginas = max(1, math.ceil(total / POR_PAGINA))
    pagina = min(max(1, pagina), paginas)
    inicio = (pagina - 1) * POR_PAGINA
    return registros[inicio:inicio + POR_PAGINA], {'pagina': pagina, 'paginas': paginas, 'total': total}


def pagina_pedida():
    try:
        return int(request.args.get('pagina', 1))
    except ValueError:
        return 1


def vista_pedida():
    """Lee el filtro ?ver= de la URL y lo valida contra la lista de vistas."""
    ver = request.args.get('ver', 'activos')
    return ver if ver in VISTAS else 'activos'


def texto_buscado():
    return (request.args.get('q') or '').strip()[:60]


def es_admin():
    return current_user.is_authenticated and current_user.rol == 'Administrador'


def solo_admin(vista):
    """Restringe una ruta al rol Administrador (gestión de usuarios y bitácora)."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not es_admin():
            flash('Esta opción está reservada al rol Administrador.', 'warning')
            return redirect(url_for('dashboard'))
        return vista(*args, **kwargs)
    return envoltura


@app.context_processor
def datos_globales():
    """Variables disponibles en todas las plantillas."""
    pendientes = 0
    if current_user.is_authenticated:
        try:
            pendientes = contar(
                'SELECT COUNT(*) AS t FROM solicitudes s '
                'INNER JOIN estados e ON e.id_estado = s.id_estado '
                "WHERE s.activo = TRUE AND e.nombre = 'Nueva'")
        except Exception:  # noqa: BLE001
            pendientes = 0
    return {
        'titulo_sitio': titulo_sitio,
        'anio_actual': date.today().year,
        'nivel_etiqueta': NIVEL_ETIQUETA,
        'nivel_color': NIVEL_COLOR,
        'es_admin': es_admin(),
        'solicitudes_nuevas': pendientes,
    }


@app.template_filter('dinero')
def filtro_dinero(valor):
    return '{:,.2f}'.format(float(valor or 0))


@app.template_filter('fecha')
def filtro_fecha(valor):
    if not valor:
        return ''
    if isinstance(valor, str):
        return valor[:10]
    return valor.strftime('%d/%m/%Y')
