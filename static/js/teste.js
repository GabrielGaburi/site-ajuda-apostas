let perguntaAtual = 1;

const totalPerguntas = document.querySelectorAll(".pergunta").length;

const formTeste = document.getElementById("formTeste");
const mensagemErro = document.getElementById("mensagemErro");


function mostrarErro(mostrar) {

    mensagemErro.classList.toggle("d-none", !mostrar);

}


function respondida(numero) {

    return document
        .getElementById("pergunta" + numero)
        .querySelector('input[type="radio"]:checked') !== null;

}


function mostrarPergunta(numero) {

    mostrarErro(false);


    // Esconde todas
    for (let i = 1; i <= totalPerguntas; i++) {

        document
            .getElementById("pergunta" + i)
            .classList.add("d-none");

    }


    // Mostra a atual
    const pergunta = document.getElementById("pergunta" + numero);

    pergunta.classList.remove("d-none");


    // Leva o foco para a opção marcada (ou a primeira) para leitores de tela e teclado
    const foco =
        pergunta.querySelector('input[type="radio"]:checked') ||
        pergunta.querySelector('input[type="radio"]');

    foco.focus();


    // Atualiza contador
    document.getElementById("contador").textContent =
        "Pergunta " + numero + " de " + totalPerguntas;


    // Atualiza barra
    const porcentagem =
        (numero / totalPerguntas) * 100;

    const barra = document.getElementById("barraProgresso");

    barra.style.width = porcentagem + "%";
    barra.setAttribute("aria-valuenow", Math.round(porcentagem));


    // Botão anterior
    document.getElementById("btnAnterior").disabled =
        numero === 1;


    // Botões finais
    if (numero === totalPerguntas) {

        document
            .getElementById("btnProxima")
            .classList.add("d-none");

        document
            .getElementById("btnFinalizar")
            .classList.remove("d-none");

    } else {

        document
            .getElementById("btnProxima")
            .classList.remove("d-none");

        document
            .getElementById("btnFinalizar")
            .classList.add("d-none");

    }

}


function proximaPergunta() {

    if (!respondida(perguntaAtual)) {

        mostrarErro(true);

        return;

    }


    if (perguntaAtual < totalPerguntas) {

        perguntaAtual++;

        mostrarPergunta(perguntaAtual);

    }

}


function anteriorPergunta() {

    if (perguntaAtual > 1) {

        perguntaAtual--;

        mostrarPergunta(perguntaAtual);

    }

}


document.getElementById("btnAnterior").addEventListener("click", anteriorPergunta);
document.getElementById("btnProxima").addEventListener("click", proximaPergunta);


// Esconde o erro assim que o usuário responde
formTeste.addEventListener("change", function () {

    mostrarErro(false);

});


// Enter avança em vez de enviar o formulário com perguntas ocultas
formTeste.addEventListener("keydown", function (evento) {

    if (evento.key === "Enter" && perguntaAtual < totalPerguntas) {

        evento.preventDefault();

        proximaPergunta();

    }

});


// Só envia se todas as perguntas foram respondidas
formTeste.addEventListener("submit", function (evento) {

    for (let i = 1; i <= totalPerguntas; i++) {

        if (!respondida(i)) {

            evento.preventDefault();

            perguntaAtual = i;

            mostrarPergunta(i);

            mostrarErro(true);

            return;

        }

    }

});
