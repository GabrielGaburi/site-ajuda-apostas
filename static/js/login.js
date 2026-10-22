// O botão de mostrar/ocultar senha é tratado pelo mostrar_senha.js (carregado no base.html)

document.addEventListener("DOMContentLoaded", function () {

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
