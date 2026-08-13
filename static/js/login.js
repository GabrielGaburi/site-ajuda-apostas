window.toggleSenha = function (campoId, iconeId) {

    const campo = document.getElementById(campoId);
    const icone = document.getElementById(iconeId);

    if (!campo || !icone) {
        return;
    }

    if (campo.type === "password") {

        campo.type = "text";

        icone.classList.remove("bi-eye");
        icone.classList.add("bi-eye-slash");

    } else {

        campo.type = "password";

        icone.classList.remove("bi-eye-slash");
        icone.classList.add("bi-eye");
    }
};
