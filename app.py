"""Ponto de entrada de "Apoio & Consciência".

Cria o app Flask, aplica a configuração (config.py), liga as extensões (extensoes.py)
e registra os hooks (hooks.py) e os Blueprints de rotas (rotas/).

    .venv\\Scripts\\python app.py          # desenvolvimento
    gunicorn app:app                      # produção
"""

from flask import Flask

from config import configurar_app
from extensoes import iniciar_extensoes
from hooks import bp as bp_hooks
from rotas.admin import bp as bp_admin
from rotas.admin_profissionais import bp as bp_admin_profissionais
from rotas.auth import bp as bp_auth
from rotas.chatbot import bp as bp_chatbot
from rotas.conta import bp as bp_conta
from rotas.forum import bp as bp_forum
from rotas.profissional import bp as bp_profissional
from rotas.publico import bp as bp_publico
from rotas.usuario import bp as bp_usuario

app = Flask(__name__)
configurar_app(app)
iniciar_extensoes(app)

for blueprint in (
    bp_hooks,
    bp_publico,
    bp_conta,
    bp_auth,
    bp_usuario,
    bp_profissional,
    bp_admin,
    bp_admin_profissionais,
    bp_forum,
    bp_chatbot,
):
    app.register_blueprint(blueprint)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
