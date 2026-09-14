document.addEventListener("DOMContentLoaded", function () {

    const toggle = document.getElementById("chatbot-toggle");
    const close = document.getElementById("chatbot-close");
    const windowChat = document.getElementById("chatbot-window");

    const input = document.getElementById("chatbot-input");
    const send = document.getElementById("chatbot-send");
    const messages = document.getElementById("chatbot-messages");

    const quickReplies = document.querySelectorAll(".chatbot-quick-reply");

    let atendimentoId = null;
    let ultimaMensagemId = 0;
    let pollingMensagens = null;


    // ========================================
    // ABRIR CHAT
    // ========================================

    toggle.addEventListener("click", function () {

        windowChat.style.display = "flex";
        toggle.style.display = "none";

        input.focus();
    });


    // ========================================
    // FECHAR CHAT
    // ========================================

    close.addEventListener("click", function () {

        windowChat.style.display = "none";
        toggle.style.display = "flex";
    });


    // ========================================
    // ADICIONAR MENSAGEM NA TELA
    // ========================================

    function adicionarMensagem(texto, tipo) {

        const mensagem = document.createElement("div");

        mensagem.classList.add("chatbot-message");

        if (tipo === "usuario") {

            mensagem.classList.add("chatbot-user-message");

        } else {

            mensagem.classList.add("chatbot-bot-message");
        }

        mensagem.textContent = texto;

        messages.appendChild(mensagem);

        messages.scrollTop = messages.scrollHeight;
    }


    // ========================================
    // VERIFICAR MENSAGENS DO PROFISSIONAL
    // ========================================

    function verificarMensagensProfissional() {
        if (!atendimentoId) {
            return;
        }

        fetch("/mensagens/" + atendimentoId)
            .then(function (resposta) {

                if (resposta.status === 401 || resposta.status === 403) {

                    console.log(
                        "Sessão sem acesso ao atendimento. Parando polling."
                    );

                    if (pollingMensagens) {
                        clearInterval(pollingMensagens);
                        pollingMensagens = null;
                    }

                    atendimentoId = null;
                    ultimaMensagemId = 0;

                    return null;
                }

                if (!resposta.ok) {
                    return null;
                }

                return resposta.json();
            })
            .then(function (dados) {

                if (!dados || !Array.isArray(dados)) {
                    return;
                }

                dados.forEach(function (mensagem) {

                    if (mensagem.id <= ultimaMensagemId) {
                        return;
                    }

                    ultimaMensagemId = mensagem.id;

                    if (mensagem.sender === "human") {
                        adicionarMensagem(
                            mensagem.text,
                            "profissional"
                        );
                    }
                });
            })
            .catch(function (erro) {

                console.error(
                    "Erro ao verificar mensagens do profissional:",
                    erro
                );
            });
    }


    // ========================================
    // INICIAR VERIFICAÇÃO AUTOMÁTICA
    // ========================================

    function iniciarPolling() {

        if (pollingMensagens) {

            clearInterval(pollingMensagens);
        }

        pollingMensagens = setInterval(
            verificarMensagensProfissional,
            2000
        );
    }


    // ========================================
    // ENVIAR MENSAGEM
    // ========================================

    function enviarMensagem() {

        console.log("1 - função enviarMensagem iniciou");

        const texto = input.value.trim();

        if (texto === "") {

            console.log("2 - mensagem vazia");

            return;
        }

        console.log("2 - mensagem:", texto);

        adicionarMensagem(texto, "usuario");

        input.value = "";
        input.focus();

        console.log("3 - preparando fetch");

        fetch("/chatbot", {

            method: "POST",

            headers: {

                "Content-Type": "application/json",

                "X-CSRFToken": document.querySelector(
                    'meta[name="csrf-token"]'
                ).getAttribute("content")
            },

            body: JSON.stringify({
                mensagem: texto
            })
        })

        .then(function (resposta) {

            console.log(
                "4 - resposta recebida:",
                resposta.status
            );

            return resposta.json();
        })

        .then(function (dados) {

            console.log("5 - dados:", dados);

            if (dados.erro) {

                adicionarMensagem(
                    dados.erro,
                    "bot"
                );

                return;
            }

            /*
             * Guarda o ID do atendimento.
             */

            if (dados.atendimento_id) {

                atendimentoId = dados.atendimento_id;

                /*
                 * Verifica imediatamente se já existe
                 * alguma mensagem do profissional.
                 */

                ultimaMensagemId = 0;

                verificarMensagensProfissional();

                /*
                 * Depois continua verificando
                 * automaticamente a cada 2 segundos.
                 */

                iniciarPolling();
            }

            /*
             * Mostra a resposta do bot.
             */

            if (dados.resposta) {

                adicionarMensagem(
                    dados.resposta,
                    "bot"
                );
            }

        })

        .catch(function (erro) {

            console.error(
                "6 - ERRO:",
                erro
            );

            adicionarMensagem(
                "Desculpe, não consegui responder agora. Tente novamente em alguns instantes.",
                "bot"
            );
        });
    }


    // ========================================
    // BOTÃO ENVIAR
    // ========================================

    send.addEventListener("click", function () {

        enviarMensagem();

    });


    // ========================================
    // ENTER PARA ENVIAR
    // ========================================

    input.addEventListener("keydown", function (event) {

        if (event.key === "Enter") {

            event.preventDefault();

            enviarMensagem();
        }

    });


    // ========================================
    // RESPOSTAS RÁPIDAS
    // ========================================

    quickReplies.forEach(function (botao) {

        botao.addEventListener("click", function () {

            const texto = botao.textContent.trim();

            input.value = texto;

            enviarMensagem();

        });

    });

});