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

document.addEventListener("DOMContentLoaded", function () {

    // Botão de mostrar/ocultar senha
    const botaoMostrarSenha = document.getElementById("botaoMostrarSenha");
    const campoSenha = document.getElementById("senha");

    if (botaoMostrarSenha && campoSenha) {

        botaoMostrarSenha.addEventListener("click", function () {

            toggleSenha("senha", "iconeSenha");

            const visivel = campoSenha.type === "text";

            botaoMostrarSenha.setAttribute(
                "aria-label",
                visivel ? "Ocultar senha" : "Mostrar senha"
            );
        });
    }

    // Evita envio duplo do formulário
    const formLogin = document.getElementById("formLogin");
    const botaoEntrar = document.getElementById("botaoEntrar");

    if (formLogin && botaoEntrar) {

        formLogin.addEventListener("submit", function () {

            botaoEntrar.disabled = true;
            botaoEntrar.textContent = "Entrando...";
        });

        // Reativa o botão se a página voltar pelo botão "voltar" do navegador
        window.addEventListener("pageshow", function () {

            botaoEntrar.disabled = false;
            botaoEntrar.textContent = "Entrar";
        });
    }
});
