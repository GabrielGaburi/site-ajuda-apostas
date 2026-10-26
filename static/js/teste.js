let perguntaAtual = 1;

const totalPerguntas = 4;


function mostrarPergunta(numero) {

    // Esconde todas
    for (let i = 1; i <= totalPerguntas; i++) {

        document
            .getElementById("pergunta" + i)
            .classList.add("d-none");

    }


    // Mostra a atual
    document
        .getElementById("pergunta" + numero)
        .classList.remove("d-none");


    // Atualiza contador
    document.getElementById("contador").textContent =
        "Pergunta " + numero + " de " + totalPerguntas;


    // Atualiza barra
    const porcentagem =
        (numero / totalPerguntas) * 100;

    document.getElementById("barraProgresso").style.width =
        porcentagem + "%";


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

    const pergunta =
        document.getElementById(
            "pergunta" + perguntaAtual
        );


    const resposta =
        pergunta.querySelector(
            'input[type="radio"]:checked'
        );


    if (!resposta) {

        alert("Selecione uma resposta antes de continuar.");

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
