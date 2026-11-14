"""Configuração do app: variáveis do .env, constantes e as chaves do app.config."""

import os
from datetime import timedelta

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv(override=True)

SECRET_KEY = os.getenv("SECRET_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

# Quantidade de proxies na frente do app (cloudflared, Nginx, hospedagem...).
# Com 0 (padrão), o IP usado é o da conexão direta.
# Só use > 0 se o app estiver MESMO atrás de proxy: sem proxy,
# qualquer pessoa poderia forjar o X-Forwarded-For e burlar o limite de tentativas.
PROXIES_CONFIAVEIS = int(os.getenv("PROXIES_CONFIAVEIS", "0") or 0)

# Scripts só do próprio site e das CDNs usadas (jsDelivr e unpkg). Não há script inline.
# Os estilos aceitam 'unsafe-inline' porque os templates usam atributos style.
POLITICA_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' https://cdn.jsdelivr.net https://unpkg.com",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com",
    # https: porque as imagens das notícias vêm do domínio de cada portal (GNews)
    "img-src 'self' data: https:",
    "font-src 'self' https://cdn.jsdelivr.net",
    "connect-src 'self' https://viacep.com.br",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

# Quanto tempo uma sessão sem atividade continua valendo. Sem isso, um cookie roubado
# serviria por 31 dias (padrão do Flask). Cada requisição renova o prazo.
SESSAO_HORAS = float(os.getenv("SESSAO_HORAS", "8") or 8)

# Endereço público do site, usado nos links enviados por e-mail.
# Não usamos o Host da requisição porque ele pode ser forjado
# (um atacante faria o link de redefinição de senha apontar para o site dele).
BASE_URL = (os.getenv("BASE_URL") or "").rstrip("/")

# Versão dos Termos de Uso e da Política de Privacidade aceita no cadastro
TERMOS_VERSAO = "provisoria-2026-10-26"

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")


def configurar_app(app):
    """Aplica ao app Flask todas as configurações (app.config e proxy reverso)."""

    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    if PROXIES_CONFIAVEIS > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=PROXIES_CONFIAVEIS)

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("HTTPS_ATIVO", "false").lower() == "true"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=SESSAO_HORAS)

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # app.config['SERVER_NAME'] = '192.168.1.11:5000'
    app.config["PREFERRED_URL_SCHEME"] = "https" if app.config["SESSION_COOKIE_SECURE"] else "http"

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False

    # Conta Gmail remetente e senha de app do Gmail (o remetente precisa ser o mesmo Gmail)
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_SUPPRESS_SEND"] = False
