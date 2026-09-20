/* ===========================================================================
   JuansecCTI - JavaScript del proyecto
   Semanas 5 a 8: manipulacion del DOM, eventos, validaciones dinamicas,
   renderizado de contenido y componentes de Bootstrap.

   El archivo se carga desde base.html en todas las paginas del sistema, por
   eso cada bloque comprueba primero que sus elementos existan en la pagina
   actual. Asi las pantallas internas (productos, clientes, login, etc.) no
   generan errores en la consola.
   =========================================================================== */

/* --------------------------- Datos del proyecto --------------------------- */

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

/* ------------------------------- Utilidades ------------------------------- */

function elemento(id) {
    return document.getElementById(id);
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

/* ------------------- Modal de detalle (vive en base.html) ------------------ */

let modalDetalle = null;

function inicializarModal() {
    const contenedor = elemento("modalDetalle");

    if (!contenedor) {
        return;
    }

    modalDetalle = new bootstrap.Modal(contenedor);
}

function abrirModalDetalle(titulo, categoria, prioridad, estado, descripcion) {
    const modalTitulo = elemento("modalTitulo");
    const modalCuerpo = elemento("modalCuerpo");

    if (!modalDetalle || !modalTitulo || !modalCuerpo) {
        return;
    }

    modalTitulo.innerText = titulo;
    modalCuerpo.innerHTML = "";

    const datos = [
        "Categoría: " + categoria,
        "Prioridad: " + prioridad,
        "Estado: " + estado,
        "Descripción: " + descripcion
    ];

    datos.forEach(function (texto) {
        const parrafo = document.createElement("p");
        parrafo.innerText = texto;
        modalCuerpo.appendChild(parrafo);
    });

    modalDetalle.show();
}

/* Se llama desde los botones "Leer más" del HTML, por eso es global. */
function abrirModalSimple(titulo, descripcion) {
    const modalTitulo = elemento("modalTitulo");
    const modalCuerpo = elemento("modalCuerpo");

    if (!modalDetalle || !modalTitulo || !modalCuerpo) {
        return;
    }

    modalTitulo.innerText = titulo;
    modalCuerpo.innerText = descripcion;
    modalDetalle.show();
}

/* ------------------ Mensaje de bienvenida de la cabecera ------------------ */

function inicializarBienvenida() {
    const boton = elemento("botonBienvenida");
    const texto = elemento("textoBienvenida");

    if (!boton || !texto) {
        return;
    }

    boton.addEventListener("click", function () {
        texto.innerText = "JuansecCTI comparte información útil para fortalecer la seguridad digital de empresas y entidades.";
    });
}

/* ------- Formulario dinamico con validaciones (Semanas 5, 6 y 8) --------- */

function inicializarFormularioRegistro() {
    const formulario = elemento("formularioRegistro");
    const nombre = elemento("nombreRegistro");
    const descripcion = elemento("descripcionRegistro");
    const categoria = elemento("categoriaRegistro");

    if (!formulario || !nombre || !descripcion || !categoria) {
        return;
    }

    const mensajeNombre = elemento("mensajeNombre");
    const mensajeDescripcion = elemento("mensajeDescripcion");
    const mensajeCategoria = elemento("mensajeCategoria");
    const mensajeFormulario = elemento("mensajeFormulario");

    function mostrarError(campo, mensaje, texto) {
        campo.classList.remove("is-valid");
        campo.classList.add("is-invalid");

        if (mensaje) {
            mensaje.className = "mensaje-validacion texto-error";
            mensaje.innerText = texto;
        }
    }

    function mostrarCorrecto(campo, mensaje, texto) {
        campo.classList.remove("is-invalid");
        campo.classList.add("is-valid");

        if (mensaje) {
            mensaje.className = "mensaje-validacion texto-correcto";
            mensaje.innerText = texto;
        }
    }

    function validarNombre() {
        const valor = nombre.value.trim();

        if (valor === "") {
            mostrarError(nombre, mensajeNombre, "El nombre es obligatorio.");
            return false;
        }

        if (valor.length < 5) {
            mostrarError(nombre, mensajeNombre, "El nombre debe tener mínimo 5 caracteres.");
            return false;
        }

        mostrarCorrecto(nombre, mensajeNombre, "Nombre válido.");
        return true;
    }

    function validarDescripcion() {
        const valor = descripcion.value.trim();

        if (valor === "") {
            mostrarError(descripcion, mensajeDescripcion, "La descripción es obligatoria.");
            return false;
        }

        if (valor.length < 15) {
            mostrarError(descripcion, mensajeDescripcion, "La descripción debe tener mínimo 15 caracteres.");
            return false;
        }

        mostrarCorrecto(descripcion, mensajeDescripcion, "Descripción válida.");
        return true;
    }

    function validarCategoria() {
        if (categoria.value === "") {
            mostrarError(categoria, mensajeCategoria, "Seleccione una categoría.");
            return false;
        }

        mostrarCorrecto(categoria, mensajeCategoria, "Categoría seleccionada.");
        return true;
    }

    function limpiarValidaciones() {
        [nombre, descripcion, categoria].forEach(function (campo) {
            campo.classList.remove("is-valid", "is-invalid");
        });

        [mensajeNombre, mensajeDescripcion, mensajeCategoria].forEach(function (mensaje) {
            if (mensaje) {
                mensaje.innerText = "";
            }
        });
    }

    // Validacion en tiempo real: eventos input, blur y change.
    nombre.addEventListener("input", validarNombre);
    nombre.addEventListener("blur", validarNombre);

    descripcion.addEventListener("input", validarDescripcion);
    descripcion.addEventListener("blur", validarDescripcion);

    categoria.addEventListener("input", validarCategoria);
    categoria.addEventListener("blur", validarCategoria);
    categoria.addEventListener("change", validarCategoria);

    formulario.addEventListener("submit", function (evento) {
        evento.preventDefault();

        const nombreValido = validarNombre();
        const descripcionValida = validarDescripcion();
        const categoriaValida = validarCategoria();

        if (!nombreValido || !descripcionValida || !categoriaValida) {
            if (mensajeFormulario) {
                mensajeFormulario.className = "alert alert-danger mt-3";
                mensajeFormulario.innerText = "Revise los campos antes de registrar la información.";
            }
            return;
        }

        registrosCTI.push({
            nombre: nombre.value.trim(),
            descripcion: descripcion.value.trim(),
            categoria: categoria.value
        });

        renderizarRegistros();

        if (mensajeFormulario) {
            mensajeFormulario.className = "alert alert-success mt-3";
            mensajeFormulario.innerText = "Registro agregado correctamente.";
        }

        formulario.reset();
        limpiarValidaciones();
    });

    renderizarRegistros();
}

function renderizarRegistros() {
    const lista = elemento("listaRegistros");
    const total = elemento("totalRegistros");
    const mensajeRegistros = elemento("mensajeRegistros");
    const plantilla = elemento("plantillaRegistro");

    if (!lista || !plantilla) {
        return;
    }

    lista.innerHTML = "";

    if (total) {
        total.innerText = registrosCTI.length;
    }

    if (registrosCTI.length === 0) {
        if (mensajeRegistros) {
            mensajeRegistros.className = "alert alert-info";
            mensajeRegistros.innerText = "Todavía no existen registros creados desde el formulario.";
        }
        return;
    }

    if (mensajeRegistros) {
        mensajeRegistros.className = "alert alert-success";
        mensajeRegistros.innerText = "Los registros se muestran mediante tarjetas Bootstrap generadas con JavaScript.";
    }

    registrosCTI.forEach(function (registro, indice) {
        const copia = plantilla.content.cloneNode(true);

        copia.querySelector('[data-campo="nombre"]').innerText = registro.nombre;
        copia.querySelector('[data-campo="categoria"]').innerText = registro.categoria;
        copia.querySelector('[data-campo="descripcion"]').innerText = registro.descripcion;

        copia.querySelector('[data-accion="detalle"]').addEventListener("click", function () {
            abrirModalDetalle(
                registro.nombre,
                registro.categoria,
                "No definida",
                "Registro creado",
                registro.descripcion
            );
        });

        copia.querySelector('[data-accion="eliminar"]').addEventListener("click", function () {
            registrosCTI.splice(indice, 1);
            renderizarRegistros();

            const mensajeFormulario = elemento("mensajeFormulario");

            if (mensajeFormulario) {
                mensajeFormulario.className = "alert alert-success mt-3";
                mensajeFormulario.innerText = "Registro eliminado correctamente.";
            }
        });

        lista.appendChild(copia);
    });
}

/* --------- Boletines destacados: tarjetas, tabla y spinner (Semana 8) ------ */

function renderizarBoletines() {
    const contenedor = elemento("contenedorBoletines");
    const plantilla = elemento("plantillaBoletin");

    if (!contenedor || !plantilla) {
        return;
    }

    const tabla = elemento("tablaBoletines");
    const mensaje = elemento("mensajeBoletines");
    const spinner = elemento("spinnerCarga");

    contenedor.innerHTML = "";

    if (tabla) {
        tabla.innerHTML = "";
    }

    if (spinner) {
        spinner.classList.remove("d-none");
    }

    setTimeout(function () {
        if (spinner) {
            spinner.classList.add("d-none");
        }

        if (boletinesCTI.length === 0) {
            if (mensaje) {
                mensaje.className = "alert alert-warning";
                mensaje.innerText = "No existen boletines disponibles para mostrar.";
            }
            return;
        }

        if (mensaje) {
            mensaje.className = "alert alert-success";
            mensaje.innerText = "Boletines cargados correctamente usando Bootstrap y JavaScript.";
        }

        boletinesCTI.forEach(function (boletin) {
            const copia = plantilla.content.cloneNode(true);

            copia.querySelector('[data-campo="titulo"]').innerText = boletin.titulo;
            copia.querySelector('[data-campo="categoria"]').innerText = boletin.categoria;
            copia.querySelector('[data-campo="prioridad"]').innerText = boletin.prioridad;
            copia.querySelector('[data-campo="descripcion"]').innerText = boletin.descripcion;

            const estado = copia.querySelector('[data-campo="estado"]');
            estado.innerText = boletin.estado;
            estado.classList.add(obtenerClaseEstado(boletin.estado));

            copia.querySelector('[data-accion="detalle"]').addEventListener("click", function () {
                abrirModalDetalle(
                    boletin.titulo,
                    boletin.categoria,
                    boletin.prioridad,
                    boletin.estado,
                    boletin.descripcion
                );
            });

            contenedor.appendChild(copia);

            if (tabla) {
                const fila = document.createElement("tr");

                fila.innerHTML = `
                    <td>${boletin.titulo}</td>
                    <td>${boletin.categoria}</td>
                    <td>${boletin.prioridad}</td>
                    <td><span class="badge ${obtenerClaseEstado(boletin.estado)}">${boletin.estado}</span></td>
                `;

                tabla.appendChild(fila);
            }
        });
    }, 1000);
}

/* ------------- Formulario de contacto con validacion (Semana 4) ------------ */

function inicializarFormularioContacto() {
    const formulario = elemento("formularioContacto");

    if (!formulario) {
        return;
    }

    const campos = [
        {
            campo: elemento("contactoNombre"),
            mensaje: elemento("mensajeContactoNombre"),
            validar: function (valor) {
                if (valor === "") {
                    return "El nombre es obligatorio.";
                }
                if (valor.length < 5) {
                    return "El nombre debe tener mínimo 5 caracteres.";
                }
                return "";
            }
        },
        {
            campo: elemento("contactoCorreo"),
            mensaje: elemento("mensajeContactoCorreo"),
            validar: function (valor) {
                if (valor === "") {
                    return "El correo electrónico es obligatorio.";
                }
                if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(valor)) {
                    return "Ingrese un correo electrónico válido.";
                }
                return "";
            }
        },
        {
            campo: elemento("contactoAsunto"),
            mensaje: elemento("mensajeContactoAsunto"),
            validar: function (valor) {
                if (valor === "") {
                    return "El asunto es obligatorio.";
                }
                if (valor.length < 5) {
                    return "El asunto debe tener mínimo 5 caracteres.";
                }
                return "";
            }
        },
        {
            campo: elemento("contactoMensaje"),
            mensaje: elemento("mensajeContactoMensaje"),
            validar: function (valor) {
                if (valor === "") {
                    return "El mensaje es obligatorio.";
                }
                if (valor.length < 15) {
                    return "El mensaje debe tener mínimo 15 caracteres.";
                }
                return "";
            }
        }
    ];

    const aviso = elemento("mensajeContacto");

    function revisar(item) {
        if (!item.campo) {
            return true;
        }

        const error = item.validar(item.campo.value.trim());

        if (error === "") {
            item.campo.classList.remove("is-invalid");
            item.campo.classList.add("is-valid");

            if (item.mensaje) {
                item.mensaje.className = "mensaje-validacion texto-correcto";
                item.mensaje.innerText = "Dato válido.";
            }
            return true;
        }

        item.campo.classList.remove("is-valid");
        item.campo.classList.add("is-invalid");

        if (item.mensaje) {
            item.mensaje.className = "mensaje-validacion texto-error";
            item.mensaje.innerText = error;
        }
        return false;
    }

    campos.forEach(function (item) {
        if (!item.campo) {
            return;
        }

        item.campo.addEventListener("input", function () {
            revisar(item);
        });

        item.campo.addEventListener("blur", function () {
            revisar(item);
        });
    });

    formulario.addEventListener("submit", function (evento) {
        evento.preventDefault();

        let valido = true;

        campos.forEach(function (item) {
            if (!revisar(item)) {
                valido = false;
            }
        });

        if (!aviso) {
            return;
        }

        if (!valido) {
            aviso.className = "alert alert-danger";
            aviso.innerText = "Revise los campos marcados antes de enviar el mensaje.";
            return;
        }

        aviso.className = "alert alert-success";
        aviso.innerText = "Mensaje registrado correctamente. Nos pondremos en contacto pronto.";

        formulario.reset();

        campos.forEach(function (item) {
            if (item.campo) {
                item.campo.classList.remove("is-valid", "is-invalid");
            }
            if (item.mensaje) {
                item.mensaje.innerText = "";
            }
        });
    });
}

/* ------------------------------ Arranque ---------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
    inicializarModal();
    inicializarBienvenida();
    inicializarFormularioRegistro();
    inicializarFormularioContacto();
    renderizarBoletines();
});
