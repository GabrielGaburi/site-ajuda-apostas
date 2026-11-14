"""Extensões Flask e clientes externos, criados sem app e ligados a ele em iniciar_extensoes()."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from openai import OpenAI

from config import OPENAI_API_KEY

limiter = Limiter(key_func=get_remote_address, default_limits=[])
csrf = CSRFProtect()
mail = Mail()
client = OpenAI(api_key=OPENAI_API_KEY)


def iniciar_extensoes(app):
    """Liga as extensões ao app. Chamar depois de config.configurar_app(app)."""

    limiter.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
