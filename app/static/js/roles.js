/*
 * ============================================================
 * RIUL · INTERFACES POR ROL (Administrador / Docente Líder)
 * ============================================================
 *
 * - El rol sale de localStorage.user (role | rol | role_name).
 * - Estudiantes y visitantes siguen usando la interfaz original.
 * - Cada módulo declara su `endpoint`: GET lo carga y las acciones
 *   (crear/editar/aprobar...) llaman al API con persist().
 *
 * Contrato del API (implementado en app/routes/admin.py y docente.py):
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
 * CATÁLOGOS (se llenan desde GET /api/catalogos, ver student.js)
 * ============================================================ */

const ROLES = ["Administrador", "Docente Líder", "Estudiante Investigador", "Visitante"];
const FACULTADES = [];
const PROGRAMAS = [];

function clone(value) {
    return JSON.parse(JSON.stringify(value));
}


/* ============================================================
 * ESTADO + API
 * ============================================================ */

const RS = {};          // filas por módulo

function errorText(error) {
    return (error.response && error.response.data && error.response.data.message) ||
        "No se pudo conectar con el servidor";
}

/* Ejecuta la acción contra el API. Devuelve { ok, data }. */
async function persist(method, url, data) {

    try {

        const response = await api.request({ method, url, data });

        return {
            ok: true,
            data: response.data && response.data.data,
            message: response.data && response.data.message
        };

    } catch (error) {

        showMessage(errorText(error), "error");

        return { ok: false };
    }
}

function doneMessage(text, result) {
    showMessage((result && result.message) || text);
}

async function mutate(cfg, row, patch, options) {

    const opts = options || {};
    const result = await persist(
        opts.method || "PATCH",
        opts.url || `${cfg.endpoint}/${row.id}`,
        patch
    );

    if (!result.ok) return false;

    Object.assign(row, patch, result.data && typeof result.data === "object" ? result.data : {});
    renderModule(cfg);
    doneMessage(opts.message || "Cambios guardados", result);

    if (cfg.afterChange) cfg.afterChange();

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
            const options = typeof field.options === "function" ? field.options() : field.options;
            control = `<select name="${field.key}" ${required} class="${INPUT}">` +
                options.map(function (option) {
                    return `<option value="${esc(option)}" ${option === value ? "selected" : ""}>${esc(option) || "—"}</option>`;
                }).join("") +
                "</select>";
        } else if (field.type === "file") {
            control = `<input name="${field.key}" type="file" accept=".pdf,.png,.jpg,.jpeg,.docx,.pptx,.xlsx" class="${INPUT}">`;
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

        /* Archivos de evidencia: se suben primero y se envía su URL (RNF-05) */
        for (const key of Object.keys(data)) {

            if (!(data[key] instanceof File)) continue;

            if (data[key].size === 0) {
                delete data[key];
                continue;
            }

            const upload = new FormData();
            upload.append("file", data[key]);

            try {
                const response = await api.post("/uploads", upload);
                data[key] = response.data.data.url;
            } catch (error) {
                showMessage(errorText(error), "error");
                return;
            }
        }

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

                if (cfg.afterChange) cfg.afterChange();
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

            const created = Object.assign({}, cfg.defaults || {}, data, result.data || {});

            RS[cfg.id].unshift(created);

            if (created.password_temporal) {
                window.alert(
                    `Usuario creado.\n\nContraseña temporal: ${created.password_temporal}\n\n` +
                    "Compártela de forma segura; el usuario puede cambiarla desde su perfil."
                );
                delete created.password_temporal;
            } else {
                doneMessage(`${cfg.singular} creado`, result);
            }

            renderModule(cfg);

            if (cfg.afterChange) cfg.afterChange();
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

    RS[cfg.id] = [];
    renderModule(cfg);

    try {

        const response = await api.get(cfg.endpoint);
        const data = response.data && response.data.data;

        RS[cfg.id] = Array.isArray(data) ? data : [];
        renderModule(cfg);

    } catch (error) {

        if (!cfg.quietLoad) showMessage(`${cfg.title}: ${errorText(error)}`, "error");
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

function semilleroNames() {
    return (RS["adm-semilleros"] || []).map(function (s) { return s.nombre; });
}

const admUsuarios = {
    id: "adm-usuarios", singular: "usuario", titleKey: "nombre",
    title: "Usuarios", subtitle: "Consulta, edita, activa o desactiva cuentas y asigna roles.",
    endpoint: "/admin/users", create: "Nuevo usuario",
    filterKey: "estado", filterOptions: ["Activo", "Inactivo", "Pendiente", "Rechazado"],
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
    defaults: { estado: "Activo", integrantes: 0, nivel: 1 },
    columns: [
        { key: "nombre", label: "Semillero", strong: true },
        { key: "facultad", label: "Facultad" },
        { key: "linea", label: "Línea" },
        { key: "lider", label: "Docente líder (nombre o correo)" },
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
        { key: "semillero", label: "Semillero", type: "select", options: semilleroNames },
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
        { key: "semillero", label: "Semillero organizador", type: "select", options: function () { return [""].concat(semilleroNames()); }, required: false },
        { key: "estado", label: "Estado", type: "select", options: ["Abierta", "Cerrada"] }
    ]
};
admEventos.actions = [act.edit(admEventos), act.remove(admEventos)];

const admConvocatorias = {
    id: "adm-convocatorias", singular: "convocatoria", titleKey: "titulo",
    title: "Convocatorias", subtitle: "Publica y administra las convocatorias institucionales de investigación.",
    endpoint: "/admin/convocatorias", create: "Nueva convocatoria",
    filterKey: "estado", filterOptions: ["Abierta", "Cerrada"],
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
    columns: logroColumns
};
admLogros.actions = logroActions(admLogros);

const admProductos = {
    id: "adm-productos", singular: "producto", titleKey: "titulo",
    title: "Productos", subtitle: "Valida los productos registrados por los semilleros (artículos, patentes, ponencias).",
    endpoint: "/admin/productos",
    filterKey: "estado", filterOptions: ["Pendiente", "Aprobado", "Rechazado"],
    columns: [
        { key: "titulo", label: "Producto", strong: true },
        { key: "tipo", label: "Tipo" },
        { key: "semillero", label: "Semillero" },
        { key: "fecha", label: "Fecha" },
        { key: "estado", label: "Estado", badge: true }
    ]
};
admProductos.actions = [
    act.set(admProductos, "Aprobar", { estado: "Aprobado" }, "Producto aprobado", { tone: "success", show: function (row) { return row.estado === "Pendiente"; } }),
    act.set(admProductos, "Rechazar", { estado: "Rechazado" }, "Producto rechazado", { tone: "danger", show: function (row) { return row.estado === "Pendiente"; } })
];

const admFacultades = {
    id: "adm-facultades", singular: "facultad", titleKey: "nombre",
    title: "Facultades", subtitle: "Administra las facultades académicas de la universidad.",
    endpoint: "/admin/facultades", create: "Nueva facultad",
    filterKey: "estado", filterOptions: ["Activo", "Inactivo"],
    afterChange: function () { if (typeof loadCatalog === "function") loadCatalog(); },
    columns: [
        { key: "nombre", label: "Facultad", strong: true },
        { key: "programas", label: "Programas" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [{ key: "nombre", label: "Nombre de la facultad" }]
};
admFacultades.actions = [
    act.edit(admFacultades),
    act.set(admFacultades, "Desactivar", { estado: "Inactivo" }, "Facultad desactivada", { tone: "danger", show: function (row) { return row.estado === "Activo"; } }),
    act.set(admFacultades, "Activar", { estado: "Activo" }, "Facultad activada", { tone: "success", show: function (row) { return row.estado !== "Activo"; } })
];

const admProgramas = {
    id: "adm-programas", singular: "programa", titleKey: "nombre",
    title: "Programas académicos", subtitle: "Administra los programas asociados a cada facultad.",
    endpoint: "/admin/programas", create: "Nuevo programa",
    filterKey: "estado", filterOptions: ["Activo", "Inactivo"],
    afterChange: function () { if (typeof loadCatalog === "function") loadCatalog(); },
    columns: [
        { key: "nombre", label: "Programa", strong: true },
        { key: "facultad", label: "Facultad" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "nombre", label: "Nombre del programa" },
        { key: "facultad", label: "Facultad", type: "select", options: function () { return FACULTADES.slice(); } }
    ]
};
admProgramas.actions = [
    act.edit(admProgramas),
    act.set(admProgramas, "Desactivar", { estado: "Inactivo" }, "Programa desactivado", { tone: "danger", show: function (row) { return row.estado === "Activo"; } }),
    act.set(admProgramas, "Activar", { estado: "Activo" }, "Programa activado", { tone: "success", show: function (row) { return row.estado !== "Activo"; } })
];

const admBitacora = {
    id: "adm-bitacora", singular: "registro", titleKey: "accion",
    title: "Bitácora", subtitle: "Acciones críticas del sistema: validaciones, cambios de rol, XP y accesos (últimos 300 registros).",
    endpoint: "/admin/bitacora",
    columns: [
        { key: "fecha", label: "Fecha" },
        { key: "usuario", label: "Usuario", strong: true },
        { key: "accion", label: "Acción" },
        { key: "detalle", label: "Detalle" }
    ]
};

const notificaciones = {
    id: "notificaciones", singular: "notificación", titleKey: "mensaje",
    title: "Notificaciones", subtitle: "Historial de avisos sobre tu cuenta, logros, publicaciones y convocatorias.",
    endpoint: "/me/notificaciones", quietLoad: true,
    filterKey: "estado", filterOptions: ["Nueva", "Leída"],
    columns: [
        { key: "fecha", label: "Fecha" },
        { key: "mensaje", label: "Mensaje", strong: true },
        { key: "estado", label: "Estado", badge: true }
    ]
};
notificaciones.actions = [{
    label: "Marcar como leída",
    show: function (row) { return !row.leida; },
    run: async function (row) {
        const result = await persist("PATCH", `/notificaciones/${row.id}`, {});
        if (!result.ok) return;
        row.leida = true;
        row.estado = "Leída";
        renderModule(notificaciones);
        updateNotificationBadge();
    }
}];

const ADMIN_MODULES = [
    admUsuarios, admSolicitudes, admSemilleros, admProyectos, admEventos, admConvocatorias,
    admPublicaciones, admLogros, admProductos, admFacultades, admProgramas, admBitacora
];


/* ============================================================
 * CONFIGURACIÓN DE MÓDULOS — DOCENTE LÍDER
 * ============================================================ */

const docIntegrantes = {
    id: "doc-integrantes", singular: "integrante", titleKey: "nombre",
    title: "Integrantes", subtitle: "Aprueba solicitudes de vinculación y administra a los estudiantes de tu semillero.",
    endpoint: "/docente/integrantes", create: "Agregar integrante",
    filterKey: "estado", filterOptions: ["Activo", "Pendiente"],
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
        { key: "evidencia", label: "Enlace de evidencia", type: "url", required: false },
        { key: "archivo", label: "Archivo de evidencia (PDF, imagen u Office · máx. 5 MB)", type: "file", required: false }
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
    defaults: { estado: "Pendiente", xp: 100, usuario: getStoredUser().name || "Docente" },
    columns: logroColumns,
    fields: [
        { key: "descripcion", label: "Descripción del logro" },
        { key: "tipo", label: "Tipo de logro", type: "select", options: ["Artículo", "Ponencia", "Producto", "Patente", "Evento"] },
        { key: "evidencia", label: "Enlace de evidencia (o adjunta un archivo)", type: "url", required: false },
        { key: "archivo", label: "Archivo de evidencia (PDF, imagen u Office · máx. 5 MB)", type: "file", required: false }
    ]
};
docLogros.actions = logroActions(docLogros);

const docConvocatorias = {
    id: "doc-convocatorias", singular: "convocatoria", titleKey: "titulo",
    title: "Convocatorias", subtitle: "Consulta las convocatorias institucionales y postula a tu semillero.",
    endpoint: "/convocatorias",
    filterKey: "estado", filterOptions: ["Abierta", "Cerrada"],
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

const docProductos = {
    id: "doc-productos", singular: "producto", titleKey: "titulo",
    title: "Productos del semillero", subtitle: "Registra artículos, patentes y ponencias del semillero y solicita su validación.",
    endpoint: "/docente/productos", create: "Registrar producto",
    filterKey: "estado", filterOptions: ["Pendiente", "Aprobado", "Rechazado"],
    columns: [
        { key: "titulo", label: "Producto", strong: true },
        { key: "tipo", label: "Tipo" },
        { key: "fecha", label: "Fecha" },
        { key: "estado", label: "Estado", badge: true }
    ],
    fields: [
        { key: "titulo", label: "Título del producto" },
        { key: "tipo", label: "Tipo", type: "select", options: ["Artículo", "Patente", "Ponencia", "Software", "Otro"] },
        { key: "descripcion", label: "Descripción", type: "textarea", required: false }
    ]
};
docProductos.actions = [
    Object.assign(act.remove(docProductos), { show: function (row) { return row.estado === "Pendiente"; } })
];

const DOCENTE_MODULES = [docIntegrantes, docProyectos, docPublicaciones, docEventos, docLogros, docProductos, docConvocatorias];


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

/* RF-15: sin semillero a cargo se muestra el aviso y la opción de crearlo. */
function toggleDocEmpty(show) {

    document.querySelectorAll("[data-doc-empty]").forEach(function (box) {
        box.classList.toggle("hidden", !show);
    });

    const edit = byId("doc-edit-semillero");
    if (edit) edit.classList.toggle("hidden", show);
}

function bindDocSemillero() {

    document.querySelectorAll("[data-doc-create]").forEach(function (button) {

        button.addEventListener("click", function () {

            openForm({
                title: "Crear mi semillero",
                submitLabel: "Crear semillero",
                fields: [
                    { key: "nombre", label: "Nombre del semillero" },
                    { key: "descripcion", label: "Descripción", type: "textarea" },
                    { key: "linea", label: "Línea de investigación" },
                    { key: "facultad", label: "Facultad", type: "select", options: function () { return FACULTADES.slice(); } }
                ],
                onSubmit: async function (data) {

                    const result = await persist("POST", "/docente/semillero", data);

                    if (!result.ok) return false;

                    RS["doc-semillero"] = result.data;
                    toggleDocEmpty(false);
                    DOCENTE_MODULES.forEach(loadModule);
                    refreshDashboards();
                    doneMessage("Semillero creado", result);
                }
            });
        });
    });

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

    try {

        const response = await api.get("/docente/semillero");
        RS["doc-semillero"] = response.data.data;
        toggleDocEmpty(false);
        refreshDashboards();

    } catch (error) {

        /* 404: el docente aún no lidera ningún semillero (puede crearlo, RF-15) */
        if (error.response && error.response.status === 404) {
            toggleDocEmpty(true);
            return;
        }

        showMessage(errorText(error), "error");
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
        ["adm-productos", "Productos"],
        ["adm-facultades", "Facultades"],
        ["adm-programas", "Programas"],
        ["adm-reportes", "Reportes"],
        ["adm-bitacora", "Bitácora"],
        ["notificaciones", "Notificaciones"],
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
        ["doc-productos", "Productos"],
        ["doc-convocatorias", "Convocatorias"],
        ["notificaciones", "Notificaciones"],
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
    "doc-convocatorias": "Convocatorias",
    "adm-productos": "Productos",
    "adm-facultades": "Facultades",
    "adm-programas": "Programas académicos",
    "adm-reportes": "Reportes e indicadores",
    "adm-bitacora": "Bitácora",
    "doc-productos": "Productos del semillero",
    "notificaciones": "Notificaciones"
});

const roleReady = {};

function buildRoleUI(role) {

    if (roleReady[role]) return;
    roleReady[role] = true;

    const modules = role === "admin" ? ADMIN_MODULES : DOCENTE_MODULES;
    const nav = byId(role === "admin" ? "nav-admin" : "nav-docente");

    nav.innerHTML = NAV_ITEMS[role].map(function (item) {

        const counter = item[0] === "adm-solicitudes"
            ? ` <span id="adm-pending-count" class="ml-1 hidden rounded-full bg-[#c9a227] px-2 py-0.5 text-xs text-white">0</span>`
            : item[0] === "notificaciones"
                ? ` <span data-notif-badge class="ml-1 hidden rounded-full bg-[#c9a227] px-2 py-0.5 text-xs text-white">0</span>`
                : "";

        return `<button data-screen="${item[0]}" class="rounded-xl bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-700">${esc(item[1])}${counter}</button>`;

    }).join("");

    nav.querySelectorAll("[data-screen]").forEach(function (button) {
        button.addEventListener("click", function () { showScreen(button.dataset.screen); });
    });

    byId("role-screens").insertAdjacentHTML("beforeend", modules.map(moduleScreenHtml).join(""));

    modules.forEach(bindModule);

    if (role === "docente") bindDocSemillero();
    if (role === "admin") bindReports();

    if (role === "admin") {

        /* Usuarios y solicitudes comparten la misma lista en memoria. */
        loadUsers();

        ADMIN_MODULES.forEach(function (cfg) {
            if (cfg !== admUsuarios && cfg !== admSolicitudes) loadModule(cfg);
        });

    } else {

        DOCENTE_MODULES.forEach(loadModule);
        loadDocSemillero();
    }
}

async function loadUsers() {

    RS["adm-usuarios"] = RS["adm-solicitudes"] = [];

    try {

        const response = await api.get("/admin/users");
        RS["adm-usuarios"] = RS["adm-solicitudes"] = response.data.data;

    } catch (error) {
        showMessage(`Usuarios: ${errorText(error)}`, "error");
    }

    renderModule(admUsuarios);
    renderModule(admSolicitudes);
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

    buildNotifications();

    /* Los visitantes sin sesión no tienen notificaciones */
    const guestOnly = !localStorage.getItem("access_token");
    document.querySelectorAll('[data-screen="notificaciones"]').forEach(function (button) {
        button.classList.toggle("hidden", guestOnly);
    });
}

/* ============================================================
 * NOTIFICACIONES (todos los roles con sesión)
 * ============================================================ */

let notificationsReady = false;

function updateNotificationBadge() {

    const unread = (RS.notificaciones || []).filter(function (n) { return !n.leida; }).length;

    document.querySelectorAll("[data-notif-badge]").forEach(function (badgeEl) {
        badgeEl.textContent = unread;
        badgeEl.classList.toggle("hidden", unread === 0);
    });
}

async function loadNotifications() {
    await loadModule(notificaciones);
    updateNotificationBadge();
}

function buildNotifications() {

    if (notificationsReady || !localStorage.getItem("access_token")) return;
    notificationsReady = true;

    byId("role-screens").insertAdjacentHTML("beforeend", moduleScreenHtml(notificaciones));
    bindModule(notificaciones);

    byId("notificaciones-search").insertAdjacentHTML(
        "afterend",
        `<button id="notificaciones-read-all" type="button" class="rounded-md border border-[#c9c8c2] bg-[#eeeeea] px-4 py-2 text-sm font-medium text-[#3a3a38]">Marcar todas como leídas</button>`
    );

    byId("notificaciones-read-all").addEventListener("click", async function () {

        const result = await persist("POST", "/notificaciones/leer-todas", {});

        if (!result.ok) return;

        (RS.notificaciones || []).forEach(function (n) { n.leida = true; n.estado = "Leída"; });
        renderModule(notificaciones);
        updateNotificationBadge();
    });

    loadNotifications();
}


/* ============================================================
 * REPORTES E INDICADORES (ADMINISTRADOR · RF-50, RF-51, RF-53)
 * ============================================================ */

let rankingPublished = true;

function bindReports() {

    byId("rep-generar").addEventListener("click", loadIndicators);

    document.querySelectorAll("[data-report]").forEach(function (button) {
        button.addEventListener("click", function () { downloadReport(button.dataset.report); });
    });

    byId("rep-ranking-toggle").addEventListener("click", async function () {

        const result = await persist("PUT", "/admin/config/ranking", { publicado: !rankingPublished });

        if (!result.ok) return;

        rankingPublished = !!result.data.publicado;
        renderRankingState();
        doneMessage("Ranking actualizado", result);
    });
}

function renderRankingState() {
    byId("rep-ranking-state").textContent = rankingPublished
        ? "El ranking institucional está publicado."
        : "El ranking institucional está oculto para los usuarios.";
    byId("rep-ranking-toggle").textContent = rankingPublished ? "Ocultar ranking" : "Publicar ranking";
}

async function loadIndicators() {

    try {

        const response = await api.get("/admin/indicadores", {
            params: {
                agrupar: byId("rep-agrupar").value,
                desde: byId("rep-desde").value || undefined,
                hasta: byId("rep-hasta").value || undefined
            }
        });

        const data = response.data.data;
        const total = data.resumen;

        renderStats("rep-resumen", [
            ["Semilleros activos", total.semilleros],
            ["Investigadores", total.investigadores],
            ["Proyectos", total.proyectos],
            ["Publicaciones", total.publicaciones],
            ["Logros aprobados", total.logros],
            ["XP total", total.xp_total]
        ]);

        byId("rep-tabla").innerHTML = `
            <div class="overflow-x-auto rounded-2xl bg-white shadow-sm">
                <table class="w-full min-w-[640px] text-left text-sm">
                    <thead class="bg-slate-50"><tr>
                        ${["Grupo", "Semilleros", "Integrantes", "Proyectos", "Publicaciones", "Logros", "XP"].map(function (h) {
                            return `<th class="px-4 py-3 font-semibold">${h}</th>`;
                        }).join("")}
                    </tr></thead>
                    <tbody>${data.filas.map(function (row) {
                        return `<tr class="border-b last:border-b-0">
                            <td class="px-4 py-3 font-semibold">${esc(row.grupo)}</td>
                            <td class="px-4 py-3">${row.semilleros}</td>
                            <td class="px-4 py-3">${row.integrantes}</td>
                            <td class="px-4 py-3">${row.proyectos}</td>
                            <td class="px-4 py-3">${row.publicaciones}</td>
                            <td class="px-4 py-3">${row.logros}</td>
                            <td class="px-4 py-3">${row.xp}</td>
                        </tr>`;
                    }).join("")}</tbody>
                </table>
            </div>`;

    } catch (error) {
        showMessage(errorText(error), "error");
    }
}

async function downloadReport(type) {

    try {

        const response = await api.get(`/admin/reportes/${type}`, { responseType: "blob" });
        const url = URL.createObjectURL(response.data);
        const link = document.createElement("a");

        link.href = url;
        link.download = `riul-${type}.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);

    } catch (error) {
        showMessage("No se pudo generar el reporte", "error");
    }
}

async function onRoleScreen(name) {

    if (name === "notificaciones" && notificationsReady) loadNotifications();

    if (name === "adm-reportes") {

        loadIndicators();

        try {
            const response = await api.get("/admin/config/ranking");
            rankingPublished = !!response.data.data.publicado;
            renderRankingState();
        } catch (error) {
            showMessage(errorText(error), "error");
        }
    }
}

/* Cada cambio de pantalla puede refrescar datos de su módulo */
const baseShowScreen = showScreen;

showScreen = function (name) {
    baseShowScreen(name);
    onRoleScreen(name);
};

document.addEventListener("DOMContentLoaded", bindModal);
