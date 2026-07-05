const botonBienvenida = document.getElementById("botonBienvenida");
const textoBienvenida = document.getElementById("textoBienvenida");

const formularioRegistro = document.getElementById("formularioRegistro");

const nombreRegistro = document.getElementById("nombreRegistro");
const descripcionRegistro = document.getElementById("descripcionRegistro");
const categoriaRegistro = document.getElementById("categoriaRegistro");

const mensajeNombre = document.getElementById("mensajeNombre");
const mensajeDescripcion = document.getElementById("mensajeDescripcion");
const mensajeCategoria = document.getElementById("mensajeCategoria");

const mensajeFormulario = document.getElementById("mensajeFormulario");
const listaRegistros = document.getElementById("listaRegistros");
const totalRegistros = document.getElementById("totalRegistros");

botonBienvenida.addEventListener("click", function () {
    textoBienvenida.innerText = "JuansecCTI comparte información útil para fortalecer la seguridad digital de empresas y entidades.";
});

nombreRegistro.addEventListener("input", validarNombre);
nombreRegistro.addEventListener("blur", validarNombre);

descripcionRegistro.addEventListener("input", validarDescripcion);
descripcionRegistro.addEventListener("blur", validarDescripcion);

categoriaRegistro.addEventListener("input", validarCategoria);
categoriaRegistro.addEventListener("blur", validarCategoria);

function validarNombre() {
    const nombre = nombreRegistro.value.trim();

    if (nombre === "") {
        mostrarError(
            nombreRegistro,
            mensajeNombre,
            "El nombre es obligatorio."
        );

        return false;
    }

    if (nombre.length < 5) {
        mostrarError(
            nombreRegistro,
            mensajeNombre,
            "El nombre debe tener mínimo 5 caracteres."
        );

        return false;
    }

    mostrarCorrecto(
        nombreRegistro,
        mensajeNombre,
        "Nombre válido."
    );

    return true;
}

function validarDescripcion() {
    const descripcion = descripcionRegistro.value.trim();

    if (descripcion === "") {
        mostrarError(
            descripcionRegistro,
            mensajeDescripcion,
            "La descripción es obligatoria."
        );

        return false;
    }

    if (descripcion.length < 15) {
        mostrarError(
            descripcionRegistro,
            mensajeDescripcion,
            "La descripción debe tener mínimo 15 caracteres."
        );

        return false;
    }

    mostrarCorrecto(
        descripcionRegistro,
        mensajeDescripcion,
        "Descripción válida."
    );

    return true;
}

function validarCategoria() {
    const categoria = categoriaRegistro.value;

    if (categoria === "") {
        mostrarError(
            categoriaRegistro,
            mensajeCategoria,
            "Seleccione una categoría."
        );

        return false;
    }

    mostrarCorrecto(
        categoriaRegistro,
        mensajeCategoria,
        "Categoría seleccionada."
    );

    return true;
}

function mostrarError(campo, mensaje, texto) {
    campo.classList.remove("is-valid");
    campo.classList.add("is-invalid");

    mensaje.className = "mensaje-validacion texto-error";
    mensaje.innerText = texto;
}

function mostrarCorrecto(campo, mensaje, texto) {
    campo.classList.remove("is-invalid");
    campo.classList.add("is-valid");

    mensaje.className = "mensaje-validacion texto-correcto";
    mensaje.innerText = texto;
}

formularioRegistro.addEventListener("submit", function (evento) {
    evento.preventDefault();

    const nombreValido = validarNombre();
    const descripcionValida = validarDescripcion();
    const categoriaValida = validarCategoria();

    if (!nombreValido || !descripcionValida || !categoriaValida) {
        mensajeFormulario.className = "alert alert-danger mt-3";
        mensajeFormulario.innerText = "Revise los campos antes de registrar la información.";

        return;
    }

    const nombre = nombreRegistro.value.trim();
    const descripcion = descripcionRegistro.value.trim();
    const categoria = categoriaRegistro.value;

    crearRegistro(nombre, descripcion, categoria);

    mensajeFormulario.className = "alert alert-success mt-3";
    mensajeFormulario.innerText = "Registro agregado correctamente.";

    formularioRegistro.reset();

    limpiarValidaciones();

    actualizarTotal();
});

function limpiarValidaciones() {
    nombreRegistro.classList.remove("is-valid", "is-invalid");
    descripcionRegistro.classList.remove("is-valid", "is-invalid");
    categoriaRegistro.classList.remove("is-valid", "is-invalid");

    mensajeNombre.innerText = "";
    mensajeDescripcion.innerText = "";
    mensajeCategoria.innerText = "";
}

function crearRegistro(nombre, descripcion, categoria) {
    const columna = document.createElement("div");

    columna.className = "col-md-6 mb-3";

    const tarjeta = document.createElement("div");

    tarjeta.className = "card registro-card h-100";

    const cuerpo = document.createElement("div");

    cuerpo.className = "card-body";

    const titulo = document.createElement("h3");

    titulo.className = "card-title h5";
    titulo.innerText = nombre;

    const textoCategoria = document.createElement("p");

    textoCategoria.className = "card-text";
    textoCategoria.innerText = "Categoría: " + categoria;

    const textoDescripcion = document.createElement("p");

    textoDescripcion.className = "card-text";
    textoDescripcion.innerText = descripcion;

    const botonEliminar = document.createElement("button");

    botonEliminar.className = "btn btn-danger btn-sm";
    botonEliminar.innerText = "Eliminar";

    botonEliminar.addEventListener("click", function () {
        columna.remove();

        mensajeFormulario.className = "alert alert-success mt-3";
        mensajeFormulario.innerText = "Registro eliminado correctamente.";

        actualizarTotal();
    });

    cuerpo.appendChild(titulo);
    cuerpo.appendChild(textoCategoria);
    cuerpo.appendChild(textoDescripcion);
    cuerpo.appendChild(botonEliminar);

    tarjeta.appendChild(cuerpo);

    columna.appendChild(tarjeta);

    listaRegistros.appendChild(columna);
}

function actualizarTotal() {
    totalRegistros.innerText = listaRegistros.children.length;
}