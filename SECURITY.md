# Política de segurança

Este é um projeto acadêmico e de portfólio, mas trato a segurança dele a sério porque lida com dados sensíveis (saúde e comportamento de apostas).

## Como reportar uma vulnerabilidade

Não abra uma issue pública. Use um destes canais:

- **Relato privado do GitHub:** aba *Security* do repositório, botão *Report a vulnerability*.
- **E-mail:** gabrielgaburi6@gmail.com

Inclua, se possível, a rota ou o arquivo afetado, os passos para reproduzir e o impacto que você enxerga. Costumo responder em alguns dias.

## O que já foi tratado

Uma auditoria do próprio projeto verificou as rotas por perfil (usuário, profissional e administrador) e corrigiu falhas como condição de corrida no 2FA, redirecionamento aberto e vazamento na exportação de dados. Os detalhes de proteção (CSRF, limite de requisições, cookies, sessão e LGPD) estão no [README](README.md).

## Fora do escopo

Chaves, senhas e o arquivo `.env` nunca fazem parte do repositório. Se você encontrar algum segredo no histórico, avise pelos canais acima. As chaves antigas já foram trocadas.
