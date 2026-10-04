"""Autenticación (Semana 14): registro, inicio y cierre de sesión con Flask-Login."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from extensiones import app, login_manager
from forms.login_form import LoginForm
from forms.usuario_form import UsuarioForm
from modelos.base import consultar, contar, id_por_nombre
from modelos.bitacora import registrar
from modelos.opciones import opciones_roles
from modelos.usuario import SQL_USUARIO, crear_usuario, datos_duplicados, usuario_desde_fila


@login_manager.user_loader
def load_user(user_id):
    """Reconstruye el usuario autenticado a partir de su identificador."""
    data = consultar(SQL_USUARIO + 'WHERE u.id = %s', (user_id,), uno=True)
    return usuario_desde_fila(data) if data else None


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = UsuarioForm()
    form.id_rol.choices = opciones_roles()
    # En el registro público el rol no se elige: se asigna el de Analista.
    # La única excepción es la primera cuenta del sistema, que queda como
    # Administrador para que alguien pueda gestionar usuarios y bitácora.
    id_analista = id_por_nombre('roles', 'id_rol', 'Analista')
    if contar('SELECT COUNT(*) AS t FROM usuarios') == 0:
        id_analista = id_por_nombre('roles', 'id_rol', 'Administrador')
    if request.method == 'GET':
        form.id_rol.data = id_analista

    if form.validate_on_submit():
        error = datos_duplicados(form)
        if error:
            flash(error, 'danger')
        else:
            crear_usuario(form, id_analista)
            registrar('CREAR', 'Usuarios', 'Registro de la cuenta ' + form.usuario.data)
            flash('Cuenta "' + form.usuario.data + '" creada correctamente. Ya puede iniciar sesión.', 'success')
            return redirect(url_for('login'))

    return render_template('registro.html', titulo='Crear cuenta', form=form, publico=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        # Se puede ingresar con el nombre de usuario o con el correo del perfil.
        data = consultar(SQL_USUARIO + 'WHERE u.usuario = %s OR p.correo = %s',
                         (form.usuario.data.strip(), form.usuario.data.strip()), uno=True)
        # La contraseña escrita nunca se compara directamente con la almacenada.
        if data and check_password_hash(data['password'], form.password.data):
            login_user(usuario_desde_fila(data), remember=form.recordar.data)
            registrar('LOGIN', 'Sesión', 'Inicio de sesión')
            flash('Bienvenido, ' + (data['nombre_completo'] or data['usuario']) + '.', 'success')
            siguiente = request.args.get('next')
            # Solo se aceptan rutas internas para evitar redirecciones abiertas.
            if not siguiente or not siguiente.startswith('/') or siguiente.startswith('//'):
                siguiente = url_for('dashboard')
            return redirect(siguiente)
        flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html', titulo='Iniciar sesión', form=form)


@app.route('/logout')
@login_required
def logout():
    nombre = current_user.usuario
    registrar('LOGOUT', 'Sesión', 'Cierre de sesión')
    logout_user()
    flash('Sesión cerrada correctamente. Hasta pronto, ' + nombre + '.', 'info')
    return redirect(url_for('login'))
