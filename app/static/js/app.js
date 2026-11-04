const screenTitles = {
    dashboard: "Inicio",
    semilleros: "Semillero DataLab",
    proyectos: "Proyectos",
    publicaciones: "Publicaciones",
    eventos: "Eventos",
    convocatorias: "Convocatorias",
    logros: "Logros",
    ranking: "Ranking",
    profile: "Mi perfil"
};


/*
 * ============================================================
 * MENSAJES
 * ============================================================
 */

function showMessage(
    message,
    type = "success"
) {

    const element =
        document.getElementById(
            "message"
        );


    element.textContent =
        message;


    element.classList.remove(
        "hidden",
        "bg-green-100",
        "text-green-800",
        "bg-red-100",
        "text-red-800"
    );


    if (type === "success") {

        element.classList.add(
            "bg-green-100",
            "text-green-800"
        );

    } else {

        element.classList.add(
            "bg-red-100",
            "text-red-800"
        );
    }


    setTimeout(
        function () {

            element.classList.add(
                "hidden"
            );

        },
        3000
    );
}


function initialsFromName(name) {

    const parts = String(name || "PR")
        .trim()
        .split(" ")
        .filter(Boolean);

    if (parts.length === 0) {
        return "PR";
    }

    if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
    }

    return (parts[0][0] + parts[1][0]).toUpperCase();
}


function fillProfile() {

    const user = JSON.parse(
        localStorage.getItem("user") || "{}"
    );

    const name = user.name || "Visitante RIUL";
    const email = user.email || "visitante@unilibre.edu.co";
    const initials = initialsFromName(name);

    const dashboardUser = document.getElementById("dashboard-username");
    const profileName = document.getElementById("profile-name");
    const profileEmail = document.getElementById("profile-email");
    const profileAvatar = document.getElementById("profile-avatar");
    const navbarAvatar = document.getElementById("navbar-avatar");

    if (dashboardUser) {
        dashboardUser.textContent = name;
    }

    if (profileName) {
        profileName.textContent = name;
    }

    if (profileEmail) {
        profileEmail.textContent = email;
    }

    if (profileAvatar) {
        profileAvatar.textContent = initials;
    }

    if (navbarAvatar) {
        navbarAvatar.textContent = initials;
    }
}


/*
 * ============================================================
 * MOSTRAR APLICACIÓN
 * ============================================================
 */

function showApplication() {

    document
        .getElementById("auth-section")
        .classList.add("hidden");

    document
        .getElementById("app-navbar")
        .classList.remove("hidden");

    document
        .getElementById("app-main")
        .classList.remove("hidden");

    document
        .getElementById("app-shell")
        .classList.remove("hidden");

    fillProfile();

    if (typeof applyRole === "function") {
        applyRole();
    }

    showScreen(
        typeof defaultScreen === "function"
            ? defaultScreen()
            : "dashboard"
    );
}


/*
 * ============================================================
 * MOSTRAR LOGIN
 * ============================================================
 */

function showLogin() {

    document
        .getElementById("auth-section")
        .classList.remove("hidden");

    document
        .getElementById("app-navbar")
        .classList.add("hidden");

    document
        .getElementById("app-main")
        .classList.add("hidden");

    document
        .getElementById("app-shell")
        .classList.add("hidden");
}


function showRecover(show) {

    document
        .getElementById("login-panel")
        .classList.toggle("hidden", show);

    document
        .getElementById("recover-panel")
        .classList.toggle("hidden", !show);
}


function setAuthToggle(mode) {

    const loginButton = document.getElementById("toggle-login");
    const registerButton = document.getElementById("toggle-register");

    const active = ["bg-[#3a3a38]", "text-white"];
    const inactive = ["bg-[#eeeeea]", "text-[#3a3a38]"];

    [loginButton, registerButton].forEach(function (button) {
        button.classList.remove(...active, ...inactive);
    });

    if (mode === "register") {
        loginButton.classList.add(...inactive);
        registerButton.classList.add(...active);
        document.getElementById("register-name").focus();
        return;
    }

    loginButton.classList.add(...active);
    registerButton.classList.add(...inactive);
}


function showScreen(screenName) {

    document
        .querySelectorAll(".app-screen")
        .forEach(function (screen) {
            screen.classList.add("hidden");
        });

    const target = document.getElementById(`${screenName}-screen`);

    if (target) {
        target.classList.remove("hidden");
    }

    const title = document.getElementById("navbar-title");

    if (title) {
        title.textContent = screenTitles[screenName] || "RIUL";
    }

    document
        .querySelectorAll("[data-screen]")
        .forEach(function (button) {
            const active = button.dataset.screen === screenName;

            button.classList.toggle("bg-[#3a3a38]", active);
            button.classList.toggle("text-white", active);
            button.classList.toggle("bg-slate-200", !active);
            button.classList.toggle("text-slate-700", !active);
        });
}


/*
 * ============================================================
 * REGISTRO
 * ============================================================
 */

async function register() {

    const value = function (id) {
        return document.getElementById(id).value.trim();
    };

    const payload = {
        name: value("register-name"),
        faculty: value("register-faculty"),
        program: value("register-program"),
        institutional: value("register-institutional") === "1",
        email: value("register-email"),
        password: document.getElementById("register-password").value
    };

    if (!payload.name || !payload.email || !payload.password) {
        showMessage("Completa nombre, correo y contraseña", "error");
        return;
    }

    try {

        const response = await api.post("/auth/register", payload);

        showMessage(
            response.data.message ||
            "Solicitud enviada. Pendiente de aprobación del admin."
        );

        ["register-name", "register-email", "register-password"].forEach(function (id) {
            document.getElementById(id).value = "";
        });

    } catch (error) {

        showMessage(
            error.response?.data?.message ||
            "No se pudo conectar con el servidor",
            "error"
        );
    }
}


/*
 * ============================================================
 * LOGIN
 * ============================================================
 */

async function login() {

    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    if (!email || !password) {
        showMessage("Ingresa correo y contraseña", "error");
        return;
    }

    try {

        const response = await api.post(
            "/auth/login",
            { email, password }
        );

        const data = response.data.data;

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));

        showApplication();

    } catch (error) {

        showMessage(
            error.response?.data?.message ||
            "No se pudo conectar con el servidor",
            "error"
        );
    }
}


function enterAsGuest() {

    localStorage.setItem(
        "user",
        JSON.stringify({
            name: "Visitante",
            email: "visitante@unilibre.edu.co"
        })
    );

    showApplication();
}


function logout() {

    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    location.reload();
}


async function sendRecoveryCode() {

    const email = document.getElementById("recover-email").value.trim();

    if (!email) {
        showMessage("Ingresa tu correo", "error");
        return;
    }

    try {

        const response = await api.post("/auth/recover", { email });
        const code = response.data.data && response.data.data.code;

        if (code) {
            // Solo en desarrollo (RESET_CODE_IN_RESPONSE=1): no hay servidor de correo
            document.getElementById("recover-code").value = code;
        }

        showMessage(
            code
                ? `Modo desarrollo: tu código es ${code}`
                : response.data.message
        );

    } catch (error) {

        showMessage(
            error.response?.data?.message || "No se pudo conectar con el servidor",
            "error"
        );
    }
}


async function recoverPassword() {

    const email = document.getElementById("recover-email").value.trim();
    const code = document.getElementById("recover-code").value.trim();
    const password = document.getElementById("recover-password").value;
    const confirm = document.getElementById("recover-password-confirm").value;

    if (password !== confirm) {
        showMessage("Las contraseñas no coinciden", "error");
        return;
    }

    try {

        const response = await api.post(
            "/auth/reset",
            { email, code, password }
        );

        showMessage(response.data.message);
        showRecover(false);

    } catch (error) {

        showMessage(
            error.response?.data?.message || "No se pudo conectar con el servidor",
            "error"
        );
    }
}


/*
 * ============================================================
 * SESIÓN INICIAL
 * ============================================================
 *
 * - Con token: se valida contra /auth/me (rol y datos vigentes).
 * - Sin token: solo se permite el modo visitante.
 */

async function startSession(token, storedUser) {

    let user = {};

    try {
        user = JSON.parse(storedUser || "{}");
    } catch (error) {
        user = {};
    }

    if (token) {

        try {

            const response = await api.get("/auth/me");

            localStorage.setItem("user", JSON.stringify(response.data.data));
            showApplication();

        } catch (error) {

            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            showLogin();
        }

        return;
    }

    if (storedUser && !user.role) {
        showApplication();
        return;
    }

    localStorage.removeItem("user");
    showLogin();
}


/*
 * ============================================================
 * INICIALIZACIÓN
 * ============================================================
 */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const token = localStorage.getItem("access_token");
        const storedUser = localStorage.getItem("user");

        document
            .getElementById("register-button")
            .addEventListener("click", register);

        document
            .getElementById("login-button")
            .addEventListener("click", login);

        document
            .getElementById("guest-button")
            .addEventListener("click", enterAsGuest);

        document
            .getElementById("logout-button")
            .addEventListener("click", logout);

        document
            .getElementById("forgot-password-link")
            .addEventListener("click", function () {
                showRecover(true);
            });

        document
            .getElementById("back-to-login")
            .addEventListener("click", function () {
                showRecover(false);
            });

        document
            .getElementById("recover-button")
            .addEventListener("click", recoverPassword);

        document
            .getElementById("recover-send-button")
            .addEventListener("click", sendRecoveryCode);

        document
            .getElementById("toggle-login")
            .addEventListener("click", function () {
                setAuthToggle("login");
            });

        document
            .getElementById("toggle-register")
            .addEventListener("click", function () {
                setAuthToggle("register");
            });

        document
            .querySelectorAll("[data-screen]")
            .forEach(function (button) {
                button.addEventListener("click", function () {
                    showScreen(button.dataset.screen);
                });
            });

        document
            .querySelectorAll(".semillero-tab")
            .forEach(function (button) {
                button.addEventListener("click", function () {
                    document.querySelectorAll(".semillero-tab").forEach(function (tab) {
                        tab.classList.remove("bg-[#3a3a38]", "text-white");
                        tab.classList.add("bg-[#eeeeea]", "text-[#3a3a38]");
                    });

                    button.classList.remove("bg-[#eeeeea]", "text-[#3a3a38]");
                    button.classList.add("bg-[#3a3a38]", "text-white");
                });
            });

        startSession(token, storedUser);
    }
);
