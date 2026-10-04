"""Usuarios, roles y bitácora (solo rol Administrador)."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensiones import app
from forms.usuario_form import UsuarioForm
from modelos.base import consultar, ejecutar
from modelos.bitacora import registrar
from modelos.opciones import opciones_roles
from modelos.usuario import crear_usuario, datos_duplicados
from rutas.comun import pagina_pedida, paginar, solo_admin


@app.route('/usuarios')
@login_required
@solo_admin
def ver_usuarios():
    usuarios = consultar(
        'SELECT u.id, u.usuario, r.nombre AS rol, p.nombre_completo, p.correo '
        'FROM usuarios u INNER JOIN roles r ON r.id_rol = u.id_rol '
        'LEFT JOIN perfiles_usuario p ON p.id_usuario = u.id ORDER BY u.id')
    return render_template('usuarios.html', titulo='Usuarios', usuarios=usuarios, roles=opciones_roles())


@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@solo_admin
def nuevo_usuario():
    form = UsuarioForm()
    form.id_rol.choices = opciones_roles()
    if form.validate_on_submit():
        error = datos_duplicados(form)
        if error:
            flash(error, 'danger')
        else:
            crear_usuario(form, form.id_rol.data)
            registrar('CREAR', 'Usuarios', form.usuario.data)
            flash('Usuario "' + form.usuario.data + '" creado correctamente.', 'success')
            return redirect(url_for('ver_usuarios'))
    return render_template('registro.html', titulo='Nuevo usuario', form=form, publico=False)


@app.route('/usuarios/rol/<int:id_usuario>', methods=['POST'])
@login_required
@solo_admin
def cambiar_rol(id_usuario):
    id_rol = request.form.get('id_rol', type=int)
    if id_usuario == current_user.id:
        flash('No puede cambiar su propio rol.', 'warning')
    elif id_rol and ejecutar('UPDATE usuarios SET id_rol = %s WHERE id = %s', (id_rol, id_usuario)):
        registrar('EDITAR', 'Usuarios', 'Rol del usuario ' + str(id_usuario))
        flash('Rol actualizado correctamente.', 'success')
    return redirect(url_for('ver_usuarios'))


@app.route('/usuarios/eliminar/<int:id_usuario>', methods=['POST'])
@login_required
@solo_admin
def eliminar_usuario(id_usuario):
    if id_usuario == current_user.id:
        flash('No puede eliminar la cuenta con la que inició sesión.', 'warning')
    elif ejecutar('DELETE FROM usuarios WHERE id = %s', (id_usuario,)):
        registrar('ELIMINAR', 'Usuarios', 'ID ' + str(id_usuario))
        flash('Usuario eliminado junto con su perfil.', 'warning')
    return redirect(url_for('ver_usuarios'))


@app.route('/bitacora')
@login_required
@solo_admin
def ver_bitacora():
    modulo = request.args.get('modulo', '')
    sql = 'SELECT id_bitacora, usuario, accion, modulo, detalle, fecha FROM bitacora '
    params = ()
    if modulo:
        sql += 'WHERE modulo = %s '
        params = (modulo,)
    registros, paginacion = paginar(consultar(sql + 'ORDER BY id_bitacora DESC', params), pagina_pedida())
    modulos = [f['modulo'] for f in consultar('SELECT DISTINCT modulo FROM bitacora ORDER BY modulo')]
    return render_template('bitacora.html', titulo='Bitácora', registros=registros,
                           paginacion=paginacion, modulos=modulos, modulo=modulo)
