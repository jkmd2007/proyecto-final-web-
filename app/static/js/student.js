/*
 * ============================================================
 * RIUL · PANTALLAS PÚBLICAS Y DE ESTUDIANTE (conectadas al API)
 * ============================================================
 *
 * Usa utilidades de roles.js (openForm, esc, badge, stars, BTN, errorText).
 * Las consultas públicas funcionan sin sesión (RF-13); las acciones
 * (vincularse, reaccionar, comentar, postular...) exigen iniciar sesión.
 */

const CATALOG = { facultades: [], roles: [], tipos_logro: [], categorias: [] };

function hasSession() {
    return !!localStorage.getItem("access_token");
}

function isStudent() {
    return hasSession() && getUserRole() === "estudiante";
}

async function fetchData(url, params) {
    const response = await api.get(url, { params });
    return response.data.data;
}

async function safely(task) {
    try {
        return await task();
    } catch (error) {
        showMessage(errorText(error), "error");
    }
}

function needLogin(text) {
    showMessage(text || "Inicia sesión para realizar esta acción", "error");
}

function emptyBox(text) {
    return `<div class="rounded-2xl bg-white p-6 text-sm text-[#6b6a66] shadow-sm">${esc(text)}</div>`;
}

function tableHtml(head, rows) {

    return `<div class="overflow-x-auto rounded-2xl bg-white shadow-sm">
        <table class="w-full min-w-[560px] text-left text-sm">
            <thead class="bg-slate-50"><tr>${head.map(function (h) {
                return `<th class="px-4 py-3 font-semibold">${esc(h)}</th>`;
            }).join("")}</tr></thead>
            <tbody>${rows.map(function (row) {
                return `<tr class="border-b last:border-b-0">${row.map(function (cell) {
                    return `<td class="px-4 py-3">${cell}</td>`;
                }).join("")}</tr>`;
            }).join("")}</tbody>
        </table>
    </div>`;
}

function smallButton(label, attrs, tone) {
    return `<button type="button" ${attrs} class="${BTN.base} ${BTN[tone || "neutral"]}">${esc(label)}</button>`;
}

function evidenceLinks(items) {

    return (items || []).map(function (item, index) {
        const href = item.url.startsWith("/") ? item.url : item.url;
        return `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer" class="text-xs text-[#0c447c] underline">Evidencia ${index + 1}</a>`;
    }).join(" · ");
}

function debounce(fn, delay) {

    let timer;

    return function () {
        clearTimeout(timer);
        timer = setTimeout(fn, delay);
    };
}


/* ============================================================
 * CATÁLOGOS (facultades, programas, tipos de logro)
 * ============================================================ */

async function loadCatalog() {

    try {

        const data = await fetchData("/catalogos");

        CATALOG.facultades = data.facultades;
        CATALOG.roles = data.roles;
        CATALOG.tipos_logro = data.tipos_logro;
        CATALOG.categorias = data.categorias;

        /* Los arrays se modifican en sitio: roles.js los usa en sus formularios */
        FACULTADES.splice(0, FACULTADES.length, ...data.facultades.map(function (f) { return f.nombre; }));

        const programs = [];
        data.facultades.forEach(function (f) {
            f.programas.forEach(function (p) { if (!programs.includes(p)) programs.push(p); });
        });
        PROGRAMAS.splice(0, PROGRAMAS.length, ...programs);

        fillAcademicSelects();

    } catch (error) {
        /* Sin API no se pueden registrar usuarios; el resto muestra sus propios errores */
    }
}

function fillAcademicSelects() {

    const faculty = document.getElementById("register-faculty");
    const program = document.getElementById("register-program");
    const ranking = document.getElementById("ranking-facultad");

    if (faculty) {
        const current = faculty.value;
        faculty.innerHTML = `<option value="">Selecciona...</option>` +
            FACULTADES.map(function (name) { return `<option value="${esc(name)}">${esc(name)}</option>`; }).join("");
        faculty.value = current;
    }

    if (ranking) {
        const current = ranking.value;
        ranking.innerHTML = `<option value="">Todas las facultades</option>` +
            FACULTADES.map(function (name) { return `<option value="${esc(name)}">${esc(name)}</option>`; }).join("");
        ranking.value = current;
    }

    fillProgramOptions();

    if (faculty && program && !faculty.dataset.bound) {
        faculty.dataset.bound = "1";
        faculty.addEventListener("change", fillProgramOptions);
    }
}

function fillProgramOptions() {

    const faculty = document.getElementById("register-faculty");
    const program = document.getElementById("register-program");

    if (!program) return;

    const selected = CATALOG.facultades.find(function (f) { return f.nombre === faculty.value; });
    const names = selected ? selected.programas : PROGRAMAS;

    program.innerHTML = `<option value="">Selecciona...</option>` +
        names.map(function (name) { return `<option value="${esc(name)}">${esc(name)}</option>`; }).join("");
}


/* ============================================================
 * INICIO: indicadores públicos (RF-54)
 * ============================================================ */

async function loadImpact() {

    await safely(async function () {

        const data = await fetchData("/public/indicadores");

        document.getElementById("stat-semilleros").textContent = data.resumen.semilleros;
        document.getElementById("stat-proyectos").textContent = data.resumen.proyectos_en_curso;
        document.getElementById("stat-publicaciones").textContent = data.resumen.publicaciones;
    });
}


/* ============================================================
 * SEMILLEROS (RF-14, RF-17, RF-30)
 * ============================================================ */

let currentSemillero = null;

async function loadSemilleros() {

    const box = document.getElementById("semilleros-list");
    const query = document.getElementById("semilleros-search").value.trim();

    await safely(async function () {

        const rows = await fetchData("/public/semilleros", { q: query || undefined });

        box.innerHTML = rows.length ? rows.map(function (s) {

            const status = s.mi_estado
                ? badge(s.mi_estado === "Activo" ? "Activo" : s.mi_estado).replace(">Activo<", ">Integrante<")
                : "";

            return `<article class="${CARD}">
                <div class="flex items-start justify-between gap-3">
                    <h3 class="text-lg font-semibold">${esc(s.nombre)}</h3>
                    ${status}
                </div>
                <p class="mt-1 text-xs text-[#6b6a66]">${esc(s.facultad)} · ${esc(s.linea)}</p>
                <p class="mt-3 line-clamp-3 text-sm text-[#6b6a66]">${esc(s.descripcion)}</p>
                <p class="mt-3 text-sm text-[#c9a227]" aria-label="${s.nivel} de 5 estrellas">${stars(s.nivel)}</p>
                <div class="mt-3 flex items-center justify-between text-xs text-[#6b6a66]">
                    <span>${s.integrantes} integrantes</span>
                    ${smallButton("Ver semillero", `data-open="${s.id}"`)}
                </div>
            </article>`;
        }).join("") : emptyBox("No se encontraron semilleros.");
    });
}

async function openSemillero(id) {

    await safely(async function () {

        const s = await fetchData(`/public/semilleros/${id}`);
        currentSemillero = s;

        const text = function (key, value) { document.getElementById(key).textContent = value; };

        text("sd-nombre", s.nombre);
        text("sd-descripcion", s.descripcion);
        text("sd-linea", `Línea: ${s.linea}`);
        text("sd-facultad", s.facultad);
        text("sd-lider", s.lider ? `Docente líder: ${s.lider}` : "Sin docente líder");
        text("sd-iniciales", s.nombre.slice(0, 2).toUpperCase());
        text("sd-stars", stars(s.nivel));
        text("sd-xp", `Nivel ${s.nivel} · ${s.xp} XP`);

        renderSemilleroActions();

        document.getElementById("sd-panel-publicaciones").innerHTML = s.publicaciones.length
            ? s.publicaciones.map(function (p) {
                return `<article class="${CARD}">
                    <p class="font-semibold">${esc(p.titulo)}</p>
                    <p class="mt-1 text-xs text-[#6b6a66]">${esc(p.tipo)} · ${esc(p.autor)} · ${esc(p.fecha)}</p>
                    <p class="mt-2 text-xs text-[#6b6a66]">♥ ${p.reacciones} · 💬 ${p.comentarios}</p>
                </article>`;
            }).join("")
            : emptyBox("Este semillero aún no tiene publicaciones.");

        document.getElementById("sd-panel-proyectos").innerHTML = s.proyectos.length
            ? tableHtml(["Proyecto", "Estado", "Avance"], s.proyectos.map(function (p) {
                return [`<span class="font-semibold">${esc(p.nombre)}</span>`, badge(p.estado), `${p.avance}%`];
            }))
            : emptyBox("Este semillero aún no tiene proyectos.");

        document.getElementById("sd-panel-integrantes").innerHTML = s.integrantes.length
            ? tableHtml(["Integrante", "Programa", "XP"], s.integrantes.map(function (m) {
                return [`<span class="font-semibold">${esc(m.nombre)}</span>`, esc(m.programa), m.xp];
            }))
            : emptyBox("Este semillero aún no tiene integrantes.");

        document.getElementById("sd-panel-logros").innerHTML = s.logros.length
            ? `<article class="${CARD}"><ul class="space-y-3 text-sm text-[#6b6a66]">${s.logros.map(function (l) {
                return `<li>★ ${esc(l)}</li>`;
            }).join("")}</ul></article>`
            : emptyBox("Aún no hay logros aprobados.");

        document.getElementById("semillero-detail").classList.remove("hidden");
        document.getElementById("semillero-detail").scrollIntoView({ behavior: "smooth", block: "start" });
    });
}

function renderSemilleroActions() {

    const s = currentSemillero;
    const join = document.getElementById("join-semillero");
    const follow = document.getElementById("follow-semillero");

    join.classList.toggle("hidden", !isStudent() || s.mi_estado === "Activo");
    join.disabled = s.mi_estado === "Pendiente";
    join.textContent = s.mi_estado === "Pendiente" ? "Solicitud pendiente" : "Solicitar vinculación";
    join.classList.toggle("opacity-60", join.disabled);

    follow.classList.toggle("hidden", !hasSession());
    follow.textContent = s.siguiendo ? "Siguiendo ✓" : "Seguir";
}

function bindSemilleros() {

    document.getElementById("semilleros-search").addEventListener("input", debounce(loadSemilleros, 300));

    document.getElementById("semilleros-list").addEventListener("click", function (event) {
        const button = event.target.closest("[data-open]");
        if (button) openSemillero(button.dataset.open);
    });

    document.getElementById("close-semillero").addEventListener("click", function () {
        document.getElementById("semillero-detail").classList.add("hidden");
        currentSemillero = null;
    });

    document.querySelectorAll(".semillero-tab").forEach(function (tab) {
        tab.addEventListener("click", function () {
            document.querySelectorAll(".semillero-panel").forEach(function (panel) {
                panel.classList.toggle("hidden", panel.id !== `sd-panel-${tab.dataset.tab}`);
            });
        });
    });

    document.getElementById("join-semillero").addEventListener("click", async function () {

        if (!currentSemillero) return;

        await safely(async function () {
            const response = await api.post(`/semilleros/${currentSemillero.id}/vinculacion`);
            currentSemillero.mi_estado = "Pendiente";
            renderSemilleroActions();
            showMessage(response.data.message);
            loadSemilleros();
        });
    });

    document.getElementById("follow-semillero").addEventListener("click", async function () {

        if (!currentSemillero) return;

        await safely(async function () {
            const following = !currentSemillero.siguiendo;
            await api.request({
                method: following ? "POST" : "DELETE",
                url: `/semilleros/${currentSemillero.id}/seguir`
            });
            currentSemillero.siguiendo = following;
            renderSemilleroActions();
            showMessage(following ? "Ahora sigues este semillero" : "Dejaste de seguir este semillero");
        });
    });

    /* Búsqueda global del inicio */
    document.getElementById("search-input").addEventListener("keydown", function (event) {

        if (event.key !== "Enter") return;

        document.getElementById("semilleros-search").value = this.value.trim();
        showScreen("semilleros");
    });
}


/* ============================================================
 * PROYECTOS (RF-22)
 * ============================================================ */

async function loadProyectos() {

    const box = document.getElementById("proyectos-list");
    const query = document.getElementById("proyectos-search").value.trim();

    await safely(async function () {

        const rows = await fetchData("/public/proyectos", { q: query || undefined });

        box.innerHTML = rows.length
            ? tableHtml(["Proyecto", "Semillero", "Avance", "Estado", ""], rows.map(function (p) {
                return [
                    `<span class="font-semibold">${esc(p.nombre)}</span>`,
                    esc(p.semillero),
                    `<div class="flex items-center gap-2"><div class="h-2 w-24 overflow-hidden rounded-full bg-[#eeeeea]"><div class="h-2 rounded-full bg-[#0c447c]" style="width:${p.avance}%"></div></div><span class="text-xs">${p.avance}%</span></div>`,
                    badge(p.estado),
                    p.puedo_aportar ? smallButton("Registrar aporte", `data-aporte="${p.id}"`) : ""
                ];
            }))
            : emptyBox("No hay proyectos para mostrar.");
    });
}

function bindProyectos() {

    document.getElementById("proyectos-search").addEventListener("input", debounce(loadProyectos, 300));

    document.getElementById("proyectos-list").addEventListener("click", function (event) {

        const button = event.target.closest("[data-aporte]");
        if (!button) return;

        const id = button.dataset.aporte;

        openForm({
            title: "Registrar aporte al proyecto",
            fields: [{ key: "descripcion", label: "Describe tu aporte", type: "textarea" }],
            onSubmit: async function (data) {
                const result = await persist("POST", `/proyectos/${id}/aportes`, data);
                if (!result.ok) return false;
                doneMessage("Aporte registrado", result);
            }
        });
    });
}


/* ============================================================
 * PUBLICACIONES (RF-24, RF-28, RF-29)
 * ============================================================ */

async function loadPublicaciones() {

    const box = document.getElementById("publicaciones-list");
    const query = document.getElementById("publicaciones-search").value.trim();

    document.getElementById("publicaciones-create").classList.toggle("hidden", !isStudent());

    await safely(async function () {

        const rows = await fetchData("/public/publicaciones", { q: query || undefined });

        box.innerHTML = rows.length ? rows.map(function (p) {

            return `<article class="${CARD}">
                <div class="flex items-start justify-between gap-3">
                    <h3 class="text-lg font-semibold">${esc(p.titulo)}</h3>
                    <span class="rounded-full bg-[#eeeeea] px-3 py-1 text-xs font-medium text-[#3a3a38]">${esc(p.tipo)}</span>
                </div>
                <p class="mt-1 text-xs text-[#6b6a66]">${esc(p.autor)} · ${esc(p.semillero)} · ${esc(p.fecha)}</p>
                ${p.contenido ? `<p class="mt-3 text-sm text-[#6b6a66]">${esc(p.contenido)}</p>` : ""}
                <p class="mt-3">${evidenceLinks(p.evidencias)}</p>
                <div class="mt-4 flex flex-wrap items-center gap-2">
                    ${smallButton(`${p.yo_reaccione ? "♥" : "♡"} ${p.reacciones}`, `data-like="${p.id}" aria-label="Me gusta"`, p.yo_reaccione ? "success" : "neutral")}
                    ${smallButton(`💬 ${p.comentarios}`, `data-comments="${p.id}" aria-label="Comentarios"`)}
                    ${smallButton(`↗ ${p.compartidos}`, `data-share="${p.id}" aria-label="Compartir"`)}
                    <span class="ml-auto text-xs text-[#8b8a85]">👁 ${p.vistas}</span>
                </div>
            </article>`;
        }).join("") : emptyBox("Aún no hay publicaciones.");
    });
}

function openComments(id) {

    safely(async function () {

        const pub = await fetchData(`/public/publicaciones/${id}`);

        const list = pub.lista_comentarios.length
            ? pub.lista_comentarios.map(function (c) {
                return `${c.autor} (${c.fecha}): ${c.contenido}`;
            }).join("\n\n")
            : "Aún no hay comentarios.";

        openForm({
            title: pub.titulo,
            text: list,
            submitLabel: hasSession() ? "Comentar" : "Cerrar",
            fields: hasSession() ? [{ key: "contenido", label: "Escribe un comentario", type: "textarea" }] : [],
            onSubmit: async function (data) {

                if (!hasSession()) return;

                const result = await persist("POST", `/publicaciones/${id}/comentarios`, data);
                if (!result.ok) return false;

                doneMessage("Comentario publicado", result);
                loadPublicaciones();
            }
        });
    });
}

function bindPublicaciones() {

    document.getElementById("publicaciones-search").addEventListener("input", debounce(loadPublicaciones, 300));

    document.getElementById("publicaciones-list").addEventListener("click", async function (event) {

        const like = event.target.closest("[data-like]");
        const comments = event.target.closest("[data-comments]");
        const share = event.target.closest("[data-share]");

        if (comments) {
            openComments(comments.dataset.comments);
            return;
        }

        if (!like && !share) return;

        if (!hasSession()) {
            needLogin("Inicia sesión para reaccionar o compartir");
            return;
        }

        await safely(async function () {

            if (like) {
                await api.post(`/publicaciones/${like.dataset.like}/reaccion`);
            } else {
                const response = await api.post(`/publicaciones/${share.dataset.share}/compartir`);
                const link = window.location.origin + response.data.data.enlace;

                if (navigator.clipboard) await navigator.clipboard.writeText(link);
                showMessage("Enlace copiado al portapapeles");
            }

            loadPublicaciones();
        });
    });

    document.getElementById("publicaciones-create").addEventListener("click", function () {

        openForm({
            title: "Nueva publicación",
            text: "Tu publicación quedará en revisión hasta que tu docente líder la publique.",
            fields: [
                { key: "titulo", label: "Título" },
                { key: "tipo", label: "Tipo", type: "select", options: function () { return CATALOG.categorias; } },
                { key: "contenido", label: "Resumen", type: "textarea", required: false },
                { key: "evidencia", label: "Enlace de evidencia", type: "url", required: false },
                { key: "archivo", label: "Archivo de evidencia (PDF, imagen u Office · máx. 5 MB)", type: "file", required: false }
            ],
            onSubmit: async function (data) {
                const result = await persist("POST", "/publicaciones", data);
                if (!result.ok) return false;
                doneMessage("Publicación enviada a revisión", result);
            }
        });
    });
}


/* ============================================================
 * EVENTOS (RF-34) Y CONVOCATORIAS (RF-33)
 * ============================================================ */

async function loadEventos() {

    const box = document.getElementById("eventos-list");

    await safely(async function () {

        const rows = await fetchData("/public/eventos");

        box.innerHTML = rows.length ? rows.map(function (e) {

            const action = hasSession() && e.estado === "Abierta"
                ? smallButton(e.participo ? "Cancelar participación" : "Participar", `data-event="${e.id}" data-joined="${e.participo ? 1 : 0}"`, e.participo ? "neutral" : "success")
                : "";

            return `<article class="${CARD}">
                <div class="flex items-start justify-between gap-3">
                    <h3 class="text-lg font-semibold">${esc(e.nombre)}</h3>
                    ${badge(e.estado)}
                </div>
                <p class="mt-1 text-xs text-[#6b6a66]">${esc(e.fecha || "Fecha por definir")} · ${esc(e.modalidad)}${e.semillero ? " · " + esc(e.semillero) : ""}</p>
                <div class="mt-4 flex items-center justify-between">
                    <span class="text-xs text-[#6b6a66]">${e.participantes} participantes</span>
                    ${action}
                </div>
            </article>`;
        }).join("") : emptyBox("No hay eventos registrados.");
    });
}

function bindEventos() {

    document.getElementById("eventos-list").addEventListener("click", async function (event) {

        const button = event.target.closest("[data-event]");
        if (!button) return;

        await safely(async function () {
            const joined = button.dataset.joined === "1";
            const response = await api.request({
                method: joined ? "DELETE" : "POST",
                url: `/eventos/${button.dataset.event}/participar`
            });
            showMessage(response.data.message);
            loadEventos();
        });
    });
}

async function loadConvocatorias() {

    const box = document.getElementById("convocatorias-list");
    const canApply = hasSession() && ["estudiante", "docente"].includes(getUserRole());

    await safely(async function () {

        const rows = await fetchData("/convocatorias");

        box.innerHTML = rows.length ? rows.map(function (c) {

            const action = canApply && c.estado === "Abierta"
                ? (c.postulado
                    ? `<span class="text-xs font-medium text-[#3b6d11]">Postulación enviada ✓</span>`
                    : smallButton("Postularme", `data-apply="${c.id}" data-title="${esc(c.titulo)}"`, "success"))
                : "";

            return `<article class="${CARD}">
                <div class="flex items-start justify-between gap-3">
                    <h3 class="text-lg font-semibold">${esc(c.titulo)}</h3>
                    ${badge(c.estado)}
                </div>
                ${c.descripcion ? `<p class="mt-2 text-sm text-[#6b6a66]">${esc(c.descripcion)}</p>` : ""}
                <p class="mt-2 text-xs text-[#6b6a66]">Cierre: ${esc(c.cierre || "sin fecha")}</p>
                <div class="mt-4 flex items-center justify-between">
                    <span class="text-xs text-[#6b6a66]">${c.postulaciones} postulaciones</span>
                    ${action}
                </div>
            </article>`;
        }).join("") : emptyBox("No hay convocatorias publicadas.");
    });
}

function bindConvocatorias() {

    document.getElementById("convocatorias-list").addEventListener("click", function (event) {

        const button = event.target.closest("[data-apply]");
        if (!button) return;

        const id = button.dataset.apply;

        openForm({
            title: `Postular a "${button.dataset.title}"`,
            submitLabel: "Enviar postulación",
            fields: [{ key: "nota", label: "Nota para el comité", type: "textarea", required: false }],
            onSubmit: async function (data) {
                const result = await persist("POST", `/convocatorias/${id}/postulaciones`, data);
                if (!result.ok) return false;
                doneMessage("Postulación enviada", result);
                loadConvocatorias();
            }
        });
    });
}


/* ============================================================
 * LOGROS (RF-35 a RF-38)
 * ============================================================ */

async function loadLogros() {

    const box = document.getElementById("logros-list");
    const create = document.getElementById("logros-create");

    create.classList.toggle("hidden", !isStudent());

    if (!isStudent()) {
        box.innerHTML = emptyBox(
            hasSession()
                ? "Los logros se registran con una cuenta de estudiante investigador. Los docentes los gestionan desde su panel."
                : "Inicia sesión como estudiante investigador para registrar y consultar tus logros."
        );
        return;
    }

    await safely(async function () {

        const rows = await fetchData("/me/logros");

        box.innerHTML = rows.length
            ? tableHtml(["Logro", "Tipo", "XP", "Estado", "Observación", "Evidencia"], rows.map(function (l) {
                return [
                    `<span class="font-semibold">${esc(l.descripcion)}</span>`,
                    esc(l.tipo), l.xp, badge(l.estado), esc(l.observacion), evidenceLinks(l.evidencias)
                ];
            }))
            : emptyBox("Aún no has registrado logros.");
    });
}

function bindLogros() {

    document.getElementById("logros-create").addEventListener("click", function () {

        openForm({
            title: "Registrar logro",
            text: "Adjunta una evidencia (enlace o archivo). Se enviará a validación.",
            submitLabel: "Enviar a validación",
            fields: [
                { key: "descripcion", label: "Descripción del logro" },
                { key: "tipo", label: "Tipo de logro", type: "select", options: function () { return CATALOG.tipos_logro.map(function (t) { return t.nombre; }); } },
                { key: "evidencia", label: "Enlace de evidencia", type: "url", required: false },
                { key: "archivo", label: "Archivo de evidencia (PDF, imagen u Office · máx. 5 MB)", type: "file", required: false }
            ],
            onSubmit: async function (data) {
                const result = await persist("POST", "/me/logros", data);
                if (!result.ok) return false;
                doneMessage("Logro enviado a validación", result);
                loadLogros();
            }
        });
    });
}


/* ============================================================
 * RANKING (RF-46)
 * ============================================================ */

async function loadRanking() {

    const box = document.getElementById("ranking-list");

    await safely(async function () {

        const data = await fetchData("/public/ranking", {
            tipo: document.getElementById("ranking-tipo").value,
            facultad: document.getElementById("ranking-facultad").value || undefined
        });

        if (!data.publicado) {
            box.innerHTML = emptyBox("El ranking institucional aún no ha sido publicado por la administración.");
            return;
        }

        box.innerHTML = data.filas.length
            ? tableHtml(["#", "Nombre", "Facultad", "XP", "Nivel"], data.filas.map(function (r) {
                return [
                    `<span class="font-semibold">${r.puesto}</span>`,
                    `<span class="font-semibold">${esc(r.nombre)}</span>`,
                    esc(r.facultad), r.xp,
                    `<span class="text-[#c9a227]" aria-label="${r.nivel} de 5">${stars(r.nivel)}</span>`
                ];
            }))
            : emptyBox("No hay datos para este ranking.");
    });
}

function bindRanking() {
    document.getElementById("ranking-tipo").addEventListener("change", loadRanking);
    document.getElementById("ranking-facultad").addEventListener("change", loadRanking);
}


/* ============================================================
 * PERFIL Y HOJA DE VIDA (RF-10, RF-12)
 * ============================================================ */

const BADGE_COLORS = ["#f0997b", "#5dcaa5", "#85b7eb", "#ed93b1", "#facf8f", "#afa9ec"];
let currentCv = null;

async function loadProfile() {

    if (!hasSession()) return;

    await safely(async function () {

        const cv = await fetchData("/me/cv");
        currentCv = cv;

        const set = function (id, value) { document.getElementById(id).textContent = value; };

        set("profile-xp", cv.xp.toLocaleString("es-CO"));
        set("profile-badges-count", cv.insignias.length);
        set("profile-pubs", cv.publicaciones);
        set("profile-level", `Nivel ${cv.nivel}`);
        set("profile-stars", stars(cv.nivel));
        set("profile-xp-next", cv.nivel < 5 ? `${cv.xp} / ${cv.xpSiguiente} XP para el siguiente nivel` : "Nivel máximo");
        set("profile-academic", [cv.usuario.faculty, cv.usuario.program].filter(Boolean).join(" · "));

        document.getElementById("profile-semilleros").innerHTML = cv.semilleros.map(function (s) {
            return `<span class="rounded-full bg-[#eaf3de] px-3 py-1 text-xs font-medium text-[#3b6d11]">Semillero: ${esc(s.nombre)}</span>`;
        }).join("");

        const items = cv.logros.map(function (l) { return [l.tipo, l.descripcion]; })
            .concat(cv.participaciones.map(function (p) { return ["Participación", p.evento]; }));

        if (cv.aportes) items.push(["Aportes", `${cv.aportes} aportes a proyectos`]);

        document.getElementById("profile-cv-list").innerHTML = items.length
            ? items.map(function (item) {
                return `<li><span class="rounded-full bg-[#eeeeea] px-3 py-1 text-xs font-medium text-[#3a3a38]">${esc(item[0])}</span>
                    <p class="mt-2 text-sm text-[#6b6a66]">${esc(item[1])}</p></li>`;
            }).join("")
            : `<li class="text-sm text-[#6b6a66]">Tu hoja de vida se llenará con tus logros aprobados.</li>`;

        document.getElementById("profile-badges").innerHTML = cv.insignias.length
            ? cv.insignias.map(function (b, index) {
                return `<div title="${esc(b.descripcion)}">
                    <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-full text-xl" style="background:${BADGE_COLORS[index % BADGE_COLORS.length]}">★</div>
                    <p class="mt-2 text-xs text-[#6b6a66]">${esc(b.nombre)}</p></div>`;
            }).join("")
            : `<p class="col-span-3 text-sm text-[#6b6a66]">Aún no tienes insignias.</p>`;
    });
}

function bindProfile() {

    document.getElementById("edit-profile").addEventListener("click", function () {

        if (!hasSession()) {
            needLogin("Inicia sesión para editar tu perfil");
            return;
        }

        const user = JSON.parse(localStorage.getItem("user") || "{}");

        openForm({
            title: "Editar perfil",
            values: {
                nombre: user.name, telefono: user.telefono, biografia: user.biografia,
                facultad: user.faculty, programa: user.program
            },
            fields: [
                { key: "nombre", label: "Nombre completo" },
                { key: "telefono", label: "Teléfono de contacto", required: false },
                { key: "facultad", label: "Facultad", type: "select", options: function () { return [""].concat(FACULTADES); }, required: false },
                { key: "programa", label: "Programa", type: "select", options: function () { return [""].concat(PROGRAMAS); }, required: false },
                { key: "biografia", label: "Biografía", type: "textarea", required: false }
            ],
            onSubmit: async function (data) {
                const result = await persist("PUT", "/auth/me", data);
                if (!result.ok) return false;

                localStorage.setItem("user", JSON.stringify(result.data));
                fillProfile();
                setText("[data-user-name]", result.data.name);
                loadProfile();
                doneMessage("Perfil actualizado", result);
            }
        });
    });

    document.getElementById("download-cv").addEventListener("click", function () {

        if (!currentCv) {
            needLogin("Inicia sesión para descargar tu hoja de vida");
            return;
        }

        const cv = currentCv;
        const list = function (items, empty) {
            return items.length ? `<ul>${items.map(function (i) { return `<li>${esc(i)}</li>`; }).join("")}</ul>` : `<p>${empty}</p>`;
        };

        const html = `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Hoja de vida investigativa</title>
            <style>body{font-family:Arial,sans-serif;max-width:720px;margin:40px auto;color:#232321}h1{margin-bottom:0}h2{margin-top:28px;border-bottom:1px solid #ccc;padding-bottom:4px}</style></head><body>
            <h1>${esc(cv.usuario.name)}</h1>
            <p>${esc(cv.usuario.email)} · ${esc(cv.usuario.role)}<br>${esc([cv.usuario.faculty, cv.usuario.program].filter(Boolean).join(" · "))}</p>
            <p><strong>Nivel ${cv.nivel} de 5</strong> · ${cv.xp} XP · ${cv.publicaciones} publicaciones · ${cv.aportes} aportes a proyectos</p>
            <h2>Semilleros</h2>${list(cv.semilleros.map(function (s) { return s.nombre; }), "Sin semilleros.")}
            <h2>Logros aprobados</h2>${list(cv.logros.map(function (l) { return `${l.tipo}: ${l.descripcion} (${l.fecha})`; }), "Sin logros aprobados.")}
            <h2>Participación en eventos</h2>${list(cv.participaciones.map(function (p) { return `${p.evento} (${p.fecha || ""})`; }), "Sin participaciones.")}
            <h2>Insignias</h2>${list(cv.insignias.map(function (b) { return b.nombre; }), "Sin insignias.")}
            <p style="margin-top:32px;font-size:12px;color:#777">Generado por RIUL el ${new Date().toLocaleDateString("es-CO")}</p></body></html>`;

        const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
        const link = document.createElement("a");

        link.href = url;
        link.download = "hoja-de-vida-riul.html";
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    });
}


/* ============================================================
 * NAVEGACIÓN: cada pantalla carga sus datos al abrirse
 * ============================================================ */

const loadedOnce = {};

function onStudentScreen(name) {

    const loaders = {
        "dashboard": loadImpact,
        "semilleros": loadSemilleros,
        "proyectos": loadProyectos,
        "publicaciones": loadPublicaciones,
        "eventos": loadEventos,
        "convocatorias": loadConvocatorias,
        "logros": loadLogros,
        "ranking": loadRanking,
        "profile": loadProfile
    };

    if (loaders[name]) loaders[name]();
}

const previousShowScreen = showScreen;

showScreen = function (name) {
    previousShowScreen(name);
    onStudentScreen(name);
};

document.addEventListener("DOMContentLoaded", function () {

    bindSemilleros();
    bindProyectos();
    bindPublicaciones();
    bindEventos();
    bindConvocatorias();
    bindLogros();
    bindRanking();
    bindProfile();
    loadCatalog();
});
