"""Helpers de sessão e acesso usados por mais de uma rota."""

from urllib.parse import urlparse

from flask import flash, g, redirect, request, session, url_for


def destino_seguro(destino):
    """Aceita só caminhos internos, para o redirecionamento não sair do site."""

    if not destino or not destino.startswith("/") or destino.startswith("//"):
        return url_for("publico.index")

    # Navegadores ignoram tab e quebra de linha dentro da URL ("/<TAB>/site.com" vira
    # "//site.com"); espaços e barras invertidas também são tratados de forma diferente
    # entre navegadores. Qualquer caractere de controle, espaço ou "\" é recusado.
    if "\\" in destino or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in destino):
        return url_for("publico.index")

    partes = urlparse(destino)

    if partes.scheme or partes.netloc:
        return url_for("publico.index")

    return destino


def usuario_comum_logado():
    """Devolve (usuario_id, resposta). Se não houver login, a resposta é o redirecionamento."""

    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "warning")
        return None, redirect(url_for("login"))

    return session["usuario_id"], None


def exigir_consentimento_saude():
    """Para o fórum: sem o consentimento de saúde, leva o usuário à página de aceite."""

    if g.get("consentimento_ok"):
        return None

    flash(
        "Para participar do fórum, é preciso consentir com o tratamento de dados de saúde.",
        "warning"
    )

    return redirect(url_for("conta.aceitar_termos", proximo=request.path))


def redirecionar_para_painel():
    """Leva o usuário logado ao painel do próprio perfil (nunca ao painel de outro)."""

    destino = {
        "usuario": "dashboard_usuario",
        "profissional": "profissional.dashboard_profissional",
        "admin": "dashboard_admin",
    }.get(session.get("tipo_usuario"), "login")

    return redirect(url_for(destino))
