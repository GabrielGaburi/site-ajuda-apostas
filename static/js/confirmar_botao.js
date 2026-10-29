// Confirmação no próprio botão, como no chat: o primeiro clique troca o botão por
// "pergunta + Sim / Cancelar". Sem resposta em alguns segundos, volta ao botão normal.
// Uso: <form data-confirmar-botao="Pergunta?" data-confirmar-sim="Sim, apagar">
document.addEventListener("submit", function (evento) {

    const formulario = evento.target;
    const pergunta = formulario.dataset && formulario.dataset.confirmarBotao;

    if (!pergunta) {
        return;
    }

    // Segundo envio, disparado pelo botão "Sim": deixa passar
    if (formulario.dataset.confirmado === "1") {
        return;
    }

    evento.preventDefault();

    const botao = formulario.querySelector("button[type='submit']");

    if (!botao || formulario.querySelector(".confirmar-botao")) {
        return;
    }

    const aviso = document.createElement("div");
    aviso.className = "confirmar-botao d-flex flex-wrap align-items-center gap-2";
    aviso.setAttribute("role", "alert");

    const texto = document.createElement("span");
    texto.className = "small me-auto";
    texto.textContent = pergunta;

    const botaoSim = document.createElement("button");
    botaoSim.type = "button";
    botaoSim.className = "btn btn-sm btn-danger";
    botaoSim.textContent = formulario.dataset.confirmarSim || "Sim";

    const botaoNao = document.createElement("button");
    botaoNao.type = "button";
    botaoNao.className = "btn btn-sm btn-outline-secondary";
    botaoNao.textContent = "Cancelar";

    aviso.append(texto, botaoSim, botaoNao);

    let timer = null;

    function cancelar() {
        clearTimeout(timer);
        aviso.remove();
        botao.hidden = false;
        botao.focus();
    }

    botaoSim.addEventListener("click", function () {
        clearTimeout(timer);
        botaoSim.disabled = true;
        botaoNao.disabled = true;
        formulario.dataset.confirmado = "1";
        formulario.requestSubmit();
    });

    botaoNao.addEventListener("click", cancelar);

    aviso.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            cancelar();
        }
    });

    botao.hidden = true;
    botao.after(aviso);

    // Foco no "Cancelar": Enter sem querer não confirma uma ação destrutiva
    botaoNao.focus();

    timer = setTimeout(cancelar, 8000);
});
