const botonBienvenida = document.getElementById("botonBienvenida");
const textoBienvenida = document.getElementById("textoBienvenida");
const formularioRegistro = document.getElementById("formularioRegistro");
const nombreRegistro = document.getElementById("nombreRegistro");
const descripcionRegistro = document.getElementById("descripcionRegistro");
const categoriaRegistro = document.getElementById("categoriaRegistro");
const mensajeFormulario = document.getElementById("mensajeFormulario");
const listaRegistros = document.getElementById("listaRegistros");
const totalRegistros = document.getElementById("totalRegistros");

botonBienvenida.addEventListener("click", function () {
    textoBienvenida.innerText = "JuansecCTI comparte información útil para fortalecer la seguridad digital de empresas y entidades.";
});

formularioRegistro.addEventListener("submit", function (evento) {
    evento.preventDefault();

    const nombre = nombreRegistro.value.trim();
    const descripcion = descripcionRegistro.value.trim();
    const categoria = categoriaRegistro.value;

    if (nombre === "" || descripcion === "" || categoria === "") {
        mensajeFormulario.className = "alert alert-warning mt-3";
        mensajeFormulario.innerText = "Por favor complete todos los campos antes de registrar la información.";
        return;
    }

    crearRegistro(nombre, descripcion, categoria);

    mensajeFormulario.className = "alert alert-success mt-3";
    mensajeFormulario.innerText = "Registro agregado correctamente.";

    formularioRegistro.reset();
    actualizarTotal();
});

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
        mensajeFormulario.className = "alert alert-info mt-3";
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