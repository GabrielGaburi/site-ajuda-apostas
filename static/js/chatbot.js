document.addEventListener("DOMContentLoaded", function () {

    const toggle = document.getElementById("chatbot-toggle");
    const close = document.getElementById("chatbot-close");
    const windowChat = document.getElementById("chatbot-window");

    const input = document.getElementById("chatbot-input");
    const send = document.getElementById("chatbot-send");
    const messages = document.getElementById("chatbot-messages");

    const headerAvatar = document.getElementById("chatbot-header-avatar");
    const headerTitle = document.getElementById("chatbot-header-title");
    const headerStatus = document.getElementById("chatbot-header-status");

    if (!toggle || !close || !windowChat || !input || !send || !messages) {
        return;
    }

    const quickReplies = document.querySelectorAll(".chatbot-quick-reply");

    const botoesContexto = document.querySelectorAll(".chatbot-context-button");

    const botaoProfissional = document.querySelector(".chatbot-profissional-button");
    const chatbotContainer = document.getElementById("chatbot-container");
    const usuarioAutenticado = chatbotContainer && chatbotContainer.dataset.chatbotAuthenticated === "true";
    const historicoLocalKey = "chatbotHistorico";
    const botoesOcultosKey = "chatbotBotoesOcultos";
    const janelaAbertaKey = "chatbotJanelaAberta";

    const sessaoChatKey = "chatbotSessaoAtiva";

    const navigationEntry = performance.getEntriesByType("navigation")[0];

    if (navigationEntry && navigationEntry.type === "reload") {
        sessionStorage.removeItem(sessaoChatKey);
        sessionStorage.removeItem("chatbotHistoricoSessao");
        sessionStorage.removeItem("atendimentoId");
    }

    let atendimentoId = sessionStorage.getItem("atendimentoId");
    let pollingMensagens = null;
    let mensagensExibidas = new Set();
    let profissionalAtendendo = false;
    let atendimentoInicializado = false;
    let historicoCarregando = false;
    let historicoCarregado = false;
    let iaRespondendo = false;


    // ========================================
    // ABRIR CHAT
    // ========================================

    toggle.addEventListener("click", function () {

        windowChat.style.display = "flex";
        localStorage.setItem(janelaAbertaKey, "true");

        windowChat.classList.remove("chatbot-animando");

        void windowChat.offsetWidth;

        windowChat.classList.add("chatbot-animando");

        toggle.style.display = "none";

        const mensagensRenderizadas = messages.querySelectorAll(
            ".chatbot-user-message, .chatbot-bot-message"
        ).length;

        if (mensagensRenderizadas <= 1 && !historicoCarregando) {
            historicoCarregado = false;
            carregarHistoricoChat();
        }

        rolarChatParaBaixo();

        input.focus();
    });


    // ========================================
    // FECHAR CHAT
    // ========================================

    close.addEventListener("click", function () {

        windowChat.style.display = "none";
        toggle.style.display = "flex";
        localStorage.setItem(janelaAbertaKey, "false");
    });


    // ========================================
    // ADICIONAR MENSAGEM NA TELA
    // ========================================

    // MOSTRAR SOMENTE O BOTÃO DE PROFISSIONAL
    function mostrarBotaoProfissional() {

        botoesContexto.forEach(function (botao) {
            botao.style.display = "none";
        });

        if (botaoProfissional) {
            botaoProfissional.style.display = "block";
        }

        localStorage.setItem(botoesOcultosKey, "true");
    }

    function esconderTodosOsBotoes() {

        quickReplies.forEach(function (botao) {
            botao.style.display = "none";
        });

    }

    function restaurarEstadoInterface() {

        if (localStorage.getItem(botoesOcultosKey) === "true") {
            mostrarBotaoProfissional();
        }

        if (localStorage.getItem(janelaAbertaKey) === "true") {
            windowChat.style.display = "flex";
            toggle.style.display = "none";
        }
    }

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

        if (!usuarioAutenticado && tipo !== "profissional") {
            const historico = JSON.parse(
                sessionStorage.getItem("chatbotHistoricoSessao") || "[]"
            );

            historico.push({
                mensagem: texto,
                remetente: tipo === "usuario" ? "usuario" : "bot"
            });

            sessionStorage.setItem(
                "chatbotHistoricoSessao",
                JSON.stringify(historico)
            );
        }

        messages.scrollTop = messages.scrollHeight;
    }
    // ========================================
    // INDICADOR DE DIGITAÇÃO DA IA
    // ========================================

    function mostrarDigitando() {

        // Evita criar mais de um indicador
        if (document.getElementById("chatbot-typing")) {
            return;
        }

        const typing = document.createElement("div");

        typing.id = "chatbot-typing";
        typing.classList.add("chatbot-typing");

        typing.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;

        messages.appendChild(typing);

        messages.scrollTop = messages.scrollHeight;
    }


    function removerDigitando() {

        const typing = document.getElementById("chatbot-typing");

        if (typing) {
            typing.remove();
        }
    }

    function mostrarAtendimentoProfissional() {

        headerAvatar.src = "/static/img/imagens.png";
        headerAvatar.alt = "Profissional";

        headerTitle.textContent = "Atendimento profissional";
        headerStatus.textContent = "Profissional atendendo";
    }


    function mostrarApoioVirtual() {

        headerAvatar.src = "/static/img/caozinho.jpg";
        headerAvatar.alt = "Apoio Virtual";

        headerTitle.textContent = "Apoio Virtual";
        headerStatus.textContent = "Estou aqui para ouvir você";
    }

    function mostrarAguardandoProfissional() {

        headerAvatar.src = "/static/img/caozinho.jpg";
        headerAvatar.alt = "Apoio Virtual";

        headerTitle.textContent = "Atendimento profissional";
        headerStatus.textContent = "Aguardando profissional...";
    }

    function carregarHistoricoChat() {

        if (historicoCarregado || historicoCarregando) {
            return;
        }

        historicoCarregando = true;

        if (!usuarioAutenticado) {
            const historicoLocal = JSON.parse(
                sessionStorage.getItem("chatbotHistoricoSessao") || "[]"
            );

            if (historicoLocal.length > 0) {
                mostrarBotaoProfissional();
            }

            historicoLocal.forEach(function (mensagem) {
                adicionarMensagemSemPersistir(
                    mensagem.mensagem,
                    mensagem.remetente === "usuario" ? "usuario" : "bot"
                );
            });

            rolarChatParaBaixo();

            historicoCarregado = true;
            historicoCarregando = false;

            return;
        }

        fetch("/chatbot/historico")
            .then(function (resposta) {
                return resposta.json();
            })
            .then(function (dados) {

                if (!dados.mensagens) {
                    historicoCarregado = true;
                    historicoCarregando = false;
                    return;
                }

                if (dados.mensagens.length > 0) {
                    mostrarBotaoProfissional();
                }

                dados.mensagens.forEach(function (mensagem) {

                    if (mensagem.remetente === "usuario") {

                        adicionarMensagem(
                            mensagem.mensagem,
                            "usuario"
                        );

                    } else if (mensagem.remetente === "bot") {

                        adicionarMensagem(
                            mensagem.mensagem,
                            "bot"
                        );

                    }

                });

                rolarChatParaBaixo();

                historicoCarregado = true;
                historicoCarregando = false;

            })
            .catch(function (erro) {

                historicoCarregando = false;

                console.error(
                    "Erro ao carregar histórico:",
                    erro
                );

            });
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

                    if (pollingMensagens) {
                        clearInterval(pollingMensagens);
                        pollingMensagens = null;
                    }

                    atendimentoId = null;
                    mensagensExibidas.clear();
                    atendimentoInicializado = false;

                    return null;
                }

                if (!resposta.ok) {
                    return null;
                }

                return resposta.json();
            })

            .then(function (dados) {

                if (!dados) {
                    return;
                }

                // ========================================
                // VERIFICAR STATUS DO ATENDIMENTO
                // ========================================

                if (dados.status === "em_atendimento") {

                    profissionalAtendendo = true;

                    mostrarAtendimentoProfissional();

                    esconderTodosOsBotoes();

                } else if (dados.status === "aguardando") {

                    profissionalAtendendo = false;

                    mostrarAguardandoProfissional();

                } else if (dados.status === "ia") {

                    profissionalAtendendo = false;

                    mostrarApoioVirtual();
                }

                // ========================================
                // ATENDIMENTO ENCERRADO
                // ========================================

                if (dados.status === "finalizado") {

                    if (pollingMensagens) {
                        clearInterval(pollingMensagens);
                        pollingMensagens = null;
                    }

                    atendimentoId = null;
                    sessionStorage.removeItem("atendimentoId");
                    atendimentoInicializado = false;
                    profissionalAtendendo = false;

                    mostrarApoioVirtual();
                    
                    mostrarBotaoProfissional();

                    adicionarMensagem(
                        "Este atendimento foi encerrado pelo profissional. Se precisar de ajuda novamente, você pode continuar conversando com o Apoio Virtual.",
                        "bot"
                    );

                    return;
                }

                const mensagens = dados.mensagens;

                if (!Array.isArray(mensagens)) {
                    return;
                }

                // ========================================
                // PRIMEIRA CONSULTA
                // ========================================

                if (!atendimentoInicializado) {

                    mensagens.forEach(function (mensagem) {

                        if (!mensagem || !mensagem.id) {
                            return;
                        }

                        mensagensExibidas.add(mensagem.id);

                        if (mensagem.sender === "human") {

                            adicionarMensagem(
                                mensagem.text,
                                "profissional"
                            );

                        } else if (mensagem.sender === "user") {

                            adicionarMensagem(
                                mensagem.text,
                                "usuario"
                            );

                        } else {

                            adicionarMensagem(
                                mensagem.text,
                                "bot"
                            );
                        }

                    });

                    atendimentoInicializado = true;

                    console.log(
                        "Histórico do atendimento restaurado."
                    );

                    return;
                }
                // ========================================
                // NOVAS MENSAGENS
                // ========================================

                mensagens.forEach(function (mensagem) {

                    if (!mensagem || !mensagem.id) {
                        return;
                    }

                    if (mensagensExibidas.has(mensagem.id)) {
                        return;
                    }

                    mensagensExibidas.add(mensagem.id);

                    // Só mensagens do profissional
                    // são adicionadas pelo polling.
                    if (mensagem.sender === "human") {

                        adicionarMensagem(
                            mensagem.text,
                            "profissional"
                        );

                    } else if (mensagem.sender === "bot") {

                        removerDigitando();

                        adicionarMensagem(
                            mensagem.text,
                            "bot"
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

        if (iaRespondendo) {
            return;
        }

        const texto = input.value.trim();

        if (texto === "") {

            console.log("2 - mensagem vazia");

            return;
        }

        iaRespondendo = true;

        console.log("2 - mensagem:", texto);

        adicionarMensagem(texto, "usuario");

        if (!profissionalAtendendo) {
            mostrarDigitando();
        }

        if (!profissionalAtendendo) {
            mostrarBotaoProfissional();
        }

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

            removerDigitando();

            iaRespondendo = false;

            if (dados.profissional_atendendo) {
                profissionalAtendendo = true;
            }


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

                const novoAtendimento =
                    atendimentoId !== dados.atendimento_id;

                atendimentoId = dados.atendimento_id;
                sessionStorage.setItem("atendimentoId", atendimentoId);

                /*
                * Se for um atendimento novo,
                * começamos o acompanhamento.
                */
                if (novoAtendimento) {

                    atendimentoInicializado = false;

                    mensagensExibidas.clear();

                    verificarMensagensProfissional();

                    iniciarPolling();
                }
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

            removerDigitando();

            iaRespondendo = false;

            adicionarMensagem(
                "Desculpe, não consegui responder agora. Tente novamente em alguns instantes.",
                "bot"
            );
        });
    }

    function adicionarMensagemSemPersistir(texto, tipo) {

        const mensagem = document.createElement("div");

        mensagem.classList.add("chatbot-message");
        mensagem.classList.add(
            tipo === "usuario"
                ? "chatbot-user-message"
                : "chatbot-bot-message"
        );
        mensagem.textContent = texto;

        messages.appendChild(mensagem);
        messages.scrollTop = messages.scrollHeight;
    }

    function rolarChatParaBaixo() {
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                messages.scrollTop = messages.scrollHeight;
            });
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

        if (botao.classList.contains("chatbot-context-button")) {
            mostrarBotaoProfissional();
        }

        input.value = texto;
        enviarMensagem();
    });

});

    carregarHistoricoChat();
    restaurarEstadoInterface();

    if (atendimentoId) {
        verificarMensagensProfissional();
        iniciarPolling();
    }

});