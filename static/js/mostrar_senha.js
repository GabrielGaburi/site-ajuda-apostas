// Botões de mostrar/ocultar senha, usados em todas as páginas.
// Uso: <button type="button" data-mostrar-senha="idDoCampo" aria-label="Mostrar senha"><i class="bi bi-eye"></i></button>
document.addEventListener("click", function (evento) {

    const botao = evento.target.closest("[data-mostrar-senha]");

    if (!botao) {
        return;
    }

    const campo = document.getElementById(botao.dataset.mostrarSenha);
    const icone = botao.querySelector("i");

    if (!campo) {
        return;
    }

    const mostrar = campo.type === "password";

    campo.type = mostrar ? "text" : "password";

    if (icone) {
        icone.classList.toggle("bi-eye", !mostrar);
        icone.classList.toggle("bi-eye-slash", mostrar);
    }

    botao.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
});
