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
const mensajeRegistros = document.getElementById("mensajeRegistros");
const listaRegistros = document.getElementById("listaRegistros");
const totalRegistros = document.getElementById("totalRegistros");

const contenedorBoletines = document.getElementById("contenedorBoletines");
const mensajeBoletines = document.getElementById("mensajeBoletines");
const tablaBoletines = document.getElementById("tablaBoletines");
const spinnerCarga = document.getElementById("spinnerCarga");

const plantillaBoletin = document.getElementById("plantillaBoletin");
const plantillaRegistro = document.getElementById("plantillaRegistro");

const modalDetalle = new bootstrap.Modal(document.getElementById("modalDetalle"));
const modalTitulo = document.getElementById("modalTitulo");
const modalCuerpo = document.getElementById("modalCuerpo");

const boletinesCTI = [
    {
        titulo: "Alerta sobre vulnerabilidades críticas",
        categoria: "Alerta de vulnerabilidad",
        prioridad: "Alta",
        estado: "Publicado",
        descripcion: "Resumen de vulnerabilidades recientes que pueden afectar a empresas y entidades."
    },
    {
        titulo: "Noticias de ciberseguridad empresarial",
        categoria: "Noticia de seguridad",
        prioridad: "Media",
        estado: "En revisión",
        descripcion: "Selección de noticias relevantes sobre amenazas digitales y buenas prácticas de protección."
    },
    {
        titulo: "Recomendaciones de protección digital",
        categoria: "Recomendación",
        prioridad: "Baja",
        estado: "Pendiente",
        descripcion: "Consejos básicos para mejorar la postura de seguridad y reducir riesgos comunes."
    }
];

let registrosCTI = [];

botonBienvenida.addEventListener("click", function () {
    textoBienvenida.innerText = "JuansecCTI comparte información útil para fortalecer la seguridad digital de empresas y entidades.";
});

nombreRegistro.addEventListener("input", validarNombre);
nombreRegistro.addEventListener("blur", validarNombre);

descripcionRegistro.addEventListener("input", validarDescripcion);
descripcionRegistro.addEventListener("blur", validarDescripcion);

categoriaRegistro.addEventListener("input", validarCategoria);
categoriaRegistro.addEventListener("blur", validarCategoria);
categoriaRegistro.addEventListener("change", validarCategoria);

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

    const nuevoRegistro = {
        nombre: nombreRegistro.value.trim(),
        descripcion: descripcionRegistro.value.trim(),
        categoria: categoriaRegistro.value
    };

    registrosCTI.push(nuevoRegistro);

    renderizarRegistros();

    mensajeFormulario.className = "alert alert-success mt-3";
    mensajeFormulario.innerText = "Registro agregado correctamente.";

    formularioRegistro.reset();
    limpiarValidaciones();
});

function validarNombre() {
    const nombre = nombreRegistro.value.trim();

    if (nombre === "") {
        mostrarError(nombreRegistro, mensajeNombre, "El nombre es obligatorio.");
        return false;
    }

    if (nombre.length < 5) {
        mostrarError(nombreRegistro, mensajeNombre, "El nombre debe tener mínimo 5 caracteres.");
        return false;
    }

    mostrarCorrecto(nombreRegistro, mensajeNombre, "Nombre válido.");
    return true;
}

function validarDescripcion() {
    const descripcion = descripcionRegistro.value.trim();

    if (descripcion === "") {
        mostrarError(descripcionRegistro, mensajeDescripcion, "La descripción es obligatoria.");
        return false;
    }

    if (descripcion.length < 15) {
        mostrarError(descripcionRegistro, mensajeDescripcion, "La descripción debe tener mínimo 15 caracteres.");
        return false;
    }

    mostrarCorrecto(descripcionRegistro, mensajeDescripcion, "Descripción válida.");
    return true;
}

function validarCategoria() {
    const categoria = categoriaRegistro.value;

    if (categoria === "") {
        mostrarError(categoriaRegistro, mensajeCategoria, "Seleccione una categoría.");
        return false;
    }

    mostrarCorrecto(categoriaRegistro, mensajeCategoria, "Categoría seleccionada.");
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

function limpiarValidaciones() {
    nombreRegistro.classList.remove("is-valid", "is-invalid");
    descripcionRegistro.classList.remove("is-valid", "is-invalid");
    categoriaRegistro.classList.remove("is-valid", "is-invalid");

    mensajeNombre.innerText = "";
    mensajeDescripcion.innerText = "";
    mensajeCategoria.innerText = "";
}

function renderizarBoletines() {
    contenedorBoletines.innerHTML = "";
    tablaBoletines.innerHTML = "";
    spinnerCarga.classList.remove("d-none");

    setTimeout(function () {
        spinnerCarga.classList.add("d-none");

        if (boletinesCTI.length === 0) {
            mensajeBoletines.className = "alert alert-warning";
            mensajeBoletines.innerText = "No existen boletines disponibles para mostrar.";
            return;
        }

        mensajeBoletines.className = "alert alert-success";
        mensajeBoletines.innerText = "Boletines cargados correctamente usando Bootstrap y JavaScript.";

        boletinesCTI.forEach(function (boletin) {
            const copia = plantillaBoletin.content.cloneNode(true);

            copia.querySelector('[data-campo="titulo"]').innerText = boletin.titulo;
            copia.querySelector('[data-campo="categoria"]').innerText = boletin.categoria;
            copia.querySelector('[data-campo="prioridad"]').innerText = boletin.prioridad;
            copia.querySelector('[data-campo="descripcion"]').innerText = boletin.descripcion;

            const estado = copia.querySelector('[data-campo="estado"]');
            estado.innerText = boletin.estado;
            estado.classList.add(obtenerClaseEstado(boletin.estado));

            const botonDetalle = copia.querySelector('[data-accion="detalle"]');

            botonDetalle.addEventListener("click", function () {
                abrirModalDetalle(
                    boletin.titulo,
                    boletin.categoria,
                    boletin.prioridad,
                    boletin.estado,
                    boletin.descripcion
                );
            });

            contenedorBoletines.appendChild(copia);

            const fila = document.createElement("tr");

            fila.innerHTML = `
                <td>${boletin.titulo}</td>
                <td>${boletin.categoria}</td>
                <td>${boletin.prioridad}</td>
                <td><span class="badge ${obtenerClaseEstado(boletin.estado)}">${boletin.estado}</span></td>
            `;

            tablaBoletines.appendChild(fila);
        });
    }, 1000);
}

function obtenerClaseEstado(estado) {
    if (estado === "Publicado") {
        return "text-bg-success";
    }

    if (estado === "En revisión") {
        return "text-bg-warning";
    }

    return "text-bg-secondary";
}

function renderizarRegistros() {
    listaRegistros.innerHTML = "";
    totalRegistros.innerText = registrosCTI.length;

    if (registrosCTI.length === 0) {
        mensajeRegistros.className = "alert alert-info";
        mensajeRegistros.innerText = "Todavía no existen registros creados desde el formulario.";
        return;
    }

    mensajeRegistros.className = "alert alert-success";
    mensajeRegistros.innerText = "Los registros se muestran mediante tarjetas Bootstrap generadas con JavaScript.";

    registrosCTI.forEach(function (registro, indice) {
        const copia = plantillaRegistro.content.cloneNode(true);

        copia.querySelector('[data-campo="nombre"]').innerText = registro.nombre;
        copia.querySelector('[data-campo="categoria"]').innerText = registro.categoria;
        copia.querySelector('[data-campo="descripcion"]').innerText = registro.descripcion;

        const botonDetalle = copia.querySelector('[data-accion="detalle"]');
        const botonEliminar = copia.querySelector('[data-accion="eliminar"]');

        botonDetalle.addEventListener("click", function () {
            abrirModalDetalle(
                registro.nombre,
                registro.categoria,
                "No definida",
                "Registro creado",
                registro.descripcion
            );
        });

        botonEliminar.addEventListener("click", function () {
            registrosCTI.splice(indice, 1);

            renderizarRegistros();

            mensajeFormulario.className = "alert alert-success mt-3";
            mensajeFormulario.innerText = "Registro eliminado correctamente.";
        });

        listaRegistros.appendChild(copia);
    });
}

function abrirModalDetalle(titulo, categoria, prioridad, estado, descripcion) {
    modalTitulo.innerText = titulo;

    modalCuerpo.innerHTML = "";

    const categoriaTexto = document.createElement("p");
    categoriaTexto.innerText = "Categoría: " + categoria;

    const prioridadTexto = document.createElement("p");
    prioridadTexto.innerText = "Prioridad: " + prioridad;

    const estadoTexto = document.createElement("p");
    estadoTexto.innerText = "Estado: " + estado;

    const descripcionTexto = document.createElement("p");
    descripcionTexto.innerText = "Descripción: " + descripcion;

    modalCuerpo.appendChild(categoriaTexto);
    modalCuerpo.appendChild(prioridadTexto);
    modalCuerpo.appendChild(estadoTexto);
    modalCuerpo.appendChild(descripcionTexto);

    modalDetalle.show();
}

function abrirModalSimple(titulo, descripcion) {
    modalTitulo.innerText = titulo;
    modalCuerpo.innerText = descripcion;
    modalDetalle.show();
}

renderizarBoletines();
renderizarRegistros();