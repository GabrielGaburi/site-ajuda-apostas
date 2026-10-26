# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

"Apoio & Consciência" é uma aplicação web Flask em português (pt-BR) de apoio a pessoas afetadas por apostas. Tem um chatbot com IA que pode transferir a conversa para profissionais humanos, um fórum moderado, notícias sobre apostas, um teste de autoavaliação e um mapa de locais de ajuda. Todos os identificadores, comentários, templates e textos da interface estão em português, e o código novo deve seguir o mesmo padrão.

## Execução

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py        # roda em 0.0.0.0:5000, debug=False
```

- A configuração de debug do VS Code (`.vscode/launch.json`) roda o `app.py` com `.venv\Scripts\python.exe`. Existe também um diretório `venv/` versionado no git, mas o ambiente realmente usado é o `.venv/`.
- O `gunicorn` está no requirements para deploy (`gunicorn app:app`).
- Antes de usar os recursos de LGPD, rode uma vez `.venv\Scripts\python migrar_lgpd.py` (cria as colunas de consentimento e exclusão em `usuarios`). Sem isso, o chat e o fórum ficam bloqueados por falta de consentimento.
- Retenção de dados: agende `.venv\Scripts\flask --app app aplicar-retencao` para rodar uma vez por dia. Os prazos vêm de `RETENCAO_CONVERSAS_DIAS` (padrão 365) e `RETENCAO_CONVERSAS_VISITANTES_DIAS` (padrão 30) no `.env`.
- Páginas legais (`/termos`, `/privacidade`, `/cookies`): os dados do controlador vêm das variáveis `LEGAL_*` do `.env`; enquanto faltarem, as páginas mostram o aviso de rascunho. Ao mudar o texto jurídico, atualize `TERMOS_VERSAO` em `app.py`: todos os usuários precisarão aceitar de novo e consentir novamente para dados de saúde.
- Não há testes automatizados, linter nem etapa de build. As mudanças são verificadas manualmente no navegador, inclusive no celular.

A configuração vem do `.env`, carregado com `override=True`. As variáveis são `SECRET_KEY`, `BASE_URL`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `MAIL_USERNAME`, `MAIL_PASSWORD` (senha de app do Gmail), `OPENAI_API_KEY` e `GNEWS_API_KEY`. `HTTPS_ATIVO=true` é opcional e ativa cookies de sessão seguros. `PROXIES_CONFIAVEIS` (padrão `0`) é o número de proxies na frente do app (ex.: `1` com o túnel `cloudflared` ou um Nginx); quando é maior que zero, o `ProxyFix` faz o Flask e o `Flask-Limiter` usarem o IP real do visitante.

## Arquitetura

Todo o back-end está em um único `app.py` de ~10 mil linhas: configuração, funções auxiliares, todas as rotas, envio de e-mails e filtros de conteúdo. Não há blueprints, models nem ORM. Para encontrar algo, use grep em `@app.route` ou `def `.

**Banco de dados**: MySQL via `mysql-connector-python`. Cada rota abre a própria conexão com `get_db_connection()`, usa `cursor(dictionary=True)` e SQL puro parametrizado (`%s`), e fecha cursor e conexão no `finally`. O `templates/database/schema.sql` só define `usuarios` e `profissionais`. As outras tabelas usadas pelo código (`atendimentos_chatbot`, `mensagens_atendimento`, `forum_topicos`, `forum_mensagens`, `codigos_2fa`, `tokens_recuperacao_senha`, `noticias_site`) existem apenas no banco real. Para saber as colunas delas, é preciso olhar as queries no `app.py`.

**Autenticação e perfis**: o login usa sessão e não há decorators. Cada rota protegida faz a checagem dentro do próprio código: se `"usuario_id" not in session`, redireciona para o login; depois, se `session.get("tipo_usuario") != "<perfil>"`, retorna `abort(403)`. Existem três perfis em `usuarios.tipo`: `usuario`, `profissional` e `admin`.
- Cada linha de `profissionais` aponta para `usuarios` pelo `usuario_id`.
- O profissional se cadastra e fica aguardando o admin aprovar ou recusar, e cada decisão dispara um e-mail.
- Usuários e profissionais podem ser banidos e reativados (`status` `ativo`/`banido`).
- O login de admin e de profissional exige 2FA por e-mail. A rota `login` grava `session["2fa_usuario_id"]` e envia um código (tabela `codigos_2fa`), e a rota `/verificar_2fa` completa o login.
- A confirmação de e-mail e a redefinição de senha usam tokens do `itsdangerous.URLSafeTimedSerializer`.

**Segurança**:
- CSRF via `Flask-WTF`: todo formulário POST precisa de `csrf_token`.
- `Flask-Limiter` limita rotas sensíveis: `@limiter.limit("5 per minute")` em login, 2FA, cadastro e redefinição de senha, e 20 por minuto no chatbot.
- Cookies `HttpOnly` + `SameSite=Lax`.
- Limite de 5 MB por upload.

**Fluxo do chatbot** (`/chatbot`, `/profissional/atendimentos`, `/assumir_atendimento`, `/enviar_profissional`, `/encerrar`, `/mensagens`):
- Cada conversa é uma linha de `atendimentos_chatbot`, e as mensagens ficam em `mensagens_atendimento`.
- O status passa por `ia` → `aguardando` → `em_atendimento` → `finalizado`:
  - Vai para `aguardando` quando o usuário pede um humano (detectado por `pediu_profissional`) ou quando `detect_critical` identifica risco.
  - Vai para `em_atendimento` quando um profissional assume a conversa.
- As respostas da IA são geradas de forma assíncrona por `processar_ia_em_background`, em uma `threading.Thread`. Um set em memória com lock (`atendimentos_processando`) evita que a mesma conversa seja processada duas vezes. O front-end (`static/js/chatbot.js`) consulta o servidor periodicamente para buscar mensagens novas.
- O cliente OpenAI usa o `SYSTEM_PROMPT`, que limita o bot estritamente a apoio emocional relacionado a apostas.
- `detect_critical` normaliza o texto e faz correspondência aproximada (Levenshtein e leet-speak) contra `CRITICAL_PATTERNS`.

**Moderação de conteúdo**: posts do fórum e outros textos de usuários passam por `verificar_conteudo_proibido`. Essa função normaliza o texto com `normalizar_texto` e o compara com as listas `PALAVRAS_PROIBIDAS`, `FRASES_*` e `TERMOS_PROMOCAO_APOSTAS`. Assim são bloqueados conteúdos como divulgação de apostas e dicas para recuperar perdas.

**Uploads**: as fotos dos profissionais ficam em `uploads/` e são servidas por `/uploads/<filename>`. Só `.jpg`, `.jpeg` e `.png` são aceitos, com validação pelo Pillow.
- Arquivos com prefixo `temp_` são uploads pendentes, registrados em `session["foto_temporaria_profissional"]`.
- `limpar_fotos_temporarias` e `limpar_fotos_orfas` rodam no início das rotas de cadastro e de edição do profissional. Elas apagam arquivos temporários antigos e qualquer arquivo que não esteja em `profissionais.foto`.

**Notícias**: `carregar_noticias` busca notícias na API do GNews, filtra com `noticia_relevante` e guarda em cache na tabela `noticias_site`.

**Front-end**: os templates Jinja ficam em `templates/` e estendem o `base.html`. Cada página tem seu JS em `static/js/` e seu CSS em `static/css/`. `templates/database/schema.sql` e `templates/lib.dom.d.ts` estão em `templates/`, mas não são templates.

## Pontos de atenção

- `@app.route("/")` está registrada duas vezes (`index` e `inicio`), e só a primeira é usada.
- A lista de locais de ajuda (com lat/lng) está escrita direto dentro da rota `ajuda()`.
- `forum.json` e `static/forum.json` são legados, já que o fórum agora lê do MySQL.
