// ------------ State ------------
        let sessaoSelecionada = null;
        let pollSessionsTimer = null;
        let pollMessagesTimer = null;
        let renderedIds = new Set(); // dedupe por ID para a sessão atual
        let ultCount = 0;            // ponteiro incremental
        const SESSIONS_POLL_MS = 5000;
        const MESSAGES_POLL_MS = 2000;

        // ------------ DOM refs ------------
        const elSessions = document.getElementById('sessions');
        const elMessages = document.getElementById('messages');
        const elTitle = document.getElementById('chatTitle');
        const elInput = document.getElementById('inputMsg');
        const elSend = document.getElementById('btnSend');
        const elEnd = document.getElementById('btnEnd');
        const elRefresh = document.getElementById('btnRefresh');
        const elToast = document.getElementById('toast');
        const elLastSync = document.getElementById('lastSync');
        const elDot = document.getElementById('onlineDot');

        // ------------ Utils ------------
        const nowHHMM = () => {
            const d = new Date();
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        const setOnline = (ok) => elDot.style.background = ok ? 'var(--ok)' : '#9ca3af';
        const toast = (msg) => { elToast.textContent = msg; elToast.classList.add('show'); setTimeout(() => elToast.classList.remove('show'), 1800); }
        const scrollBottom = () => elMessages.scrollTop = elMessages.scrollHeight;

        function messageRow({ sender, text, ts }) {
            const row = document.createElement('div');
            row.className = 'row ' + (sender === 'human' ? 'human' : sender === 'user' ? 'user' : 'bot');
            const bubble = document.createElement('div');
            bubble.className = 'msg';
            bubble.textContent = text;
            const meta = document.createElement('div');
            meta.className = 'meta';
            meta.textContent = ts ? ts : nowHHMM();
            bubble.appendChild(document.createElement('br'));
            bubble.appendChild(meta);
            row.appendChild(bubble);
            return row;
        }

        function clearMessagesUI() {
            renderedIds.clear();
            ultCount = 0;
            elMessages.innerHTML = '';
        }

        // ------------ Sessions ------------
        async function carregarSessoes() {
            try {
                const r = await fetch('/lista_sessoes');
                setOnline(r.ok);
                const lista = r.ok ? await r.json() : [];
                elSessions.innerHTML = '';
                if (!lista || lista.length === 0) {
                    elSessions.innerHTML = '<div class="empty">Nenhuma sessão aguardando.</div>';
                } else {
                    lista.forEach(id => {
                        const item = document.createElement('div');
                        item.className = 'item' + (id === sessaoSelecionada ? ' active' : '');
                        item.innerHTML = `<div><strong>${id}</strong></div><span class="badge">aguardando</span>`;
                        item.onclick = () => selecionarSessao(id);
                        elSessions.appendChild(item);
                    });
                }
                elLastSync.textContent = `atualizado às ${nowHHMM()}`;
            } catch (e) {
                setOnline(false);
                console.error(e);
                elLastSync.textContent = `falha ao sincronizar`;
            }
        }

        function startSessionsPolling() {
            if (pollSessionsTimer) clearInterval(pollSessionsTimer);
            pollSessionsTimer = setInterval(carregarSessoes, SESSIONS_POLL_MS);
        }

        // ------------ Messages ------------
        async function selecionarSessao(id) {

            try {

                // Primeiro assume o atendimento
                const csrfToken = document
                    .querySelector('meta[name="csrf-token"]')
                    .getAttribute('content');

                const resposta = await fetch(`/assumir_atendimento/${id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });

                const dados = await resposta.json();

                if (!resposta.ok) {
                    toast(dados.erro || 'Não foi possível assumir o atendimento.');
                    await carregarSessoes();
                    return;
                }

                // Atendimento assumido com sucesso
                sessaoSelecionada = id;

                elTitle.textContent = `Atendendo sessão: ${id}`;

                elInput.disabled = false;
                elSend.disabled = false;
                elEnd.disabled = false;

                // Destaque visual na lista
                [...elSessions.querySelectorAll('.item')].forEach(n => {
                    n.classList.toggle(
                        'active',
                        n.textContent.includes(String(id))
                    );
                });

                // Limpa mensagens anteriores
                clearMessagesUI();

                // Carrega histórico
                await renderIncremental();

                // Começa atualização automática
                startMessagesPolling();

                // Atualiza lista
                await carregarSessoes();

                toast(`Atendimento ${id} assumido.`);

            } catch (e) {

                console.error('Erro ao assumir atendimento:', e);

                toast('Não foi possível assumir o atendimento.');
            }
        }

        function startMessagesPolling() {
            if (pollMessagesTimer) clearInterval(pollMessagesTimer);
            pollMessagesTimer = setInterval(renderIncremental, MESSAGES_POLL_MS);
        }

        async function renderIncremental() {

            if (!sessaoSelecionada) {
                return;
            }

            try {

                const r = await fetch(
                    `/mensagens/${sessaoSelecionada}`
                );

                setOnline(r.ok);

                if (!r.ok) {
                    return;
                }

                const dados = await r.json();

                // ========================================
                // ATENDIMENTO ENCERRADO
                // ========================================

                if (dados.status === "finalizado") {

                    console.log(
                        "Atendimento finalizado."
                    );

                    clearMessagesUI();

                    elMessages.appendChild(
                        messageRow({
                            sender: "bot",
                            text: "Este atendimento foi encerrado."
                        })
                    );

                    return;
                }

                // ========================================
                // MENSAGENS
                // ========================================

                const msgs = dados.mensagens;

                console.log("MENSAGENS RECEBIDAS:", msgs);
                console.log("IDS JÁ RENDERIZADOS:", [...renderedIds]);

                if (!Array.isArray(msgs)) {
                    return;
                }

                let adicionouMensagem = false;

                msgs.forEach(function (m) {

                    if (!m || !m.id) {
                        return;
                    }

                    // Se essa mensagem já apareceu,
                    // não adiciona novamente.
                    if (renderedIds.has(m.id)) {
                        return;
                    }

                    renderedIds.add(m.id);

                    elMessages.appendChild(
                        messageRow({
                            sender: m.sender,
                            text: m.text
                        })
                    );

                    adicionouMensagem = true;
                });

                if (adicionouMensagem) {
                    scrollBottom();
                }

                ultCount = msgs.length;

            } catch (e) {

                setOnline(false);

                console.error(
                    "Erro ao buscar mensagens",
                    e
                );
            }
        }
        // ------------ Actions ------------
        async function enviar() {

            const texto = elInput.value.trim();

            if (!texto || !sessaoSelecionada) {
                return;
            }

            elSend.disabled = true;

            try {

                const csrfToken = document
                    .querySelector('meta[name="csrf-token"]')
                    .getAttribute('content');

                const r = await fetch(
                    `/enviar_profissional/${sessaoSelecionada}`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({
                            message: texto
                        })
                    }
                );

                const dados = await r.json();

                if (!r.ok) {
                    throw new Error(
                        dados.erro || 'Falha ao enviar'
                    );
                }

                elInput.value = '';

                await renderIncremental();

            } catch (e) {

                console.error(e);

                toast(
                    e.message || 'Erro ao enviar. Tente de novo.'
                );

            } finally {

                elSend.disabled = false;
                elInput.focus();
            }
        }

        async function encerrar() {

            if (!sessaoSelecionada) {
                return;
            }

            const ok = confirm('Encerrar este atendimento?');

            if (!ok) {
                return;
            }

            try {

                const csrfToken = document
                    .querySelector('meta[name="csrf-token"]')
                    .getAttribute('content');

                const r = await fetch(
                    `/encerrar/${sessaoSelecionada}`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        }
                    }
                );

                const dados = await r.json();

                if (!r.ok) {
                    throw new Error(
                        dados.erro || 'Falha ao encerrar'
                    );
                }

                clearMessagesUI();

                elTitle.textContent = 'Nenhuma sessão selecionada';

                elInput.disabled = true;
                elSend.disabled = true;
                elEnd.disabled = true;

                sessaoSelecionada = null;

                if (pollMessagesTimer) {
                    clearInterval(pollMessagesTimer);
                    pollMessagesTimer = null;
                }

                await carregarSessoes();

                toast('Atendimento encerrado.');

            } catch (e) {

                console.error(e);

                toast(
                    e.message || 'Não foi possível encerrar.'
                );
            }
        }

        // ------------ Wire-up ------------
        elRefresh.addEventListener('click', carregarSessoes);
        elSend.addEventListener('click', enviar);
        elEnd.addEventListener('click', encerrar);

        // Enter envia, Shift+Enter quebra linha
        elInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                enviar();
            }
        });

        // boot
        (async function init() {
            await carregarSessoes();
            startSessionsPolling();
        })();