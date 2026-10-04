/* JavaScript de JuansecCTI: validaciones, eventos y componentes de Bootstrap */

/* Datos del proyecto */

// Arreglo que se recorre con un bucle y una condición (Semana 7) para pintar
// los boletines destacados de la versión estática.
const boletinesCTI = [
    {
        titulo: "Campaña de phishing contra cooperativas de ahorro",
        categoria: "Alerta temprana",
        prioridad: "Alta",
        estado: "Publicado",
        descripcion: "Correos que suplantan a entidades de control con enlaces a portales falsos de banca en línea. Se recomienda bloquear los dominios reportados y alertar al personal."
    },
    {
        titulo: "Vulnerabilidad crítica en VPN de acceso remoto",
        categoria: "Vulnerabilidad",
        prioridad: "Crítica",
        estado: "Publicado",
        descripcion: "Fallo que permite ejecución remota de código sin autenticación. Existe parche del fabricante y explotación activa reportada."
    },
    {
        titulo: "Credenciales corporativas filtradas en foros",
        categoria: "Dark web",
        prioridad: "Media",
        estado: "En revisión",
        descripcion: "Listado de cuentas de correo de organizaciones ecuatorianas expuestas en un foro clandestino. Se sugiere forzar el cambio de contraseña."
    },
    {
        titulo: "Buenas prácticas de respaldo frente a ransomware",
        categoria: "Recomendación",
        prioridad: "Baja",
        estado: "Pendiente",
        descripcion: "Guía breve para aplicar la regla 3-2-1 de respaldos y probar periódicamente su restauración."
    }
];

let registrosCTI = [];

/* Utilidades */

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

function obtenerClasePrioridad(prioridad) {
    if (prioridad === "Crítica") {
        return "text-bg-danger";
    }
    if (prioridad === "Alta") {
        return "text-bg-warning";
    }
    if (prioridad === "Media") {
        return "text-bg-info";
    }
    return "text-bg-secondary";
}

/* Barra pública: se vuelve sólida al bajar */

function inicializarNavbar() {
    const barra = elemento("navbarPublica");

    if (!barra) {
        return;
    }

    // Al elegir una opción en el móvil se cierra el menú desplegado.
    barra.querySelectorAll(".nav-link:not(.dropdown-toggle), .dropdown-item").forEach(function (enlace) {
        enlace.addEventListener("click", function () {
            const menu = elemento("menuPublico");
            if (menu && menu.classList.contains("show") && typeof bootstrap !== "undefined") {
                bootstrap.Collapse.getOrCreateInstance(menu).hide();
            }
        });
    });

    // En las páginas internas la barra ya llega sólida desde Flask.
    if (barra.classList.contains("navbar-solida")) {
        return;
    }

    function revisar() {
        barra.classList.toggle("navbar-solida", window.scrollY > 60);
    }

    window.addEventListener("scroll", revisar);
    revisar();
}

/* Menú lateral del panel (móvil) */

function inicializarMenuLateral() {
    const boton = elemento("botonMenu");
    const menu = elemento("menuLateral");
    const velo = elemento("veloMenu");

    if (!boton || !menu) {
        return;
    }

    function cerrar() {
        menu.classList.remove("abierto");
        if (velo) {
            velo.classList.remove("visible");
        }
    }

    boton.addEventListener("click", function () {
        menu.classList.toggle("abierto");
        if (velo) {
            velo.classList.toggle("visible");
        }
    });

    if (velo) {
        velo.addEventListener("click", cerrar);
    }

    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            cerrar();
        }
    });
}

/* Componentes de Bootstrap */

function inicializarTooltips() {
    if (typeof bootstrap === "undefined") {
        return;
    }
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (nodo) {
        new bootstrap.Tooltip(nodo);
    });
}

// Un solo modal de confirmación sirve para todos los listados: cada botón
// indica en data-accion la ruta POST y en data-nombre el registro afectado.
function inicializarModalEliminar() {
    const modal = elemento("modalEliminar");

    if (!modal) {
        return;
    }

    modal.addEventListener("show.bs.modal", function (evento) {
        const boton = evento.relatedTarget;
        const formulario = elemento("formEliminar");
        const nombre = elemento("nombreEliminar");

        if (!boton || !formulario) {
            return;
        }

        formulario.setAttribute("action", boton.getAttribute("data-accion"));

        if (nombre) {
            nombre.innerText = boton.getAttribute("data-nombre") || "este registro";
        }
    });
}

function inicializarImpresion() {
    document.querySelectorAll("[data-imprimir]").forEach(function (boton) {
        boton.addEventListener("click", function () {
            window.print();
        });
    });
}

// Las alertas de éxito se cierran solas a los seis segundos.
function cerrarAlertasAutomaticamente() {
    if (typeof bootstrap === "undefined") {
        return;
    }
    document.querySelectorAll(".alert-dismissible.alert-success").forEach(function (alerta) {
        setTimeout(function () {
            bootstrap.Alert.getOrCreateInstance(alerta).close();
        }, 6000);
    });
}

/* Validación en vivo de los formularios (el servidor vuelve a validar con Flask-WTF) */

const REGLAS = {
    letras: {
        patron: /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'-]*$/,
        mensaje: "Use solo letras y espacios."
    },
    correo: {
        patron: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
        mensaje: "Ingrese un correo electrónico válido."
    },
    telefono: {
        patron: /^0[0-9]{8,9}$/,
        mensaje: "Debe empezar con 0 y tener 9 o 10 dígitos."
    },
    ruc: {
        patron: /^[0-9]{10}001$/,
        mensaje: "El RUC tiene 13 dígitos y termina en 001."
    }
};

function mensajeDe(campo) {
    const grupo = campo.closest(".input-group") || campo;
    let mensaje = grupo.nextElementSibling;

    if (!mensaje || !mensaje.classList.contains("mensaje-vivo")) {
        mensaje = document.createElement("div");
        mensaje.className = "mensaje-vivo small mt-1";
        // Si el campo está dentro de un input-group, el aviso va debajo del grupo.
        grupo.insertAdjacentElement("afterend", mensaje);
    }
    return mensaje;
}

function marcar(campo, error) {
    const mensaje = mensajeDe(campo);

    if (error) {
        campo.classList.remove("is-valid");
        campo.classList.add("is-invalid");
        mensaje.className = "mensaje-vivo small mt-1 text-danger";
        mensaje.innerText = error;
        return false;
    }

    campo.classList.remove("is-invalid");
    if (campo.value.trim() !== "") {
        campo.classList.add("is-valid");
    }
    mensaje.className = "mensaje-vivo small mt-1";
    mensaje.innerText = "";
    return true;
}

function errorDe(campo, formulario) {
    const valor = campo.value.trim();
    const regla = REGLAS[campo.dataset.validar];

    if (campo.required && valor === "") {
        return "Este campo es obligatorio.";
    }
    if (valor === "") {
        return "";
    }
    if (campo.minLength > 0 && valor.length < campo.minLength) {
        return "Mínimo " + campo.minLength + " caracteres.";
    }
    if (campo.maxLength > 0 && valor.length > campo.maxLength) {
        return "Máximo " + campo.maxLength + " caracteres.";
    }
    if (regla && !regla.patron.test(valor)) {
        return regla.mensaje;
    }
    if (campo.dataset.igualA) {
        const otro = formulario.querySelector("#" + campo.dataset.igualA);
        if (otro && otro.value !== campo.value) {
            return "Las contraseñas no coinciden.";
        }
    }
    return "";
}

function inicializarValidacionViva() {
    document.querySelectorAll("form[data-validacion-viva]").forEach(function (formulario) {
        const campos = formulario.querySelectorAll("input:not([type=hidden]):not([type=checkbox]):not([type=submit]), textarea, select");

        campos.forEach(function (campo) {
            campo.addEventListener("input", function () {
                marcar(campo, errorDe(campo, formulario));
            });
            campo.addEventListener("blur", function () {
                marcar(campo, errorDe(campo, formulario));
            });
        });

        formulario.addEventListener("submit", function (evento) {
            let valido = true;

            campos.forEach(function (campo) {
                if (!marcar(campo, errorDe(campo, formulario))) {
                    valido = false;
                }
            });

            const casilla = formulario.querySelector("input[type=checkbox][required]");
            if (casilla && !casilla.checked) {
                casilla.classList.add("is-invalid");
                valido = false;
            }

            if (!valido) {
                evento.preventDefault();
                let aviso = formulario.querySelector(".aviso-formulario");
                if (!aviso) {
                    aviso = document.createElement("div");
                    aviso.setAttribute("role", "alert");
                    formulario.prepend(aviso);
                }
                aviso.className = "aviso-formulario alert alert-danger";
                aviso.innerText = "Revise los campos marcados en rojo antes de continuar.";
                const primero = formulario.querySelector(".is-invalid");
                if (primero) {
                    primero.focus();
                }
            }
        });
    });
}

/* Contador de caracteres en textos */

function inicializarContadores() {
    document.querySelectorAll("[data-contador]").forEach(function (campo) {
        const maximo = parseInt(campo.dataset.contador, 10);
        const contador = document.createElement("div");
        contador.className = "form-text text-end";
        campo.insertAdjacentElement("afterend", contador);

        function actualizar() {
            const usados = campo.value.length;
            contador.innerText = usados + " / " + maximo + " caracteres";
            contador.classList.toggle("text-danger", usados > maximo);
        }

        campo.addEventListener("input", actualizar);
        actualizar();
    });
}

/* Contraseña: mostrar/ocultar y medidor de fuerza */

function inicializarContrasenas() {
    document.querySelectorAll("[data-mostrar]").forEach(function (boton) {
        const campo = elemento(boton.dataset.mostrar);
        if (!campo) {
            return;
        }
        boton.addEventListener("click", function () {
            const oculto = campo.type === "password";
            campo.type = oculto ? "text" : "password";
            boton.innerHTML = oculto ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
        });
    });

    document.querySelectorAll("[data-medidor]").forEach(function (campo) {
        const barra = elemento(campo.dataset.medidor);
        const texto = elemento("textoMedidor");
        if (!barra) {
            return;
        }

        const niveles = [
            { ancho: "0%", color: "transparent", texto: "Mínimo 8 caracteres con mayúscula, minúscula, número y carácter especial." },
            { ancho: "25%", color: "#dc3545", texto: "Contraseña muy débil." },
            { ancho: "50%", color: "#fd7e14", texto: "Contraseña débil." },
            { ancho: "75%", color: "#ffc107", texto: "Contraseña aceptable, añada lo que falta." },
            { ancho: "100%", color: "#198754", texto: "Contraseña segura." }
        ];

        campo.addEventListener("input", function () {
            const valor = campo.value;
            let puntos = 0;
            if (valor.length >= 8) { puntos++; }
            if (/[A-Z]/.test(valor) && /[a-z]/.test(valor)) { puntos++; }
            if (/[0-9]/.test(valor)) { puntos++; }
            if (/[^A-Za-z0-9]/.test(valor)) { puntos++; }
            if (valor === "") { puntos = 0; }

            const nivel = niveles[puntos];
            barra.style.width = nivel.ancho;
            barra.style.background = nivel.color;
            if (texto) {
                texto.innerText = nivel.texto;
            }
        });
    });
}

/* Vista previa de la imagen del servicio */

function inicializarVistaPrevia() {
    document.querySelectorAll("[data-vista-previa]").forEach(function (selector) {
        const imagen = elemento(selector.dataset.vistaPrevia);
        if (!imagen) {
            return;
        }
        selector.addEventListener("change", function () {
            imagen.src = imagen.dataset.base + selector.value;
        });
    });
}

/* Gráfico del panel (Chart.js) */

function inicializarGrafico() {
    const lienzo = elemento("graficoIngresos");

    if (!lienzo || typeof Chart === "undefined") {
        return;
    }

    const meses = JSON.parse(lienzo.dataset.meses || "[]");
    const totales = JSON.parse(lienzo.dataset.totales || "[]");

    new Chart(lienzo, {
        type: "bar",
        data: {
            labels: meses,
            datasets: [{
                label: "Ingresos (USD)",
                data: totales,
                backgroundColor: "rgba(14, 165, 233, 0.75)",
                borderRadius: 6
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

/* Versión estática (GitHub Pages) */

/* Modal de detalle (vive en index.html) */

let modalDetalle = null;

function inicializarModal() {
    const contenedor = elemento("modalDetalle");

    if (!contenedor || typeof bootstrap === "undefined") {
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

/* Se llama desde los botones "Ver detalle" de las tarjetas de servicio. */
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

/* Mensaje de bienvenida de la cabecera */

function inicializarBienvenida() {
    const boton = elemento("botonBienvenida");
    const texto = elemento("textoBienvenida");

    if (!boton || !texto) {
        return;
    }

    boton.addEventListener("click", function () {
        texto.innerText = "JuansecCTI vigila fuentes abiertas, foros y la dark web para avisarle antes de que una amenaza llegue a su organización.";
        texto.classList.remove("d-none");
    });
}

/* Formulario dinámico con validaciones (Semanas 5, 6 y 8) */

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
            mostrarError(nombre, mensajeNombre, "El nombre de la organización es obligatorio.");
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
            mostrarError(descripcion, mensajeDescripcion, "La necesidad es obligatoria.");
            return false;
        }
        if (valor.length < 15) {
            mostrarError(descripcion, mensajeDescripcion, "Describa la necesidad con mínimo 15 caracteres.");
            return false;
        }
        mostrarCorrecto(descripcion, mensajeDescripcion, "Descripción válida.");
        return true;
    }

    function validarCategoria() {
        if (categoria.value === "") {
            mostrarError(categoria, mensajeCategoria, "Seleccione un servicio.");
            return false;
        }
        mostrarCorrecto(categoria, mensajeCategoria, "Servicio seleccionado.");
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

    // Validación en tiempo real: eventos input, blur y change.
    nombre.addEventListener("input", validarNombre);
    nombre.addEventListener("blur", validarNombre);
    descripcion.addEventListener("input", validarDescripcion);
    descripcion.addEventListener("blur", validarDescripcion);
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
                mensajeFormulario.innerText = "Revise los campos antes de registrar la suscripción.";
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
            mensajeFormulario.innerText = "Suscripción registrada correctamente.";
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

    if (!lista) {
        return;
    }

    lista.innerHTML = "";

    if (total) {
        total.innerText = registrosCTI.length;
    }

    if (registrosCTI.length === 0) {
        if (mensajeRegistros) {
            mensajeRegistros.className = "alert alert-info";
            mensajeRegistros.innerText = "Todavía no hay suscripciones registradas desde el formulario.";
        }
        return;
    }

    if (mensajeRegistros) {
        mensajeRegistros.className = "alert alert-success";
        mensajeRegistros.innerText = "Suscripciones registradas en esta sesión.";
    }

    // Cada registro se arma con createElement y appendChild (Semana 5).
    registrosCTI.forEach(function (registro, indice) {
        const tarjeta = document.createElement("div");
        tarjeta.className = "registro-item";

        const titulo = document.createElement("h4");
        titulo.innerText = registro.nombre;

        const etiqueta = document.createElement("span");
        etiqueta.className = "badge text-bg-primary mb-2";
        etiqueta.innerText = registro.categoria;

        const texto = document.createElement("p");
        texto.className = "mb-2";
        texto.innerText = registro.descripcion;

        const acciones = document.createElement("div");
        acciones.className = "d-flex gap-2";

        const botonDetalle = document.createElement("button");
        botonDetalle.type = "button";
        botonDetalle.className = "btn btn-outline-primary btn-sm";
        botonDetalle.innerText = "Ver detalle";
        botonDetalle.addEventListener("click", function () {
            abrirModalDetalle(registro.nombre, registro.categoria, "No definida", "Registro creado", registro.descripcion);
        });

        const botonEliminar = document.createElement("button");
        botonEliminar.type = "button";
        botonEliminar.className = "btn btn-outline-danger btn-sm";
        botonEliminar.innerText = "Eliminar";
        botonEliminar.addEventListener("click", function () {
            registrosCTI.splice(indice, 1);
            renderizarRegistros();
            const mensajeFormulario = elemento("mensajeFormulario");
            if (mensajeFormulario) {
                mensajeFormulario.className = "alert alert-success mt-3";
                mensajeFormulario.innerText = "Suscripción eliminada correctamente.";
            }
        });

        acciones.appendChild(botonDetalle);
        acciones.appendChild(botonEliminar);
        tarjeta.appendChild(titulo);
        tarjeta.appendChild(etiqueta);
        tarjeta.appendChild(texto);
        tarjeta.appendChild(acciones);
        lista.appendChild(tarjeta);
    });
}

/* Boletines destacados: tarjetas, tabla y spinner (Semana 8) */

function renderizarBoletines() {
    const contenedor = elemento("contenedorBoletines");

    if (!contenedor) {
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
            mensaje.innerText = "Boletines de ciberinteligencia actualizados.";
        }

        for (let i = 0; i < boletinesCTI.length; i++) {
            const boletin = boletinesCTI[i];

            // Condición: solo los boletines publicados van a las tarjetas;
            // la tabla resume todos, incluidos los que siguen en revisión.
            if (boletin.estado === "Publicado") {
                const columna = document.createElement("div");
                columna.className = "col-md-6";
                columna.innerHTML = `
                    <article class="card h-100 tarjeta-boletin">
                        <div class="card-body">
                            <span class="badge ${obtenerClasePrioridad(boletin.prioridad)} mb-2">${boletin.prioridad}</span>
                            <h3 class="h5 card-title">${boletin.titulo}</h3>
                            <p class="small text-muted mb-2">${boletin.categoria}</p>
                            <p class="card-text">${boletin.descripcion}</p>
                        </div>
                        <div class="card-footer bg-transparent border-0 pt-0">
                            <button type="button" class="btn btn-outline-primary btn-sm">Ver detalle</button>
                        </div>
                    </article>`;
                columna.querySelector("button").addEventListener("click", function () {
                    abrirModalDetalle(boletin.titulo, boletin.categoria, boletin.prioridad, boletin.estado, boletin.descripcion);
                });
                contenedor.appendChild(columna);
            }

            if (tabla) {
                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td>${boletin.titulo}</td>
                    <td>${boletin.categoria}</td>
                    <td><span class="badge ${obtenerClasePrioridad(boletin.prioridad)}">${boletin.prioridad}</span></td>
                    <td><span class="badge ${obtenerClaseEstado(boletin.estado)}">${boletin.estado}</span></td>`;
                tabla.appendChild(fila);
            }
        }
    }, 900);
}

/* Formulario de contacto con validación (Semana 4) */

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
                if (valor === "") { return "El nombre es obligatorio."; }
                if (valor.length < 5) { return "El nombre debe tener mínimo 5 caracteres."; }
                if (!REGLAS.letras.patron.test(valor)) { return REGLAS.letras.mensaje; }
                return "";
            }
        },
        {
            campo: elemento("contactoCorreo"),
            mensaje: elemento("mensajeContactoCorreo"),
            validar: function (valor) {
                if (valor === "") { return "El correo electrónico es obligatorio."; }
                if (!REGLAS.correo.patron.test(valor)) { return REGLAS.correo.mensaje; }
                return "";
            }
        },
        {
            campo: elemento("contactoAsunto"),
            mensaje: elemento("mensajeContactoAsunto"),
            validar: function (valor) {
                if (valor === "") { return "El asunto es obligatorio."; }
                if (valor.length < 5) { return "El asunto debe tener mínimo 5 caracteres."; }
                return "";
            }
        },
        {
            campo: elemento("contactoMensaje"),
            mensaje: elemento("mensajeContactoMensaje"),
            validar: function (valor) {
                if (valor === "") { return "El mensaje es obligatorio."; }
                if (valor.length < 15) { return "El mensaje debe tener mínimo 15 caracteres."; }
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
        item.campo.addEventListener("input", function () { revisar(item); });
        item.campo.addEventListener("blur", function () { revisar(item); });
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
        aviso.innerText = "Mensaje registrado correctamente. Un analista le responderá en menos de 24 horas.";

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

/* Arranque */

document.addEventListener("DOMContentLoaded", function () {
    // Sitio Flask y versión estática
    inicializarNavbar();
    inicializarTooltips();
    inicializarImpresion();
    cerrarAlertasAutomaticamente();

    // Panel y formularios de Flask
    inicializarMenuLateral();
    inicializarModalEliminar();
    inicializarValidacionViva();
    inicializarContadores();
    inicializarContrasenas();
    inicializarVistaPrevia();
    inicializarGrafico();

    // Versión estática de GitHub Pages
    inicializarModal();
    inicializarBienvenida();
    inicializarFormularioRegistro();
    inicializarFormularioContacto();
    renderizarBoletines();
});
