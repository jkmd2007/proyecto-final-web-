const api = axios.create({

    /*
     * Todas las solicitudes tendrán
     * automáticamente este prefijo.
     */

    baseURL: "/api",

    headers: {

        "Content-Type":
            "application/json"
    }
});


/*
 * ============================================================
 * REQUEST INTERCEPTOR
 * ============================================================
 *
 * Antes de enviar una solicitud:
 *
 * 1. Buscamos el JWT.
 * 2. Lo obtenemos desde localStorage.
 * 3. Lo agregamos al header Authorization.
 *
 * Resultado:
 *
 * Authorization: Bearer TOKEN
 */

api.interceptors.request.use(

    function (config) {

        const token =
            localStorage.getItem(
                "access_token"
            );


        if (token) {

            config.headers.Authorization =
                `Bearer ${token}`;
        }


        return config;
    },


    function (error) {

        return Promise.reject(
            error
        );
    }
);


/*
 * ============================================================
 * RESPONSE INTERCEPTOR
 * ============================================================
 *
 * Si Flask devuelve 401:
 *
 * significa que el token no es válido
 * o ya expiró.
 */

api.interceptors.response.use(

    function (response) {

        return response;
    },


    function (error) {

        if (
            error.response &&
            error.response.status === 401
        ) {

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "user"
            );


            window.location.reload();
        }


        return Promise.reject(
            error
        );
    }
);
