# Apoio & Consciência

Aplicação web em português (pt-BR) de apoio a pessoas afetadas por apostas. Reúne um chatbot com IA que pode transferir a conversa para um profissional humano, um fórum moderado, notícias sobre apostas, um teste de autoavaliação e um mapa de locais de ajuda.

> **Projeto acadêmico.** Começou como TCC em grupo e foi refeito do zero por mim, para estudo e portfólio. Não tem vínculo com órgãos públicos, casas de apostas ou serviços de saúde, e não substitui atendimento profissional. Em crise, ligue 188 (CVV).

<!-- Adicione aqui capturas de tela (ex.: docs/home.png, docs/chatbot.png, docs/painel-profissional.png) e um link para o vídeo de demonstração. -->

## Funcionalidades

- **Chatbot com IA** (OpenAI) restrito a apoio emocional sobre apostas. Passa para um profissional quando o usuário pede ou quando detecta risco.
- **Atendimento humano:** fila de atendimentos, profissional assume a conversa e responde em tempo quase real.
- **Fórum moderado** com filtro de conteúdo proibido (divulgação de apostas, dicas para "recuperar perdas").
- **Teste de autoavaliação**, **notícias** (GNews) e **mapa de locais de ajuda**.
- **Três perfis:** usuário, profissional (cadastro aprovado pelo admin) e admin, com banimento e reativação.
- **LGPD:** consentimento para dados de saúde, exportação, apagamento de conversas e exclusão de conta, retenção automática e páginas legais.

## Stack

| Camada | Tecnologia |
|---|---|
| Back-end | Python, Flask |
| Banco | MySQL (`mysql-connector-python`, SQL parametrizado) |
| IA | OpenAI API |
| E-mail | Flask-Mail (SMTP do Gmail) |
| Segurança | Flask-WTF (CSRF), Flask-Limiter, itsdangerous, Pillow |
| Front-end | Templates Jinja, JavaScript e CSS por página |
| Deploy | Gunicorn |

## Como rodar

Pré-requisitos: Python 3.11 (versão em que foi desenvolvido e testado) e MySQL.

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env      # preencha os valores
.venv\Scripts\python app.py # http://localhost:5000
```

1. Crie o banco e as tabelas (`templates/database/schema.sql` define `usuarios` e `profissionais`; as demais tabelas são usadas em `app.py`).
2. Rode uma vez `.venv\Scripts\python migrar_lgpd.py` para criar as colunas de consentimento. Sem isso, chat e fórum ficam bloqueados.
3. Agende `flask --app app aplicar-retencao` uma vez por dia para aplicar a retenção de dados.
4. (Opcional) Rode os testes das validações de cadastro, que não precisam do banco:

```powershell
.venv\Scripts\python -m unittest discover -s testes     # validacoes.py, deteccao_risco.py, moderacao.py
node --test testes/test_validacao_cadastro.js           # static/js/validacao_cadastro.js
```

Em produção (Linux): `gunicorn app:app`. O Gunicorn não roda no Windows, onde `python app.py` serve só para desenvolvimento. Se houver proxy na frente (Nginx, cloudflared), defina `PROXIES_CONFIAVEIS` com o número de proxies, para o app enxergar o IP real. Veja `.env.example` para todas as variáveis.

## Segurança

Já implementado:

- CSRF em todos os formulários POST.
- Rate limit nas rotas sensíveis (login, 2FA, cadastro, recuperação de senha e chatbot).
- 2FA por e-mail para admin e profissional.
- Cookies `HttpOnly` e `SameSite=Lax` (e `Secure` com `HTTPS_ATIVO`) e cabeçalho Content-Security-Policy.
- Tokens com expiração para confirmação de e-mail e redefinição de senha.
- SQL sempre parametrizado.
- Upload restrito a JPG/PNG, validado com Pillow, com limite de 5 MB.
- Moderação de conteúdo e detecção de risco com correspondência aproximada (Levenshtein e leet-speak).
- LGPD: consentimento, minimização e retenção.

Teste de segurança com [Strix](https://strix.ai) (pentest autônomo), executado só em ambiente local com dados de teste:

| Achado | Severidade | Correção | Revalidado |
|---|---|---|---|
| _a preencher após o teste_ | | | |

Dependências verificadas com `pip-audit`: _a preencher_.

## Decisões técnicas e próximos passos

- **`app.py` único (~10 mil linhas), sem ORM nem blueprints.** Foi uma escolha para aprender o fluxo completo (rotas, SQL e e-mail) sem abstrações. O próximo passo é dividir em blueprints (`auth`, `chatbot`, `forum`, `admin`) e extrair o acesso a dados.
- **Respostas da IA em background** (`threading.Thread` com lock por conversa) e polling no front-end, em vez de WebSocket, para manter o deploy simples.
- **Sem decorators de autorização:** cada rota checa a sessão. Funciona, mas é fácil esquecer uma checagem. Centralizar em decorators é um próximo passo e um dos alvos do teste de segurança.
- **Testes automatizados só nas regras puras:** `validacoes.py`, `deteccao_risco.py`, `moderacao.py`, `normalizacao.py` e `validacao_cadastro.js` têm testes (`testes/`). Rotas, banco e autorização por perfil ainda são verificados manualmente; adicionar testes de autorização por perfil é um próximo passo.

## Estrutura

```
app.py            rotas, regras e e-mails
validacoes.py     validações de formulário
deteccao_risco.py detecção de risco de vida e pedido de atendimento humano no chat
moderacao.py      filtro de conteúdo do fórum e da biografia
normalizacao.py   limpeza de texto compartilhada (leet, letras separadas, Unicode)
locais_ajuda.py   locais do mapa de ajuda
migrar_lgpd.py    migração das colunas de LGPD
templates/        páginas Jinja (base.html) e database/schema.sql
static/           js/ e css/ por página
testes/           testes das validações, da detecção de risco e da moderação (Python e JavaScript)
uploads/          fotos de profissionais (criada em execução, fora do git)
.env.example      modelo das variáveis de ambiente
```
