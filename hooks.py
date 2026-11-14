"""Hooks que valem para a aplicação inteira, registrados como um Blueprint sem rotas.

- cabeçalhos de segurança e Cache-Control em todas as respostas;
- páginas de erro 429 (limite de tentativas) e 413 (arquivo grande demais);
- checagem de conta ativa, senha atual e aceite dos Termos antes de cada requisição;
- versão (?v=) dos arquivos estáticos e dados legais disponíveis em todos os templates;
- comando `flask aplicar-retencao` (cli_group=None mantém o nome sem prefixo).

Os nomes de endpoint dos conjuntos ENDPOINTS_* seguem o formato <blueprint>.<função>.
"""

import functools
import os
import secrets

import mysql.connector
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for

from config import POLITICA_CSP, TERMOS_VERSAO
from db import get_db_connection
from servicos.lgpd import LEGAL
from servicos.retencao import RETENCAO_CONVERSAS_DIAS, RETENCAO_CONVERSAS_VISITANTES_DIAS, aplicar_retencao
from servicos.sessao import impressao_senha

bp = Blueprint("hooks", __name__, cli_group=None)


# Páginas e respostas que, mesmo sem login, carregam dados pessoais ou de saúde
ENDPOINTS_SEM_CACHE = {
    "auth.login", "auth.verificar_2fa", "auth.redefinir_senha", "auth.esqueci_senha", "conta.aceitar_termos", "usuario.cadastro_usuario",
    "profissional.cadastro_profissional", "auth.reenviar_confirmacao", "auth.reenviar_codigo_2fa", "chatbot.chatbot_historico",
    "chatbot.mensagens", "chatbot.lista_sessoes",
}


@bp.after_app_request
def cabecalhos_de_seguranca(resposta):
    """Cabeçalhos que limitam de onde o navegador aceita scripts, estilos e imagens."""

    resposta.headers.setdefault("Content-Security-Policy", POLITICA_CSP)
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resposta.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
    resposta.headers.setdefault("X-Frame-Options", "DENY")

    # Dados pessoais e de saúde não ficam no cache do navegador: o botão "voltar" depois
    # do logout, em computador compartilhado, não pode mostrar a página anterior
    if request.endpoint != "static" and (
        request.endpoint in ENDPOINTS_SEM_CACHE or "usuario_id" in session
    ):
        resposta.headers.setdefault("Cache-Control", "no-store")

    if current_app.config["SESSION_COOKIE_SECURE"]:
        resposta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")

    return resposta


@bp.app_errorhandler(429)
def limite_excedido(erro):

    mensagem = "Muitas tentativas em pouco tempo. Aguarde um minuto e tente novamente."

    # Rotas chamadas por fetch (ex.: chatbot) esperam JSON
    if request.is_json or request.accept_mimetypes.best == "application/json":
        return {"erro": mensagem}, 429

    return render_template("erro_429.html", mensagem=mensagem), 429


@bp.app_errorhandler(413)
def arquivo_grande_demais(erro):

    limite_mb = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    mensagem = f"O arquivo enviado é grande demais. O limite é de {limite_mb} MB."

    if request.is_json or request.accept_mimetypes.best == "application/json":
        return {"erro": mensagem}, 413

    # O formulário não pode ser lido (o envio foi cortado), então volta para a mesma página
    flash(mensagem, "danger")
    return redirect(request.path)


# Rotas que não exigem o aceite da versão atual dos Termos.
# O chat e suas consultas têm a própria checagem de consentimento.
ENDPOINTS_SEM_ACEITE = {
    "static", "conta.aceitar_termos", "auth.logout", "conta.termos_de_uso", "conta.politica_privacidade",
    "conta.politica_cookies", "chatbot.chatbot", "chatbot.chatbot_historico", "chatbot.voltar_para_ia",
    "conta.registrar_consentimento_chat", "chatbot.mensagens",
}


@bp.before_app_request
def verificar_conta_e_consentimento():
    """Encerra a sessão de quem foi banido e exige o aceite da versão atual dos Termos."""

    # Visitante sem cadastro: o consentimento fica na sessão
    g.consentimento_ok = session.get("consentimento_chat") == TERMOS_VERSAO

    if "usuario_id" not in session or request.endpoint in (None, "static"):
        return None

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT status, senha_hash, termos_versao, consentimento_saude_versao
                FROM usuarios
                WHERE id = %s
                """,
                (session["usuario_id"],)
            )
        except mysql.connector.errors.ProgrammingError:
            # Colunas novas ainda não criadas: rode migrar_lgpd.py
            current_app.logger.error("Colunas de consentimento ausentes na tabela usuarios. Rode migrar_lgpd.py.")

            cursor.execute(
                "SELECT status, senha_hash FROM usuarios WHERE id = %s",
                (session["usuario_id"],)
            )

        usuario = cursor.fetchone()

    except Exception:
        current_app.logger.exception("Erro ao verificar status do usuário.")
        # Nunca libera acesso quando não dá para confirmar o status da
        # conta (ex.: falha transitória no banco): um banimento não pode
        # passar despercebido só porque o banco falhou nesse instante.
        abort(503)

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    if not usuario or usuario["status"] == "banido":
        session.clear()
        flash("Sua conta não está mais ativa.", "danger")
        return redirect(url_for("auth.login"))

    # Sessão aberta antes da troca de senha (ou criada sem a impressão da senha) não vale mais
    if not secrets.compare_digest(
        str(session.get("senha_v", "")),
        impressao_senha(usuario["senha_hash"])
    ):
        session.clear()
        flash("Sua sessão expirou. Faça login novamente.", "warning")
        return redirect(url_for("auth.login"))

    g.consentimento_ok = usuario.get("consentimento_saude_versao") == TERMOS_VERSAO

    if request.endpoint in ENDPOINTS_SEM_ACEITE or "termos_versao" not in usuario:
        return None

    if usuario["termos_versao"] != TERMOS_VERSAO:
        proximo = request.path if request.method == "GET" else None

        return redirect(url_for("conta.aceitar_termos", proximo=proximo))

    return None


@functools.lru_cache(maxsize=512)
def _versao_arquivo_estatico(filename):
    # Lê a data de modificação uma única vez por arquivo (cache em memória);
    # os arquivos estáticos não mudam enquanto o processo está no ar.
    try:
        caminho = os.path.join(current_app.static_folder, filename)
        return int(os.path.getmtime(caminho))
    except (OSError, TypeError, ValueError):
        return None


@bp.app_url_defaults
def versionar_arquivos_estaticos(endpoint, values):
    # Acrescenta ?v=<data de modificação> nos CSS/JS, para o navegador
    # baixar de novo sempre que o arquivo mudar em vez de usar o cache antigo
    if endpoint == "static" and values.get("filename") and "v" not in values:
        versao = _versao_arquivo_estatico(values["filename"])
        if versao is not None:
            values["v"] = versao


@bp.app_context_processor
def injetar_dados_legais():
    return {
        "legal": LEGAL,
        "termos_versao": TERMOS_VERSAO,
        "consentimento_chat_ok": bool(g.get("consentimento_ok")),
        "retencao_conversas_dias": RETENCAO_CONVERSAS_DIAS,
        "retencao_visitantes_dias": RETENCAO_CONVERSAS_VISITANTES_DIAS,
    }


@bp.cli.command("aplicar-retencao")
def comando_aplicar_retencao():
    """Rotina de retenção. Agende para rodar uma vez por dia."""

    for nome, quantidade in aplicar_retencao().items():
        print(f"{nome}: {quantidade}")
