window.toggleSenha = function (campoId, iconeId) {
    const campo = document.getElementById(campoId);
    const icone = document.getElementById(iconeId);

    if (!campo || !icone) {
        return;
    }

    if (campo.type === "password") {
        campo.type = "text";
        icone.textContent = "🙈";
    } else {
        campo.type = "password";
        icone.textContent = "👁️";
    }
};
