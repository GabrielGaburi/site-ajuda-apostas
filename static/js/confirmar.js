// Pede confirmação antes de enviar formulários ou clicar em botões com data-confirmar.
// Substitui os onsubmit/onclick inline, que a Content-Security-Policy bloqueia.
document.addEventListener("submit", function (evento) {

    const mensagem = evento.target.dataset && evento.target.dataset.confirmar;

    if (mensagem && !window.confirm(mensagem)) {
        evento.preventDefault();
    }
});

document.addEventListener("click", function (evento) {

    const botao = evento.target.closest("button[data-confirmar], a[data-confirmar]");

    if (botao && !window.confirm(botao.dataset.confirmar)) {
        evento.preventDefault();
    }
});
