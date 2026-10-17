/*
 * ============================================================
 * RIUL · INTERFACES POR ROL (Administrador / Docente Líder)
 * ============================================================
 *
 * - El rol sale de localStorage.user (role | rol | role_name).
 * - Estudiantes y visitantes siguen usando la interfaz original.
 * - Cada módulo declara su `endpoint`. Al cargar intenta
 *   GET {endpoint}; si el API aún no existe usa TEMP_DATA.
 * - Las acciones (crear/editar/aprobar...) llaman al API con
 *   persist(); si responde 404/405/501 o no hay red, el cambio
 *   queda solo en pantalla.
 *
 * Contrato esperado del API (pendiente de implementar):
 *   GET    {endpoint}              -> { data: [ ... ] }
 *   POST   {endpoint}              -> { data: { ...creado } }
 *   PUT    {endpoint}/:id
 *   PATCH  {endpoint}/:id
 *   DELETE {endpoint}/:id
 */

/* ============================================================
 * ROL ACTUAL
 * ============================================================ */

const ROLE_LABELS = {
    admin: "Administrador",
    docente: "Docente Líder",
    estudiante: "Estudiante Investigador",
    visitante: "Visitante"
};

function normalizeRole(raw) {

    const value = String(raw || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();

    if (value.includes("admin")) return "admin";
    if (value.includes("docente") || value.includes("lider") || value.includes("teacher")) return "docente";
    if (value.includes("estudiante") || value.includes("student")) return "estudiante";

    return "visitante";
}

function getStoredUser() {

    try {
        return JSON.parse(localStorage.getItem("user") || "{}");
    } catch (error) {
        return {};
    }
}

function getUserRole() {

    const user = getStoredUser();

    return normalizeRole(user.role || user.rol || user.role_name || user.roleName);
}

/* TEMPORAL: sin API de login, "admin@..." y "docente@..." simulan el rol. */
function inferDemoRole(email) {

    const prefix = String(email || "").toLowerCase();

    if (prefix.startsWith("admin")) return "Administrador";
    if (prefix.startsWith("docente")) return "Docente Líder";

    return undefined;
}

function defaultScreen() {

    const role = getUserRole();

    if (role === "admin") return "adm-dashboard";
    if (role === "docente") return "doc-dashboard";

    return "dashboard";
}


/* ============================================================
 * UTILIDADES
 * ============================================================ */

function esc(value) {

    return String(value ?? "").replace(/[&<>"']/g, function (char) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "\"": "&quot;",
            "'": "&#39;"
        }[char];
    });
}

function byId(id) {
    return document.getElementById(id);
}

function setText(selector, value) {
    document.querySelectorAll(selector).forEach(function (node) {
        node.textContent = value;
    });
}

function stars(level) {

    const n = Math.max(0, Math.min(5, Number(level) || 0));

    return "★".repeat(n) + "☆".repeat(5 - n);
}

const BADGE_TONES = {
    green: "bg-[#eaf3de] text-[#3b6d11]",
    amber: "bg-[#faeeda] text-[#854f0b]",
    blue: "bg-[#e6f1fb] text-[#0c447c]",
    red: "bg-red-100 text-red-800",
    grey: "bg-[#eeeeea] text-[#3a3a38]"
};

const BADGE_MAP = {
    "Activo": "green", "Aprobado": "green", "En curso": "green", "Abierta": "green", "Publicada": "green",
    "Pendiente": "amber", "En revisión": "amber",
    "Nuevo": "blue", "Finalizado": "blue",
    "Rechazado": "red",
    "Inactivo": "grey", "Cerrada": "grey", "Oculta": "grey", "Suspendido": "grey"
};

function badge(text) {

    const tone = BADGE_TONES[BADGE_MAP[text] || "grey"];

    return `<span class="rounded-full px-3 py-1 text-xs font-medium ${tone}">${esc(text)}</span>`;
}

const BTN = {
    base: "rounded-md border px-3 py-1 text-xs font-medium",
    neutral: "border-[#c9c8c2] bg-[#eeeeea] text-[#3a3a38]",
    success: "border-transparent bg-[#eaf3de] text-[#3b6d11]",
    danger: "border-transparent bg-red-100 text-red-800"
};

const CARD = "rounded-2xl border border-[#d8d7d1] bg-white p-6 shadow-sm";
const INPUT = "w-full rounded-lg border border-[#c9c8c2] bg-white px-3 py-2 text-sm";


/* ============================================================
 * DATOS TEMPORALES (reemplazar por el API)
 * ============================================================ */

const ROLES = ["Administrador", "Docente Líder", "Estudiante Investigador", "Visitante"];
const FACULTADES = ["Ingeniería", "Derecho", "Ciencias de la Salud", "Ciencias Económicas", "Ciencias Sociales"];
const PROGRAMAS = ["Ingeniería de Sistemas", "Ingeniería Industrial", "Derecho", "Medicina", "Contaduría Pública", "Psicología"];

const TEMP_CONVOCATORIAS = [
    { id: 1, titulo: "Convocatoria interna de investigación", cierre: "2026-11-30", estado: "Abierta", postulaciones: 6 },
    { id: 2, titulo: "Movilidad académica 2027", cierre: "2026-12-15", estado: "Abierta", postulaciones: 2 },
    { id: 3, titulo: "Financiación de semilleros 2026-I", cierre: "2026-03-15", estado: "Cerrada", postulaciones: 11 }
];

const TEMP_DATA = {

    usuarios: [
        { id: 1, nombre: "Marcela Ortiz", correo: "marcela.ortiz@unilibre.edu.co", facultad: "Ingeniería", programa: "Ingeniería de Sistemas", rol: "Docente Líder", estado: "Activo", cuenta: "Institucional", fecha: "2026-08-02" },
        { id: 2, nombre: "Elena Ruiz", correo: "elena.ruiz@unilibre.edu.co", facultad: "Ingeniería", programa: "Ingeniería de Sistemas", rol: "Estudiante Investigador", estado: "Activo", cuenta: "Institucional", fecha: "2026-08-10" },
        { id: 3, nombre: "Carlos Pérez", correo: "carlos.perez@unilibre.edu.co", facultad: "Ingeniería", programa: "Ingeniería Industrial", rol: "Estudiante Investigador", estado: "Activo", cuenta: "Institucional", fecha: "2026-08-12" },
        { id: 4, nombre: "Andrés Barrios", correo: "abarrios@unilibre.edu.co", facultad: "Derecho", programa: "Derecho", rol: "Docente Líder", estado: "Activo", cuenta: "Institucional", fecha: "2026-07-21" },
        { id: 5, nombre: "Luis Mora", correo: "luis.mora@gmail.com", facultad: "Ciencias Económicas", programa: "Contaduría Pública", rol: "Visitante", estado: "Inactivo", cuenta: "Externa", fecha: "2026-06-30" },
        { id: 6, nombre: "Sofía Vega", correo: "sofia.vega@unilibre.edu.co", facultad: "Ciencias de la Salud", programa: "Medicina", rol: "Estudiante Investigador", estado: "Pendiente", cuenta: "Institucional", fecha: "2026-10-12" },
        { id: 7, nombre: "Mateo Rojas", correo: "mateo.rojas@outlook.com", facultad: "Ciencias Sociales", programa: "Psicología", rol: "Estudiante Investigador", estado: "Pendiente", cuenta: "Externa", fecha: "2026-10-14" },
        { id: 8, nombre: "Valentina Cruz", correo: "vcruz@correo.com", facultad: "Derecho", programa: "Derecho", rol: "Visitante", estado: "Pendiente", cuenta: "Externa", fecha: "2026-10-15" }
    ],

    semilleros: [
        { id: 1, nombre: "DataLab", facultad: "Ingeniería", linea: "Ciencia de datos", lider: "Marcela Ortiz", integrantes: 18, nivel: 4, estado: "Activo", descripcion: "Análisis de datos y visualización aplicados a la investigación universitaria." },
        { id: 2, nombre: "BioLibre", facultad: "Ciencias de la Salud", linea: "Biodiversidad", lider: "Camilo Herrera", integrantes: 12, nivel: 3, estado: "Activo", descripcion: "Estudio de biodiversidad y salud pública en el Caribe." },
        { id: 3, nombre: "JurisLab", facultad: "Derecho", linea: "Justicia digital", lider: "Andrés Barrios", integrantes: 9, nivel: 2, estado: "Inactivo", descripcion: "Acceso a la justicia y derecho informático." },
        { id: 4, nombre: "EcoFinanzas", facultad: "Ciencias Económicas", linea: "Economía regional", lider: "Paola Mejía", integrantes: 10, nivel: 3, estado: "Activo", descripcion: "Finanzas sostenibles y desarrollo regional." }
    ],

    proyectos: [
        { id: 1, nombre: "Observatorio de datos académicos", semillero: "DataLab", estado: "En curso", avance: 65, inicio: "2026-02-10", descripcion: "Tablero de indicadores académicos." },
        { id: 2, nombre: "Clasificador de publicaciones RIUL", semillero: "DataLab", estado: "Nuevo", avance: 10, inicio: "2026-09-01", descripcion: "Clasificación automática por línea de investigación." },
        { id: 3, nombre: "Biodiversidad del Caribe", semillero: "BioLibre", estado: "En curso", avance: 40, inicio: "2026-03-05", descripcion: "Inventario de especies locales." },
        { id: 4, nombre: "Acceso a la justicia digital", semillero: "JurisLab", estado: "Finalizado", avance: 100, inicio: "2025-08-18", descripcion: "Diagnóstico de acceso a servicios judiciales en línea." }
    ],

    eventos: [
        { id: 1, nombre: "Encuentro nacional de semilleros", fecha: "2026-10-28", modalidad: "Híbrida", semillero: "DataLab", estado: "Abierta" },
        { id: 2, nombre: "Feria de investigación Unilibre", fecha: "2026-11-12", modalidad: "Presencial", semillero: "BioLibre", estado: "Abierta" },
        { id: 3, nombre: "Webinar de ciencia abierta", fecha: "2026-10-22", modalidad: "Virtual", semillero: "EcoFinanzas", estado: "Cerrada" }
    ],

    publicaciones: [
        { id: 1, titulo: "Modelo predictivo de deserción estudiantil", tipo: "Artículo", semillero: "DataLab", autor: "Elena Ruiz", anio: 2026, reacciones: 8, comentarios: 3, estado: "Publicada" },
        { id: 2, titulo: "Dashboard de indicadores de investigación", tipo: "Producto", semillero: "DataLab", autor: "Carlos Pérez", anio: 2026, reacciones: 5, comentarios: 1, estado: "Publicada" },
        { id: 3, titulo: "Análisis de redes en semilleros Unilibre", tipo: "Ponencia", semillero: "DataLab", autor: "Marcela Ortiz", anio: 2025, reacciones: 8, comentarios: 2, estado: "Publicada" },
        { id: 4, titulo: "Minería de texto en convocatorias internas", tipo: "Artículo", semillero: "DataLab", autor: "Ana Gómez", anio: 2025, reacciones: 2, comentarios: 0, estado: "En revisión" }
    ],

    logros: [
        { id: 1, descripcion: "Ponencia nacional en ciencia de datos", usuario: "Elena Ruiz", tipo: "Ponencia", xp: 150, estado: "Pendiente" },
        { id: 2, descripcion: "Primer artículo indexado", usuario: "Carlos Pérez", tipo: "Artículo", xp: 300, estado: "Aprobado" },
        { id: 3, descripcion: "Participación en feria de semilleros", usuario: "Ana Gómez", tipo: "Evento", xp: 80, estado: "Pendiente" },
        { id: 4, descripcion: "Patente en trámite", usuario: "Luis Mora", tipo: "Patente", xp: 500, estado: "Rechazado" }
    ],

    docSemillero: {
        nombre: "DataLab",
        descripcion: "Análisis de datos, visualización y proyectos aplicados a la investigación universitaria.",
        linea: "Ciencia de datos",
        facultad: "Ingeniería",
        nivel: 4,
        xp: 2340,
        xpSiguiente: 3000,
        estado: "Activo"
    },

    docIntegrantes: [
        { id: 1, nombre: "Elena Ruiz", correo: "elena.ruiz@unilibre.edu.co", programa: "Ingeniería de Sistemas", estado: "Activo", desde: "2026-02-01" },
        { id: 2, nombre: "Carlos Pérez", correo: "carlos.perez@unilibre.edu.co", programa: "Ingeniería Industrial", estado: "Activo", desde: "2026-02-01" },
        { id: 3, nombre: "Ana Gómez", correo: "ana.gomez@unilibre.edu.co", programa: "Ingeniería de Sistemas", estado: "Activo", desde: "2026-03-10" },
        { id: 4, nombre: "Luis Mora", correo: "luis.mora@unilibre.edu.co", programa: "Ingeniería de Sistemas", estado: "Activo", desde: "2026-04-22" },
        { id: 5, nombre: "Sofía Vega", correo: "sofia.vega@unilibre.edu.co", programa: "Ingeniería de Sistemas", estado: "Pendiente", desde: "2026-10-12" },
        { id: 6, nombre: "Mateo Rojas", correo: "mateo.rojas@unilibre.edu.co", programa: "Ingeniería Industrial", estado: "Pendiente", desde: "2026-10-14" }
    ]
};

function clone(value) {
    return JSON.parse(JSON.stringify(value));
}


/* ============================================================
 * ESTADO + API
 * ============================================================ */

const RS = {};          // filas por módulo
const usingMock = {};   // módulo -> true si usa TEMP_DATA

/*
 * Ejecuta la acción contra el API.
 * Si el endpoint aún no existe (404/405/501 o sin respuesta)
 * devuelve { ok: true, local: true } para que la UI siga funcionando.
 */
async function persist(method, url, data) {

    try {

        const response = await api.request({ method, url, data });

        return {
            ok: true,
            local: false,
            data: response.data && response.data.data
        };

    } catch (error) {

        const status = error.response && error.response.status;

        if (!error.response || [404, 405, 501].includes(status)) {
            return { ok: true, local: true };
        }

        showMessage(
            (error.response.data && error.response.data.message) ||
            "No se pudo completar la acción",
            "error"
        );

        return { ok: false };
    }
}

function doneMessage(text, result) {
    showMessage(result.local ? `${text} · solo en pantalla, API pendiente` : text);
}

async function mutate(cfg, row, patch, options) {

    const opts = options || {};
    const result = await persist(
        opts.method || "PATCH",
        opts.url || `${cfg.endpoint}/${row.id}`,
        patch
    );

    if (!result.ok) return false;

    Object.assign(row, patch);
    renderModule(cfg);
    doneMessage(opts.message || "Cambios guardados", result);

    return true;
}


/* ============================================================
 * MODAL GENÉRICO
 * ============================================================ */

let modalSubmit = null;

function openForm(options) {

    const fields = options.fields || [];
    const values = options.values || {};

    byId("role-modal-title").textContent = options.title;
    byId("role-modal-submit").textContent = options.submitLabel || "Guardar";

    const text = byId("role-modal-text");
    text.textContent = options.text || "";
    text.classList.toggle("hidden", !options.text);

    byId("role-modal-fields").innerHTML = fields.map(function (field) {

        const value = values[field.key] ?? "";
        const required = field.required === false ? "" : "required";
        let control;

        if (field.type === "textarea") {
            control = `<textarea name="${field.key}" rows="3" ${required} class="${INPUT}">${esc(value)}</textarea>`;
        } else if (field.type === "select") {
            control = `<select name="${field.key}" ${required} class="${INPUT}">` +
                field.options.map(function (option) {
                    return `<option value="${esc(option)}" ${option === value ? "selected" : ""}>${esc(option)}</option>`;
                }).join("") +
                "</select>";
        } else {
            control = `<input name="${field.key}" type="${field.type || "text"}" value="${esc(value)}" ${required} class="${INPUT}">`;
        }

        return `<label class="block text-sm font-medium text-[#3a3a38]">${esc(field.label)}<span class="mt-1 block">${control}</span></label>`;

    }).join("");

    modalSubmit = options.onSubmit;

    const modal = byId("role-modal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");

    const first = modal.querySelector("input, textarea, select");
    if (first) first.focus();
}

function closeForm() {

    const modal = byId("role-modal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    modalSubmit = null;
}

function bindModal() {

    byId("role-modal-cancel").addEventListener("click", closeForm);

    byId("role-modal").addEventListener("click", function (event) {
        if (event.target === this) closeForm();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && modalSubmit) closeForm();
    });

    byId("role-modal-form").addEventListener("submit", async function (event) {

        event.preventDefault();

        if (!modalSubmit) return;

        const data = Object.fromEntries(new FormData(this).entries());
        const keepOpen = (await modalSubmit(data)) === false;

        if (!keepOpen) closeForm();
    });
}


/* ============================================================
 * MÓDULOS (tablas generadas desde configuración)
 * ============================================================ */

/* Acciones reutilizables */
const act = {

    edit: function (cfg) {
        return {
            label: "Editar",
            run: function (row) { openModuleForm(cfg, row); }
        };
    },

    remove: function (cfg) {
        return {
            label: "Eliminar",
            tone: "danger",
            run: async function (row) {

                if (!window.confirm(`¿Eliminar "${row[cfg.titleKey]}"?`)) return;

                const result = await persist("DELETE", `${cfg.endpoint}/${row.id}`);

                if (!result.ok) return;

                RS[cfg.id] = RS[cfg.id].filter(function (item) { return item !== row; });
                renderModule(cfg);
                doneMessage(`${cfg.singular} eliminado`, result);
            }
        };
    },

    set: function (cfg, label, patch, message, options) {
        const opts = options || {};
        return {
            label: label,
            tone: opts.tone,
            show: opts.show,
            run: function (row) {
                mutate(cfg, row, typeof patch === "function" ? patch(row) : patch, {
                    url: opts.url ? opts.url(row) : undefined,
                    message: message
                });
            }
        };
    }
};

function openModuleForm(cfg, row) {

    openForm({
        title: row ? `Editar ${cfg.singular}` : `Nuevo ${cfg.singular}`,
        fields: cfg.fields,
        values: row || cfg.defaults || {},
        onSubmit: async function (data) {

            if (row) {
                return mutate(cfg, row, data, {
                    method: "PUT",
                    message: `${cfg.singular} actualizado`
                });
            }

            const result = await persist("POST", cfg.endpoint, data);

            if (!result.ok) return false;

            const created = Object.assign(
                { id: Date.now() },
                cfg.defaults || {},
                data,
                result.data || {}
            );

            RS[cfg.id].unshift(created);
            renderModule(cfg);
            doneMessage(`${cfg.singular} creado`, result);
        }
    });
}

function moduleScreenHtml(cfg) {

    const filter = cfg.filterKey
        ? `<select id="${cfg.id}-filter" class="${INPUT} sm:w-44">
               <option value="">Todos los estados</option>
               ${cfg.filterOptions.map(function (option) {
                   return `<option value="${esc(option)}">${esc(option)}</option>`;
               }).join("")}
           </select>`
        : "";

    const create = cfg.create
        ? `<button id="${cfg.id}-create" type="button" class="rounded-md bg-[#3a3a38] px-5 py-2 text-sm font-medium text-white">${esc(cfg.create)}</button>`
        : "";

    return `
    <section id="${cfg.id}-screen" class="app-screen hidden space-y-4">
        <div class="rounded-2xl bg-white p-6 shadow-sm">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                    <h2 class="text-2xl font-bold">${esc(cfg.title)}</h2>
                    <p class="mt-2 text-sm text-[#6b6a66]">${esc(cfg.subtitle)}</p>
                </div>
                <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
                    <input id="${cfg.id}-search" type="search" placeholder="Buscar..." aria-label="Buscar en ${esc(cfg.title)}" class="${INPUT} sm:w-56">
                    ${filter}
                    ${create}
                </div>
            </div>
            <p id="${cfg.id}-mock" class="mt-3 hidden text-xs text-[#854f0b]">
                Datos temporales de demostración: se reemplazarán al conectar <code>${esc(cfg.endpoint)}</code>.
            </p>
        </div>
        <div id="${cfg.id}-table"></div>
    </section>`;
}

function renderModule(cfg) {

    const box = byId(`${cfg.id}-table`);

    if (!box) return;

    const query = (byId(`${cfg.id}-search`).value || "").toLowerCase();
    const filterEl = byId(`${cfg.id}-filter`);
    const filter = filterEl ? filterEl.value : "";

    const rows = (RS[cfg.id] || []).filter(function (row) {

        if (cfg.base && !cfg.base(row)) return false;
        if (filter && row[cfg.filterKey] !== filter) return false;

        return !query || cfg.columns.some(function (column) {
            return String(row[column.key] ?? "").toLowerCase().includes(query);
        });
    });

    cfg._view = rows;

    byId(`${cfg.id}-mock`).classList.toggle("hidden", !usingMock[cfg.id]);

    if (rows.length === 0) {
        box.innerHTML = `<div class="rounded-2xl bg-white p-6 text-sm text-[#6b6a66] shadow-sm">${esc(cfg.empty || "No hay registros para mostrar.")}</div>`;
        refreshDashboards();
        return;
    }

    const head = cfg.columns.map(function (column) {
        return `<th class="px-4 py-3 font-semibold">${esc(column.label)}</th>`;
    }).join("") + (cfg.actions && cfg.actions.length ? `<th class="px-4 py-3 font-semibold">Acciones</th>` : "");

    const body = rows.map(function (row, index) {

        const cells = cfg.columns.map(function (column) {

            let content;

            if (column.render) {
                content = column.render(row, index);
            } else if (column.badge) {
                content = badge(row[column.key]);
            } else {
                content = esc(row[column.key]);
            }

            return `<td class="px-4 py-3 ${column.strong ? "font-semibold" : ""}">${content}</td>`;
        }).join("");

        const buttons = (cfg.actions || []).map(function (action, actionIndex) {

            if (action.show && !action.show(row)) return "";

            const label = typeof action.label === "function" ? action.label(row) : action.label;

            return `<button type="button" data-act="${actionIndex}" data-i="${index}" class="${BTN.base} ${BTN[action.tone || "neutral"]}">${esc(label)}</button>`;
        }).join("");

        const actions = cfg.actions && cfg.actions.length
            ? `<td class="px-4 py-3"><div class="flex flex-wrap gap-2">${buttons}</div></td>`
            : "";

        return `<tr class="border-b last:border-b-0">${cells}${actions}</tr>`;
    }).join("");

    box.innerHTML = `
        <div class="overflow-x-auto rounded-2xl bg-white shadow-sm">
            <table class="w-full min-w-[640px] text-left text-sm">
                <thead class="bg-slate-50"><tr>${head}</tr></thead>
                <tbody>${body}</tbody>
            </table>
        </div>`;

    refreshDashboards();
}

function bindModule(cfg) {

    const box = byId(`${cfg.id}-table`);

    box.addEventListener("click", function (event) {

        const button = event.target.closest("[data-act]");

        if (!button) return;

        const action = cfg.actions[Number(button.dataset.act)];
        const row = cfg._view[Number(button.dataset.i)];

        if (action && row) action.run(row);
    });

    box.addEventListener("change", function (event) {

        const select = event.target.closest("[data-inline]");

        if (!select || !cfg.onInline) return;

        cfg.onInline(cfg._view[Number(select.dataset.i)], select.dataset.inline, select.value);
    });

    byId(`${cfg.id}-search`).addEventListener("input", function () { renderModule(cfg); });

    const filter = byId(`${cfg.id}-filter`);
    if (filter) filter.addEventListener("change", function () { renderModule(cfg); });

    const create = byId(`${cfg.id}-create`);
    if (create) create.addEventListener("click", function () { openModuleForm(cfg); });
}

async function loadModule(cfg) {

    RS[cfg.id] = clone(cfg.mock());
    usingMock[cfg.id] = true;
    renderModule(cfg);

    try {

        const response = await api.get(cfg.endpoint);
        const data = response.data && (response.data.data || response.data);

        if (Array.isArray(data)) {
            RS[cfg.id] = data;
            usingMock[cfg.id] = false;
            renderModule(cfg);
        }

    } catch (error) {
        /* API aún no disponible: se conservan los datos temporales. */
    }
}


/* ============================================================
 * CONFIGURACIÓN DE MÓDULOS — ADMINISTRADOR
 * ============================================================ */

const inlineRoleSelect = function (disabledWhen) {
    return function (row, index) {
        const disabled = disabledWhen(row) ? "disabled" : "";
        return `<select data-inline="rol" data-i="${index}" ${disabled} aria-label="Rol de ${esc(row.nombre)}" class="${INPUT} min-w-[11rem] py-1 text-xs">` +
            ROLES.map(function (role) {
                return `<option value="${esc(role)}" ${role === row.rol ? "selected" : ""}>${esc(role)}</option>`;
            }).join("") + "</select>";
    };
};

const isSelf = function (row) {
    return String(row.correo).toLowerCase() === String(getStoredUser().email || "").toLowerCase();
};

const admUsuarios = {
    id: "adm-usuarios", singular: "usuario", titleKey: "nombre",
    title: "Usuarios", subtitle: "Consulta, edita, activa o desactiva cuentas y asigna roles.",
    endpoint: "/admin/users", create: "Nuevo usuario",
    filterKey: "estado", filterOptions: ["Activo", "Inactivo", "Pendiente", "Rechazado"],
    mock: function () { return TEMP_DATA.usuarios; },
    defaults: { estado: "Activo", cuenta: "Institucional", rol: "Estudiante Investigador", fecha: new Date().toISOString().slice(0, 10) },
    columns: [
        { key: "nombre", label: "Nombre", strong: true },
        { key: "correo", label: "Correo" },
        { key: "facultad", label: "Facultad" },
        { key: "programa", label: "Programa" },
        { key: "rol", label: "Rol", render: inlineRoleSelect(function (row) { return row.estado !== "Activo" && row.estado !== "Inactivo" || isSelf(row); }) },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "nombre", label: "Nombre completo" },
        { key: "correo", label: "Correo", type: "email" },
        { key: "facultad", label: "Facultad", type: "select", options: FACULTADES },
        { key: "programa", label: "Programa", type: "select", options: PROGRAMAS },
        { key: "rol", label: "Rol", type: "select", options: ROLES },
        { key: "estado", label: "Estado", type: "select", options: ["Activo", "Inactivo"] }
    ],
    onInline: function (row, key, value) {
        mutate(admUsuarios, row, { rol: value }, {
            url: `/admin/users/${row.id}/role`,
            message: `Rol de ${row.nombre} actualizado`
        });
    }
};

admUsuarios.actions = [
    act.edit(admUsuarios),
    act.set(admUsuarios, "Desactivar", { estado: "Inactivo" }, "Usuario desactivado", { tone: "danger", show: function (row) { return row.estado === "Activo" && !isSelf(row); } }),
    act.set(admUsuarios, "Activar", { estado: "Activo" }, "Usuario activado", { tone: "success", show: function (row) { return row.estado === "Inactivo"; } })
];

const admSolicitudes = {
    id: "adm-solicitudes", singular: "solicitud", titleKey: "nombre",
    title: "Solicitudes de registro", subtitle: "Revisa las cuentas nuevas, ajusta el rol y apruébalas o recházalas.",
    endpoint: "/admin/users", empty: "No hay solicitudes pendientes.",
    base: function (row) { return row.estado === "Pendiente"; },
    mock: function () { return TEMP_DATA.usuarios; },
    columns: [
        { key: "nombre", label: "Nombre", strong: true },
        { key: "correo", label: "Correo" },
        { key: "facultad", label: "Facultad" },
        { key: "programa", label: "Programa" },
        { key: "cuenta", label: "Cuenta" },
        { key: "rol", label: "Rol a asignar", render: inlineRoleSelect(function () { return false; }) },
        { key: "fecha", label: "Fecha" }
    ],
    onInline: function (row, key, value) { row.rol = value; }
};

admSolicitudes.actions = [
    {
        label: "Aprobar", tone: "success",
        run: function (row) {
            mutate(admSolicitudes, row, { estado: "Activo", rol: row.rol }, {
                url: `/admin/users/${row.id}/approve`,
                message: `Cuenta de ${row.nombre} aprobada`
            });
        }
    },
    {
        label: "Rechazar", tone: "danger",
        run: function (row) {
            mutate(admSolicitudes, row, { estado: "Rechazado" }, {
                url: `/admin/users/${row.id}/reject`,
                message: `Solicitud de ${row.nombre} rechazada`
            });
        }
    }
];


const admSemilleros = {
    id: "adm-semilleros", singular: "semillero", titleKey: "nombre",
    title: "Semilleros", subtitle: "Crea, edita y activa o desactiva semilleros de investigación.",
    endpoint: "/admin/semilleros", create: "Nuevo semillero",
    filterKey: "estado", filterOptions: ["Activo", "Inactivo"],
    mock: function () { return TEMP_DATA.semilleros; },
    defaults: { estado: "Activo", integrantes: 0, nivel: 1 },
    columns: [
        { key: "nombre", label: "Semillero", strong: true },
        { key: "facultad", label: "Facultad" },
        { key: "linea", label: "Línea" },
        { key: "lider", label: "Docente líder" },
        { key: "integrantes", label: "Integrantes" },
        { key: "nivel", label: "Nivel", render: function (row) { return `<span class="text-[#c9a227]" aria-label="${row.nivel} de 5">${stars(row.nivel)}</span>`; } },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "nombre", label: "Nombre" },
        { key: "facultad", label: "Facultad", type: "select", options: FACULTADES },
        { key: "linea", label: "Línea de investigación" },
        { key: "lider", label: "Docente líder" },
        { key: "descripcion", label: "Descripción", type: "textarea" }
    ]
};

admSemilleros.actions = [
    act.edit(admSemilleros),
    act.set(admSemilleros, "Desactivar", { estado: "Inactivo" }, "Semillero desactivado", { tone: "danger", show: function (row) { return row.estado === "Activo"; } }),
    act.set(admSemilleros, "Activar", { estado: "Activo" }, "Semillero activado", { tone: "success", show: function (row) { return row.estado !== "Activo"; } })
];

const admProyectos = {
    id: "adm-proyectos", singular: "proyecto", titleKey: "nombre",
    title: "Proyectos", subtitle: "Supervisa los proyectos de todos los semilleros.",
    endpoint: "/admin/proyectos", create: "Nuevo proyecto",
    filterKey: "estado", filterOptions: ["Nuevo", "En curso", "Finalizado", "Suspendido"],
    mock: function () { return TEMP_DATA.proyectos; },
    defaults: { estado: "Nuevo", avance: 0, inicio: new Date().toISOString().slice(0, 10) },
    columns: [
        { key: "nombre", label: "Proyecto", strong: true },
        { key: "semillero", label: "Semillero" },
        { key: "avance", label: "Avance", render: function (row) { return `${Number(row.avance) || 0}%`; } },
        { key: "inicio", label: "Inicio" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "nombre", label: "Nombre del proyecto" },
        { key: "semillero", label: "Semillero" },
        { key: "estado", label: "Estado", type: "select", options: ["Nuevo", "En curso", "Finalizado", "Suspendido"] },
        { key: "descripcion", label: "Descripción", type: "textarea", required: false }
    ]
};
admProyectos.actions = [act.edit(admProyectos), act.remove(admProyectos)];

const MODALIDADES = ["Presencial", "Virtual", "Híbrida"];

const admEventos = {
    id: "adm-eventos", singular: "evento", titleKey: "nombre",
    title: "Eventos", subtitle: "Administra los eventos académicos y científicos.",
    endpoint: "/admin/eventos", create: "Nuevo evento",
    filterKey: "estado", filterOptions: ["Abierta", "Cerrada"],
    mock: function () { return TEMP_DATA.eventos; },
    defaults: { estado: "Abierta" },
    columns: [
        { key: "nombre", label: "Evento", strong: true },
        { key: "fecha", label: "Fecha" },
        { key: "modalidad", label: "Modalidad" },
        { key: "semillero", label: "Semillero" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "nombre", label: "Nombre del evento" },
        { key: "fecha", label: "Fecha", type: "date" },
        { key: "modalidad", label: "Modalidad", type: "select", options: MODALIDADES },
        { key: "semillero", label: "Semillero organizador" },
        { key: "estado", label: "Estado", type: "select", options: ["Abierta", "Cerrada"] }
    ]
};
admEventos.actions = [act.edit(admEventos), act.remove(admEventos)];

const admConvocatorias = {
    id: "adm-convocatorias", singular: "convocatoria", titleKey: "titulo",
    title: "Convocatorias", subtitle: "Publica y administra las convocatorias institucionales de investigación.",
    endpoint: "/admin/convocatorias", create: "Nueva convocatoria",
    filterKey: "estado", filterOptions: ["Abierta", "Cerrada"],
    mock: function () { return TEMP_CONVOCATORIAS; },
    defaults: { estado: "Abierta", postulaciones: 0 },
    columns: [
        { key: "titulo", label: "Convocatoria", strong: true },
        { key: "cierre", label: "Cierre" },
        { key: "postulaciones", label: "Postulaciones" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "titulo", label: "Título" },
        { key: "cierre", label: "Fecha de cierre", type: "date" },
        { key: "estado", label: "Estado", type: "select", options: ["Abierta", "Cerrada"] }
    ]
};
admConvocatorias.actions = [
    act.edit(admConvocatorias),
    act.set(admConvocatorias, "Cerrar", { estado: "Cerrada" }, "Convocatoria cerrada", { show: function (row) { return row.estado === "Abierta"; } }),
    act.set(admConvocatorias, "Reabrir", { estado: "Abierta" }, "Convocatoria reabierta", { tone: "success", show: function (row) { return row.estado !== "Abierta"; } }),
    act.remove(admConvocatorias)
];

const admPublicaciones = {
    id: "adm-publicaciones", singular: "publicación", titleKey: "titulo",
    title: "Publicaciones", subtitle: "Modera las publicaciones registradas por los semilleros.",
    endpoint: "/admin/publicaciones",
    filterKey: "estado", filterOptions: ["Publicada", "En revisión", "Oculta"],
    mock: function () { return TEMP_DATA.publicaciones; },
    columns: [
        { key: "titulo", label: "Título", strong: true },
        { key: "tipo", label: "Tipo" },
        { key: "semillero", label: "Semillero" },
        { key: "autor", label: "Autor" },
        { key: "reacciones", label: "♥", render: function (row) { return `♥ ${row.reacciones} · 💬 ${row.comentarios}`; } },
        { key: "estado", label: "Estado", badge: true }
    ]
};
admPublicaciones.actions = [
    act.set(admPublicaciones, "Publicar", { estado: "Publicada" }, "Publicación visible", { tone: "success", show: function (row) { return row.estado !== "Publicada"; } }),
    act.set(admPublicaciones, "Ocultar", { estado: "Oculta" }, "Publicación oculta", { show: function (row) { return row.estado === "Publicada"; } }),
    act.remove(admPublicaciones)
];

const logroColumns = [
    { key: "descripcion", label: "Logro", strong: true },
    { key: "usuario", label: "Estudiante" },
    { key: "tipo", label: "Tipo" },
    { key: "xp", label: "XP" },
    { key: "estado", label: "Estado", badge: true }
];

const logroActions = function (cfg) {
    return [
        act.set(cfg, "Aprobar", { estado: "Aprobado" }, "Logro aprobado: XP asignado", { tone: "success", show: function (row) { return row.estado === "Pendiente"; } }),
        act.set(cfg, "Rechazar", { estado: "Rechazado" }, "Logro rechazado", { tone: "danger", show: function (row) { return row.estado === "Pendiente"; } })
    ];
};

const admLogros = {
    id: "adm-logros", singular: "logro", titleKey: "descripcion",
    title: "Logros", subtitle: "Valida los logros enviados por estudiantes y docentes.",
    endpoint: "/admin/logros",
    filterKey: "estado", filterOptions: ["Pendiente", "Aprobado", "Rechazado"],
    mock: function () { return TEMP_DATA.logros; },
    columns: logroColumns
};
admLogros.actions = logroActions(admLogros);

const ADMIN_MODULES = [admUsuarios, admSolicitudes, admSemilleros, admProyectos, admEventos, admConvocatorias, admPublicaciones, admLogros];


/* ============================================================
 * CONFIGURACIÓN DE MÓDULOS — DOCENTE LÍDER
 * ============================================================ */

const docIntegrantes = {
    id: "doc-integrantes", singular: "integrante", titleKey: "nombre",
    title: "Integrantes", subtitle: "Aprueba solicitudes de vinculación y administra a los estudiantes de tu semillero.",
    endpoint: "/docente/integrantes", create: "Agregar integrante",
    filterKey: "estado", filterOptions: ["Activo", "Pendiente"],
    mock: function () { return TEMP_DATA.docIntegrantes; },
    defaults: { estado: "Activo", desde: new Date().toISOString().slice(0, 10) },
    columns: [
        { key: "nombre", label: "Nombre", strong: true },
        { key: "correo", label: "Correo" },
        { key: "programa", label: "Programa" },
        { key: "desde", label: "Desde" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "nombre", label: "Nombre completo" },
        { key: "correo", label: "Correo institucional", type: "email" },
        { key: "programa", label: "Programa", type: "select", options: PROGRAMAS }
    ]
};
docIntegrantes.actions = [
    act.set(docIntegrantes, "Aprobar", { estado: "Activo" }, "Estudiante vinculado al semillero", { tone: "success", show: function (row) { return row.estado === "Pendiente"; } }),
    {
        label: "Rechazar", tone: "danger",
        show: function (row) { return row.estado === "Pendiente"; },
        run: async function (row) {
            const result = await persist("PATCH", `/docente/integrantes/${row.id}`, { estado: "Rechazado" });
            if (!result.ok) return;
            RS[docIntegrantes.id] = RS[docIntegrantes.id].filter(function (item) { return item !== row; });
            renderModule(docIntegrantes);
            doneMessage("Solicitud rechazada", result);
        }
    },
    Object.assign(act.remove(docIntegrantes), { label: "Remover", show: function (row) { return row.estado === "Activo"; } })
];

const docProyectos = {
    id: "doc-proyectos", singular: "proyecto", titleKey: "nombre",
    title: "Proyectos", subtitle: "Registra proyectos, publica avances y cierra su ciclo de vida.",
    endpoint: "/docente/proyectos", create: "Nuevo proyecto",
    filterKey: "estado", filterOptions: ["Nuevo", "En curso", "Finalizado", "Suspendido"],
    mock: function () { return TEMP_DATA.proyectos.filter(function (p) { return p.semillero === "DataLab"; }); },
    defaults: { estado: "Nuevo", avance: 0, semillero: "DataLab", inicio: new Date().toISOString().slice(0, 10) },
    columns: [
        { key: "nombre", label: "Proyecto", strong: true },
        { key: "avance", label: "Avance", render: function (row) {
            const value = Math.max(0, Math.min(100, Number(row.avance) || 0));
            return `<div class="flex items-center gap-2"><div class="h-2 w-24 overflow-hidden rounded-full bg-[#eeeeea]"><div class="h-2 rounded-full bg-[#0c447c]" style="width:${value}%"></div></div><span class="text-xs">${value}%</span></div>`;
        } },
        { key: "inicio", label: "Inicio" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "nombre", label: "Nombre del proyecto" },
        { key: "descripcion", label: "Descripción", type: "textarea" },
        { key: "estado", label: "Estado", type: "select", options: ["Nuevo", "En curso", "Finalizado", "Suspendido"] }
    ]
};
docProyectos.actions = [
    act.edit(docProyectos),
    {
        label: "Publicar avance",
        show: function (row) { return row.estado === "En curso" || row.estado === "Nuevo"; },
        run: function (row) {
            openForm({
                title: `Avance · ${row.nombre}`,
                fields: [
                    { key: "avance", label: "Porcentaje de avance (0-100)", type: "number" },
                    { key: "nota", label: "Descripción del avance", type: "textarea" }
                ],
                values: { avance: row.avance },
                onSubmit: async function (data) {
                    const avance = Math.max(0, Math.min(100, Number(data.avance) || 0));
                    const result = await persist("POST", `/docente/proyectos/${row.id}/avances`, { avance: avance, nota: data.nota });
                    if (!result.ok) return false;
                    row.avance = avance;
                    if (row.estado === "Nuevo") row.estado = "En curso";
                    renderModule(docProyectos);
                    doneMessage("Avance publicado", result);
                }
            });
        }
    },
    act.set(docProyectos, "Cerrar", { estado: "Finalizado", avance: 100 }, "Proyecto cerrado", { show: function (row) { return row.estado === "En curso"; } })
];

const docPublicaciones = {
    id: "doc-publicaciones", singular: "publicación", titleKey: "titulo",
    title: "Publicaciones", subtitle: "Crea y administra las publicaciones de tu semillero.",
    endpoint: "/docente/publicaciones", create: "Nueva publicación",
    filterKey: "estado", filterOptions: ["Publicada", "En revisión"],
    mock: function () { return TEMP_DATA.publicaciones; },
    defaults: { estado: "En revisión", semillero: "DataLab", reacciones: 0, comentarios: 0, anio: new Date().getFullYear(), autor: getStoredUser().name || "Docente" },
    columns: [
        { key: "titulo", label: "Título", strong: true },
        { key: "tipo", label: "Tipo" },
        { key: "autor", label: "Autor" },
        { key: "anio", label: "Año" },
        { key: "reacciones", label: "Impacto", render: function (row) { return `♥ ${row.reacciones} · 💬 ${row.comentarios}`; } },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "titulo", label: "Título" },
        { key: "tipo", label: "Tipo", type: "select", options: ["Artículo", "Ponencia", "Producto", "Patente"] },
        { key: "evidencia", label: "Enlace de evidencia", type: "url", required: false }
    ]
};
docPublicaciones.actions = [
    act.edit(docPublicaciones),
    act.set(docPublicaciones, "Publicar", { estado: "Publicada" }, "Publicación visible para los seguidores", { tone: "success", show: function (row) { return row.estado !== "Publicada"; } }),
    act.remove(docPublicaciones)
];

const docEventos = {
    id: "doc-eventos", singular: "evento", titleKey: "nombre",
    title: "Eventos", subtitle: "Registra la participación de tu semillero en eventos académicos.",
    endpoint: "/docente/eventos", create: "Registrar evento",
    filterKey: "estado", filterOptions: ["Abierta", "Cerrada"],
    mock: function () { return TEMP_DATA.eventos.filter(function (e) { return e.semillero === "DataLab" || e.semillero === "BioLibre"; }).map(function (e) { return Object.assign({}, e, { semillero: "DataLab" }); }); },
    defaults: { estado: "Abierta", semillero: "DataLab" },
    columns: admEventos.columns.filter(function (c) { return c.key !== "semillero"; }),
    fields: admEventos.fields.filter(function (f) { return f.key !== "semillero" && f.key !== "estado"; })
};
docEventos.actions = [act.edit(docEventos), act.remove(docEventos)];

const docLogros = {
    id: "doc-logros", singular: "logro", titleKey: "descripcion",
    title: "Logros", subtitle: "Valida los logros de tus integrantes y registra los de tu semillero.",
    endpoint: "/docente/logros", create: "Registrar logro",
    filterKey: "estado", filterOptions: ["Pendiente", "Aprobado", "Rechazado"],
    mock: function () { return TEMP_DATA.logros; },
    defaults: { estado: "Pendiente", xp: 100, usuario: getStoredUser().name || "Docente" },
    columns: logroColumns,
    fields: [
        { key: "descripcion", label: "Descripción del logro" },
        { key: "tipo", label: "Tipo de logro", type: "select", options: ["Artículo", "Ponencia", "Producto", "Patente", "Evento"] },
        { key: "evidencia", label: "Enlace de evidencia", type: "url", required: false }
    ]
};
docLogros.actions = logroActions(docLogros);

const docConvocatorias = {
    id: "doc-convocatorias", singular: "convocatoria", titleKey: "titulo",
    title: "Convocatorias", subtitle: "Consulta las convocatorias institucionales y postula a tu semillero.",
    endpoint: "/convocatorias",
    filterKey: "estado", filterOptions: ["Abierta", "Cerrada"],
    mock: function () { return TEMP_CONVOCATORIAS; },
    columns: [
        { key: "titulo", label: "Convocatoria", strong: true },
        { key: "cierre", label: "Cierre" },
        { key: "estado", label: "Estado", badge: true },
        { key: "postulado", label: "Mi postulación", render: function (row) { return row.postulado ? badge("Aprobado").replace("Aprobado", "Enviada") : "—"; } }
    ]
};
docConvocatorias.actions = [{
    label: "Postular",
    tone: "success",
    show: function (row) { return row.estado === "Abierta" && !row.postulado; },
    run: function (row) {
        openForm({
            title: `Postular a "${row.titulo}"`,
            text: "Se enviará la postulación de tu semillero.",
            submitLabel: "Enviar postulación",
            fields: [{ key: "nota", label: "Nota para el comité", type: "textarea", required: false }],
            onSubmit: async function (data) {
                const result = await persist("POST", `/convocatorias/${row.id}/postulaciones`, data);
                if (!result.ok) return false;
                row.postulado = true;
                renderModule(docConvocatorias);
                doneMessage("Postulación enviada", result);
            }
        });
    }
}];

const DOCENTE_MODULES = [docIntegrantes, docProyectos, docPublicaciones, docEventos, docLogros, docConvocatorias];


/* ============================================================
 * DASHBOARDS
 * ============================================================ */

function rowsOf(id, filter) {
    return (RS[id] || []).filter(filter || function () { return true; });
}

function renderStats(containerId, items) {

    byId(containerId).innerHTML = items.map(function (item) {
        return `
        <article class="rounded-2xl border border-[#d8d7d1] bg-white p-5 shadow-sm">
            <p class="text-sm text-[#6b6a66]">${esc(item[0])}</p>
            <p class="mt-2 text-3xl font-bold text-[#232321]">${esc(item[1])}</p>
        </article>`;
    }).join("");
}

function pendingItem(row, extra) {
    return `<li class="flex items-center justify-between gap-3 text-sm">
        <span class="font-medium">${esc(row.nombre)}</span>
        <span class="text-[#8b8a85]">${esc(extra)}</span>
    </li>`;
}

function renderAdminDashboard() {

    const users = rowsOf("adm-usuarios");
    const pending = users.filter(function (u) { return u.estado === "Pendiente"; });

    renderStats("adm-stats", [
        ["Usuarios activos", users.filter(function (u) { return u.estado === "Activo"; }).length],
        ["Solicitudes pendientes", pending.length],
        ["Semilleros activos", rowsOf("adm-semilleros", function (s) { return s.estado === "Activo"; }).length],
        ["Proyectos en curso", rowsOf("adm-proyectos", function (p) { return p.estado === "En curso"; }).length],
        ["Publicaciones", rowsOf("adm-publicaciones", function (p) { return p.estado === "Publicada"; }).length],
        ["Eventos abiertos", rowsOf("adm-eventos", function (e) { return e.estado === "Abierta"; }).length],
        ["Convocatorias abiertas", rowsOf("adm-convocatorias", function (c) { return c.estado === "Abierta"; }).length],
        ["Logros por validar", rowsOf("adm-logros", function (l) { return l.estado === "Pendiente"; }).length]
    ]);

    const active = users.filter(function (u) { return u.estado === "Activo" || u.estado === "Inactivo"; });
    const max = Math.max(1, ...ROLES.map(function (role) {
        return active.filter(function (u) { return u.rol === role; }).length;
    }));

    byId("adm-role-bars").innerHTML = ROLES.map(function (role) {

        const count = active.filter(function (u) { return u.rol === role; }).length;

        return `<div>
            <div class="flex justify-between text-sm"><span>${esc(role)}</span><span class="font-semibold">${count}</span></div>
            <div class="mt-1 h-2 w-full overflow-hidden rounded-full bg-[#eeeeea]">
                <div class="h-2 rounded-full bg-[#0c447c]" style="width:${Math.round(count / max * 100)}%"></div>
            </div>
        </div>`;
    }).join("");

    byId("adm-pending-list").innerHTML = pending.length
        ? pending.slice(0, 5).map(function (u) { return pendingItem(u, u.programa); }).join("")
        : `<li class="text-sm text-[#6b6a66]">No hay solicitudes pendientes.</li>`;

    const counter = byId("adm-pending-count");
    if (counter) {
        counter.textContent = pending.length;
        counter.classList.toggle("hidden", pending.length === 0);
    }
}

function docMetrics() {

    return {
        integrantes: rowsOf("doc-integrantes", function (i) { return i.estado === "Activo"; }).length,
        solicitudes: rowsOf("doc-integrantes", function (i) { return i.estado === "Pendiente"; }),
        proyectos: rowsOf("doc-proyectos", function (p) { return p.estado === "En curso" || p.estado === "Nuevo"; }).length,
        publicaciones: rowsOf("doc-publicaciones", function (p) { return p.estado === "Publicada"; }).length,
        eventos: rowsOf("doc-eventos", function (e) { return e.estado === "Abierta"; }).length,
        logros: rowsOf("doc-logros", function (l) { return l.estado === "Pendiente"; }).length,
        aprobados: rowsOf("doc-logros", function (l) { return l.estado === "Aprobado"; }).length,
        reacciones: rowsOf("doc-publicaciones").reduce(function (total, p) { return total + (Number(p.reacciones) || 0); }, 0)
    };
}

function renderDocenteDashboard() {

    const sem = RS["doc-semillero"];

    if (!sem) return;

    const m = docMetrics();

    setText("[data-doc=nombre]", sem.nombre);
    setText("[data-doc=iniciales]", initialsFromName(sem.nombre));
    setText("[data-doc=descripcion]", sem.descripcion);
    setText("[data-doc=linea]", `Línea: ${sem.linea}`);
    setText("[data-doc=facultad]", sem.facultad);
    setText("[data-doc=nivel]", `${sem.nivel} ★ nivel`);

    renderStats("doc-stats", [
        ["Integrantes activos", m.integrantes],
        ["Solicitudes de vinculación", m.solicitudes.length],
        ["Proyectos activos", m.proyectos],
        ["Publicaciones", m.publicaciones],
        ["Eventos abiertos", m.eventos],
        ["Logros por validar", m.logros]
    ]);

    renderStats("doc-semillero-stats", [
        ["Integrantes", m.integrantes],
        ["Proyectos activos", m.proyectos],
        ["Publicaciones", m.publicaciones],
        ["Reacciones recibidas", m.reacciones],
        ["Logros aprobados", m.aprobados],
        ["XP acumulado", sem.xp.toLocaleString("es-CO")],
        ["Nivel", `${sem.nivel} / 5`],
        ["Eventos abiertos", m.eventos]
    ]);

    byId("doc-stars").textContent = stars(sem.nivel);
    byId("doc-xp-label").textContent = `${sem.xp.toLocaleString("es-CO")} / ${sem.xpSiguiente.toLocaleString("es-CO")} XP para el siguiente nivel`;
    byId("doc-xp-bar").style.width = `${Math.min(100, Math.round(sem.xp / sem.xpSiguiente * 100))}%`;

    byId("doc-pending-list").innerHTML = m.solicitudes.length
        ? m.solicitudes.slice(0, 4).map(function (i) { return pendingItem(i, i.programa); }).join("")
        : `<li class="text-sm text-[#6b6a66]">No hay solicitudes pendientes.</li>`;

    const open = rowsOf("doc-convocatorias", function (c) { return c.estado === "Abierta"; });

    byId("doc-open-calls").innerHTML = open.length
        ? open.slice(0, 4).map(function (c) {
            return `<li class="text-sm"><p class="font-medium">${esc(c.titulo)}</p><p class="text-[#8b8a85]">Cierre: ${esc(c.cierre)}</p></li>`;
        }).join("")
        : `<li class="text-sm text-[#6b6a66]">No hay convocatorias abiertas.</li>`;
}

function refreshDashboards() {

    const role = getUserRole();

    if (role === "admin" && byId("adm-stats")) renderAdminDashboard();
    if (role === "docente" && byId("doc-stats")) renderDocenteDashboard();
}


/* ============================================================
 * MI SEMILLERO (DOCENTE)
 * ============================================================ */

function bindDocSemillero() {

    byId("doc-edit-semillero").addEventListener("click", function () {

        const sem = RS["doc-semillero"];

        /* El docente solo edita descripción y línea. */
        openForm({
            title: "Editar información del semillero",
            fields: [
                { key: "descripcion", label: "Descripción", type: "textarea" },
                { key: "linea", label: "Línea de investigación" }
            ],
            values: sem,
            onSubmit: async function (data) {

                const result = await persist("PUT", "/docente/semillero", data);

                if (!result.ok) return false;

                Object.assign(sem, data);
                renderDocenteDashboard();
                doneMessage("Información del semillero actualizada", result);
            }
        });
    });
}

async function loadDocSemillero() {

    RS["doc-semillero"] = clone(TEMP_DATA.docSemillero);
    refreshDashboards();

    try {

        const response = await api.get("/docente/semillero");
        const data = response.data && (response.data.data || response.data);

        if (data && data.nombre) {
            RS["doc-semillero"] = Object.assign(RS["doc-semillero"], data);
            refreshDashboards();
        }

    } catch (error) {
        /* API aún no disponible: se conservan los datos temporales. */
    }
}


/* ============================================================
 * ACTIVAR ROL
 * ============================================================ */

const NAV_ITEMS = {
    admin: [
        ["adm-dashboard", "Panel"],
        ["adm-solicitudes", "Solicitudes"],
        ["adm-usuarios", "Usuarios"],
        ["adm-semilleros", "Semilleros"],
        ["adm-proyectos", "Proyectos"],
        ["adm-eventos", "Eventos"],
        ["adm-convocatorias", "Convocatorias"],
        ["adm-publicaciones", "Publicaciones"],
        ["adm-logros", "Logros"],
        ["profile", "Perfil"]
    ],
    docente: [
        ["doc-dashboard", "Inicio"],
        ["doc-semillero", "Mi semillero"],
        ["doc-integrantes", "Integrantes"],
        ["doc-proyectos", "Proyectos"],
        ["doc-publicaciones", "Publicaciones"],
        ["doc-eventos", "Eventos"],
        ["doc-logros", "Logros"],
        ["doc-convocatorias", "Convocatorias"],
        ["profile", "Perfil"]
    ]
};

Object.assign(screenTitles, {
    "adm-dashboard": "Panel administrativo",
    "adm-solicitudes": "Solicitudes de registro",
    "adm-usuarios": "Usuarios",
    "adm-semilleros": "Semilleros",
    "adm-proyectos": "Proyectos",
    "adm-eventos": "Eventos",
    "adm-convocatorias": "Convocatorias",
    "adm-publicaciones": "Publicaciones",
    "adm-logros": "Logros",
    "doc-dashboard": "Inicio",
    "doc-semillero": "Mi semillero",
    "doc-integrantes": "Integrantes",
    "doc-proyectos": "Proyectos",
    "doc-publicaciones": "Publicaciones",
    "doc-eventos": "Eventos",
    "doc-logros": "Logros",
    "doc-convocatorias": "Convocatorias"
});

const roleReady = {};

function buildRoleUI(role) {

    if (roleReady[role]) return;
    roleReady[role] = true;

    const modules = role === "admin" ? ADMIN_MODULES : DOCENTE_MODULES;
    const nav = byId(role === "admin" ? "nav-admin" : "nav-docente");

    nav.innerHTML = NAV_ITEMS[role].map(function (item, index) {

        const counter = item[0] === "adm-solicitudes"
            ? ` <span id="adm-pending-count" class="ml-1 hidden rounded-full bg-[#c9a227] px-2 py-0.5 text-xs text-white">0</span>`
            : "";

        return `<button data-screen="${item[0]}" class="rounded-xl bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-700">${esc(item[1])}${counter}</button>`;

    }).join("");

    nav.querySelectorAll("[data-screen]").forEach(function (button) {
        button.addEventListener("click", function () { showScreen(button.dataset.screen); });
    });

    byId("role-screens").insertAdjacentHTML("beforeend", modules.map(moduleScreenHtml).join(""));

    modules.forEach(bindModule);

    if (role === "docente") bindDocSemillero();

    if (role === "admin") {

        /* Usuarios y solicitudes comparten la misma lista en memoria. */
        RS["adm-usuarios"] = clone(TEMP_DATA.usuarios);
        RS["adm-solicitudes"] = RS["adm-usuarios"];
        usingMock["adm-usuarios"] = usingMock["adm-solicitudes"] = true;

        ADMIN_MODULES.forEach(function (cfg) {
            if (cfg === admUsuarios || cfg === admSolicitudes) {
                renderModule(cfg);
            } else {
                loadModule(cfg);
            }
        });

        loadUsers();

    } else {

        DOCENTE_MODULES.forEach(loadModule);
        loadDocSemillero();
    }
}

async function loadUsers() {

    try {

        const response = await api.get("/admin/users");
        const data = response.data && (response.data.data || response.data);

        if (Array.isArray(data)) {
            RS["adm-usuarios"] = RS["adm-solicitudes"] = data;
            usingMock["adm-usuarios"] = usingMock["adm-solicitudes"] = false;
            renderModule(admUsuarios);
            renderModule(admSolicitudes);
        }

    } catch (error) {
        /* API aún no disponible: se conservan los datos temporales. */
    }
}

function applyRole() {

    const role = getUserRole();
    const user = getStoredUser();

    document.body.dataset.role = role;

    byId("nav-default").classList.toggle("hidden", role === "admin" || role === "docente");

    ["admin", "docente"].forEach(function (name) {
        const nav = byId(`nav-${name}`);
        nav.classList.toggle("hidden", role !== name);
        nav.classList.toggle("flex", role === name);
    });

    setText("[data-user-name]", user.name || ROLE_LABELS[role]);

    const roleBadge = byId("profile-role");
    if (roleBadge) roleBadge.textContent = ROLE_LABELS[role];

    if (role === "admin" || role === "docente") {
        buildRoleUI(role);
    }
}

document.addEventListener("DOMContentLoaded", bindModal);
