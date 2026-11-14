# Apoio & Consciência

[![Testes](https://github.com/GabrielGaburi/site-ajuda-apostas/actions/workflows/testes.yml/badge.svg)](https://github.com/GabrielGaburi/site-ajuda-apostas/actions/workflows/testes.yml)
![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white)

Aplicação web em português (pt-BR) de apoio a pessoas afetadas por apostas. Reúne um chatbot com IA que pode transferir a conversa para um profissional humano, um fórum moderado, notícias sobre apostas, um teste de autoavaliação e um mapa de locais de ajuda.

> **Projeto acadêmico.** Começou como TCC em grupo e foi refeito do zero por mim, para estudo e portfólio. Não tem vínculo com órgãos públicos, casas de apostas ou serviços de saúde, e não substitui atendimento profissional. Em crise, ligue 188 (CVV).

<!-- Adicione aqui capturas de tela (ex.: docs/home.png, docs/chatbot.png, docs/painel-profissional.png) e um link para o vídeo de demonstração. -->

## Em 1 minuto (para quem avalia)

**Problema:** quem tem problema com apostas costuma esconder o que sente, e um chatbot sozinho não é seguro nesse contexto. O site combina IA com atendimento humano e trata dados de saúde com cuidado legal e técnico.

**O que este projeto demonstra:**

- **Back-end completo em Flask e MySQL, sem ORM:** autenticação por perfis, 2FA por e-mail, tokens com expiração, upload de imagem, e-mails transacionais e rotina agendada. Cerca de 10 mil linhas, hoje organizadas em Blueprints por domínio, serviços reutilizáveis e hooks globais.
- **Refatoração segura:** o `app.py` começou monolítico e foi dividido sem mudar o comportamento. Cada etapa foi comparada com a anterior e, no fim, o fluxo inteiro foi testado no navegador (login com 2FA, chat com IA, encaminhamento a profissional, fórum e painéis do admin) antes do merge.
- **Segurança verificada, não só declarada:** auditoria própria com 13 achados corrigidos, entre eles uma falha real de concorrência no limite de tentativas do 2FA (tabela na seção "Segurança").
- **Produto com responsabilidade:** IA restrita ao tema, detecção de risco de vida que enxerga tentativas de burlar o texto, moderação do fórum, LGPD (consentimento, exportação e exclusão) e nome abreviado de quem participa do fórum.
- **Engenharia de qualidade:** testes automatizados nas regras de negócio puras (46 em Python e 7 em JavaScript), executados pelo GitHub Actions em cada pull request e em cada push na `main`, com Dependabot ativo.

**Limites, ditos com honestidade:** as rotas e o banco ainda são verificados manualmente (não há testes de integração no repositório), não há decorators de autorização e o controle de conversas da IA vive na memória de um único processo. Cada um está explicado, com o próximo passo, em "Decisões técnicas e próximos passos".

**Por onde olhar o código:** `rotas/chatbot.py` e `servicos/ia.py` (conversa com a IA e transferência a um humano), `deteccao_risco.py`, `moderacao.py` e `normalizacao.py` (texto adversarial, com testes), `rotas/auth.py` e `servicos/doisfa.py` (login e 2FA), `hooks.py` (segurança em toda requisição).

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

1. Crie o banco e as tabelas (`templates/database/schema.sql` define `usuarios` e `profissionais`; as demais tabelas são usadas em `rotas/` e `servicos/`).
2. Rode uma vez `.venv\Scripts\python migrar_lgpd.py` para criar as colunas de consentimento. Sem isso, chat e fórum ficam bloqueados.
3. Agende `flask --app app aplicar-retencao` uma vez por dia para aplicar a retenção de dados.
4. (Opcional) Rode os testes das regras puras, que não precisam do banco:

```powershell
.venv\Scripts\python -m unittest discover -s testes     # validacoes, deteccao_risco, moderacao, normalizacao, nomes
node --test testes/test_validacao_cadastro.js           # static/js/validacao_cadastro.js
```

Veja `.env.example` para todas as variáveis. Para publicar o site, siga a seção abaixo: o Gunicorn não roda no Windows, onde `python app.py` serve só para desenvolvimento.

## Colocando no ar

> **Antes do primeiro acesso público**, confira esta lista. Os itens 1 a 3 são obrigatórios: o site trata dados de saúde (LGPD, art. 11).

1. **Jurídico.** Preencha as variáveis `LEGAL_*` no `.env` (`LEGAL_CONTROLADOR`, `LEGAL_DOCUMENTO`, `LEGAL_ENDERECO`, `LEGAL_ENCARREGADO`, `LEGAL_EMAIL_PRIVACIDADE`, `LEGAL_EMAIL_CONTATO` e `LEGAL_ATUALIZACAO`) e resolva com um advogado os trechos `[A DEFINIR...]` de `templates/termos.html`, `privacidade.html` e `cookies.html` (bases legais, transferência internacional para a OpenAI, prazos de guarda, menores de idade). Depois atualize `TERMOS_VERSAO` em `config.py`: todos os usuários terão de aceitar de novo.
2. **Segredos novos para produção.** `SECRET_KEY` (`python -c "import secrets; print(secrets.token_hex(32))"`), senha do banco, senha de app do Gmail e chave da OpenAI **com limite de gasto e alerta de saldo** (sem créditos o chat deixa de responder). Não reutilize valores de desenvolvimento, e o `.env` nunca vai para o git.
3. **HTTPS.** `HTTPS_ATIVO=true` e `BASE_URL=https://seu-dominio` (os links dos e-mails usam o `BASE_URL`). Com proxy ou túnel na frente (Nginx, cloudflared), use `PROXIES_CONFIAVEIS=1` e deixe o app acessível só pelo proxy (`--bind 127.0.0.1`); caso contrário alguém forja o `X-Forwarded-For` e escapa do limite de tentativas.
4. **Servidor.** Linux, como serviço (systemd), atrás do proxy: `gunicorn app:app --workers 1 --threads 8 --bind 127.0.0.1:8000 --timeout 60`. Use **um processo só**: o controle de conversas em processamento e os limites de tentativas ficam na memória do processo, e com vários processos as contagens se multiplicam. Para escalar, aponte o Flask-Limiter para o Redis e troque o lock em memória.
5. **Banco.** MySQL 8 com o usuário da aplicação limitado a `SELECT, INSERT, UPDATE, DELETE` no banco do site (o schema e o `migrar_lgpd.py` rodam com outro usuário), porta do MySQL fechada para a internet e backup diário (`mysqldump`) com restauração testada.
6. **Rotinas.** Agende `flask --app app aplicar-retencao` uma vez por dia (cron ou timer do systemd) e mande os logs do Gunicorn para arquivo com rotação.
7. **Conteúdo e operação.** Ligue para os serviços de `locais_ajuda.py` e atualize `AJUDA_REVISADA_EM`. Tenha ao menos um profissional aprovado e online para atender as conversas encaminhadas, e um admin com e-mail funcionando (o 2FA é por e-mail).
8. **Teste de fumaça no ambiente real.** Cadastro de usuário → e-mail → login; cadastro de profissional → aprovação → 2FA; esqueci a senha; chat com a IA; pedido de profissional; exportar e excluir a conta; `/ajuda`.

## Segurança

Já implementado:

- CSRF em todos os formulários POST.
- Rate limit nas rotas sensíveis (login, 2FA, cadastro, recuperação de senha e chatbot).
- 2FA por e-mail para admin e profissional, com limite de 5 tentativas por código aplicado de forma atômica (vale também para requisições simultâneas).
- Sessão que expira após 8 horas sem atividade (`SESSAO_HORAS`) e cai quando a senha é trocada. Cookies `HttpOnly`, `SameSite=Lax` e `Secure` com `HTTPS_ATIVO`.
- Cabeçalhos: Content-Security-Policy sem script inline, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`, HSTS com HTTPS e `Cache-Control: no-store` nas páginas autenticadas.
- Tokens com expiração e uso único para confirmação de e-mail e redefinição de senha. Login, recuperação de senha, reenvio de confirmação e cadastro respondem igual (conteúdo e tempo) para contas existentes e inexistentes.
- SQL sempre parametrizado.
- Upload restrito a JPG/PNG, regravado com Pillow (remove EXIF e comentários), com limite de 5 MB e de 50 megapixels.
- Moderação de conteúdo e detecção de risco que enxergam leet-speak, letras separadas, caracteres invisíveis e Unicode disfarçado.
- LGPD: consentimento, minimização, retenção, exportação por lista de campos permitidos, exclusão de conta. No fórum, usuários comuns aparecem como "Maria S.".

### Auditoria feita durante o desenvolvimento

Scripts próprios (cliente de teste do Flask contra o MySQL, com contas descartáveis apagadas no fim; ficam fora do repositório porque mexem no banco), mais `pip-audit` (sem vulnerabilidades conhecidas) e `bandit` (sem achados reais). Cobriram autorização por perfil nas 68 rotas, IDOR, CSRF, limites de tentativas, 2FA, tokens, XSS, SQL injection, upload, redirecionamento aberto, cabeçalhos e cookies, enumeração de usuários, páginas de erro, exportação LGPD, vazamento entre conversas e concorrência. O que foi encontrado:

| Achado | Gravidade | Correção |
|---|---|---|
| Limite de 5 tentativas do 2FA não valia com requisições simultâneas (40 tentativas eram avaliadas) | Alta | reserva atômica da tentativa |
| `.env` com chaves no histórico público do git | Alta | chaves trocadas (o histórico continua público) |
| Sessão válida por 31 dias e ainda viva após trocar a senha | Média | 8 h de inatividade; cai ao trocar a senha |
| Exportação "Baixar meus dados" incluía o segredo do autenticador | Média | lista de campos permitidos |
| Nome completo de quem participa do fórum visível a todos | Média | nome abreviado; visitantes não veem o autor |
| Imagem de 4 MB consumia mais de 450 MB de memória | Média | limite de 50 megapixels |
| Redirecionamento aberto em `/aceitar_termos` | Média | validação com `urlparse` e sem caracteres de controle |
| Detecção de crise pegava 2 de 24 frases reais | Média | novos padrões e normalização de Unicode |
| Moderação burlada em 31 de 33 variações | Baixa | forma canônica do texto |
| Reenvio de confirmação revelava contas pelo tempo de resposta | Baixa | envio em segundo plano |
| Páginas autenticadas no cache; sem `X-Frame-Options` | Baixa | `no-store` e `DENY` |
| Flask 3.1.2 (PYSEC-2026-2151) | Baixa | Flask 3.1.3 |
| Duplo clique na 1ª mensagem criava várias conversas | Baixa | trava por usuário |

**Não coberto:** injeção de prompt contra o modelo real (exige créditos da OpenAI), teste de carga, pentest externo e revisão jurídica.

## Decisões técnicas e próximos passos

- **Blueprints por domínio, sem ORM.** O back-end começou num único `app.py` de ~10 mil linhas, escolha para aprender o fluxo completo (rotas, SQL e e-mail) sem abstrações. Foi dividido em Blueprints (`rotas/`), regras reutilizáveis (`servicos/`) e hooks globais (`hooks.py`), sem alterar o comportamento nos roteiros de teste: cada etapa foi comparada com a anterior, com banco simulado, em requisições que checam status, redirecionamentos, HTML, SQL de escrita e e-mails. Depois, o fluxo completo foi testado à mão no navegador, com banco, e-mail e OpenAI reais, antes do merge. Esses roteiros de comparação ainda não estão no repositório, e a verificação de rotas e banco continua manual. O acesso ao banco continua sendo SQL puro em cada rota; extraí-lo para uma camada de dados é um próximo passo.
- **Respostas da IA em background** (`threading.Thread` com lock por conversa) e polling no front-end, em vez de WebSocket, para manter o deploy simples.
- **Sem decorators de autorização:** cada rota checa a sessão. A auditoria percorreu as 68 rotas com cada perfil e não achou checagem faltando, mas é fácil esquecer uma em rotas novas. Centralizar em decorators é um próximo passo.
- **Estado em memória:** o controle de conversas em processamento e os limites de tentativas vivem no processo. Por isso o deploy usa um processo com várias threads; escalar exige Redis (ver "Colocando no ar").
- **Escolhas de produto:** marcas de casas de apostas não são bloqueadas no fórum (quem conta o que perdeu precisa citá-las), e a detecção de crise erra para o lado de encaminhar a um profissional, mesmo que isso gere alertas a mais.
- **Testes automatizados só nas regras puras:** `validacoes.py`, `deteccao_risco.py`, `moderacao.py`, `normalizacao.py`, `nomes.py` e `validacao_cadastro.js` têm testes (`testes/`). Rotas, banco e autorização por perfil foram auditados com scripts fora do repositório; transformá-los em testes de integração com banco descartável é um próximo passo.

## Estrutura

```
app.py            fábrica do app: configuração, extensões, hooks e Blueprints
config.py         variáveis do .env, constantes e configuração do Flask
extensoes.py      limitador de tentativas, CSRF, e-mail e cliente OpenAI
db.py             conexão com o MySQL
hooks.py          cabeçalhos de segurança, páginas de erro e checagem de conta e consentimento
rotas/            um Blueprint por domínio (publico, conta, auth, usuario, profissional, admin, forum, chatbot)
servicos/         e-mails, 2FA, sessão, LGPD, fotos, notícias, retenção, IA e cadastro
validacoes.py     validações de formulário
deteccao_risco.py detecção de risco de vida e pedido de atendimento humano no chat
moderacao.py      filtro de conteúdo do fórum e da biografia
normalizacao.py   limpeza de texto compartilhada (leet, letras separadas, Unicode)
nomes.py          nome exibido no fórum ("Maria S.")
locais_ajuda.py   locais do mapa de ajuda
migrar_lgpd.py    migração das colunas de LGPD
templates/        páginas Jinja (base.html) e database/schema.sql
static/           js/ e css/ por página
testes/           testes das validações, da detecção de risco e da moderação (Python e JavaScript)
uploads/          fotos de profissionais (criada em execução, fora do git)
.env.example      modelo das variáveis de ambiente
```

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
