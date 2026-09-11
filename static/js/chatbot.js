document.addEventListener("DOMContentLoaded", function () {

    const toggle = document.getElementById("chatbot-toggle");
    const close = document.getElementById("chatbot-close");
    const windowChat = document.getElementById("chatbot-window");

    const input = document.getElementById("chatbot-input");
    const send = document.getElementById("chatbot-send");
    const messages = document.getElementById("chatbot-messages");

    const quickReplies = document.querySelectorAll(".chatbot-quick-reply");


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
    // ENVIAR MENSAGEM
    // ========================================

    function enviarMensagem() {

        const texto = input.value.trim();

        if (texto === "") {
            return;
        }

        // Mostra a mensagem do usuário
        adicionarMensagem(texto, "usuario");

        // Limpa o campo
        input.value = "";

        input.focus();


        // Resposta provisória
        setTimeout(function () {

            adicionarMensagem(
                "Recebi sua mensagem. Em breve vamos conectar o Apoio Virtual à inteligência artificial.",
                "bot"
            );

        }, 500);
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