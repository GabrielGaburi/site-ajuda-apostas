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


const senha = document.getElementById("senha");
const confirmar = document.getElementById("confirmarSenha");


/* =========================
   VALIDAÇÃO DA SENHA
========================= */

if (senha) {

    senha.addEventListener("keyup", function () {

        const texto = this.value;
        const forca = document.getElementById("forcaSenha");

        if (!forca) {
            return;
        }

        if (texto.length === 0) {
            forca.innerHTML = "";
            return;
        }

        if (texto.length > 16) {

            forca.innerHTML =
                "<span class='text-danger'>" +
                "A senha deve ter no máximo 16 caracteres." +
                "</span>";

            return;
        }

        const faltando = [];

        // Tamanho mínimo
        if (texto.length < 8) {
            faltando.push("8 caracteres");
        }

        // Letra maiúscula
        if (!/[A-Z]/.test(texto)) {
            faltando.push("uma letra maiúscula");
        }

        // Número
        if (!/[0-9]/.test(texto)) {
            faltando.push("um número");
        }

        // Caractere especial
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(texto)) {
            faltando.push("um caractere especial");
        }


        // Senha válida
        if (faltando.length === 0) {

            forca.innerHTML =
                "<span class='text-success'>" +
                "✓ Senha válida." +
                "</span>";

            return;
        }


        // Monta mensagem
        let mensagem = "Precisa de ";

        if (faltando.length === 1) {

            mensagem += faltando[0] + ".";

        } else if (faltando.length === 2) {

            mensagem +=
                faltando[0] +
                " e " +
                faltando[1] +
                ".";

        } else {

            mensagem +=
                faltando.slice(0, -1).join(", ") +
                " e " +
                faltando[faltando.length - 1] +
                ".";
        }


        forca.innerHTML =
            "<span class='text-danger'>" +
            mensagem +
            "</span>";

    });
}


/* =========================
   CONFIRMAÇÃO DA SENHA
========================= */

if (confirmar && senha) {

    confirmar.addEventListener("keyup", function () {

        const mensagem =
            document.getElementById("erroConfirmarSenha");

        if (!mensagem) {
            return;
        }

        if (this.value.length === 0) {

            this.classList.remove("is-valid", "is-invalid");
            mensagem.innerHTML = "";

            return;
        }


        if (this.value === senha.value) {

            this.classList.remove("is-invalid");
            this.classList.add("is-valid");

            mensagem.innerHTML =
                "<span class='text-success'>" +
                "✓ As senhas coincidem." +
                "</span>";

        } else {

            this.classList.remove("is-valid");
            this.classList.add("is-invalid");

            mensagem.innerHTML =
                "<span class='text-danger'>" +
                "As senhas não coincidem." +
                "</span>";
        }

    });
}