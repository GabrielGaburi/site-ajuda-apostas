"""Páginas públicas: início, notícias, ajuda, bloqueio de sites, autoavaliação e fotos enviadas."""

import os

from flask import Blueprint, abort, current_app, render_template, request, send_from_directory, session
from werkzeug.utils import secure_filename

from db import get_db_connection
from locais_ajuda import LOCAIS
from servicos.noticias import carregar_noticias

bp = Blueprint("publico", __name__)


@bp.route("/")
def index():
    noticias_completas = carregar_noticias()
    return render_template("index.html", noticias=noticias_completas[:3])


@bp.route("/noticias")
def todas_noticias():
    noticias_completas = carregar_noticias()
    return render_template("noticia.html", noticias=noticias_completas[:9])


@bp.route("/bloqueio")
def bloqueio():
    return render_template("bloqueio.html")


@bp.route("/bloqueio-cpf")
def bloqueio_cpf():
    return render_template("bloqueio_cpf.html")


@bp.route('/escolher_cadastro')
def escolher_cadastro():
    return render_template('escolher_cadastro.html')


@bp.route("/teste", methods=["GET", "POST"])
def teste():

    if request.method == "POST":

        pontos = 0

        # Conta as respostas "sim"
        for pergunta in ["q1", "q2", "q3", "q4"]:
            if request.form.get(pergunta) == "sim":
                pontos += 1

        # Resultado
        if pontos == 0:

            resultado = {
                "titulo": "Nenhum sinal identificado",
                "mensagem": (
                    "Você respondeu não a todas as perguntas. "
                    "Isso indica ausência de sinais de risco relacionados às apostas."
                ),
                "orientacao": (
                    "Mantenha atenção aos sinais de alerta e procure "
                    "informações e orientação caso sua relação com as apostas mude."
                ),
                "classe": "success"
            }

        elif pontos == 1:

            resultado = {
                "titulo": "Possível problema com o jogo",
                "mensagem": (
                    "Você pode estar apresentando sinais de problemas "
                    "relacionados ao jogo."
                ),
                "orientacao": (
                    "Reflita sobre sua relação com as apostas, converse "
                    "com pessoas de confiança e considere buscar acolhimento "
                    "em uma Unidade Básica de Saúde (UBS)."
                ),
                "classe": "warning"
            }

        elif pontos == 2:

            resultado = {
                "titulo": "Possível problema relacionado ao jogo",
                "mensagem": (
                    "Sua pontuação indica que pode existir um problema "
                    "relacionado às apostas."
                ),
                "orientacao": (
                    "É recomendado buscar apoio em uma Unidade Básica "
                    "de Saúde (UBS) ou Centro de Atenção Psicossocial (CAPS)."
                ),
                "classe": "warning"
            }

        elif pontos == 3:

            resultado = {
                "titulo": "Impactos significativos",
                "mensagem": (
                    "Sua relação com o jogo pode estar causando "
                    "impactos significativos."
                ),
                "orientacao": (
                    "Procure apoio em uma Unidade Básica de Saúde (UBS) "
                    "ou Centro de Atenção Psicossocial (CAPS)."
                ),
                "classe": "danger"
            }

        else:

            resultado = {
                "titulo": "Sinais de problemas com o jogo",
                "mensagem": (
                    "Sua pontuação indica sinais importantes "
                    "de problemas relacionados ao jogo."
                ),
                "orientacao": (
                    "Procure rapidamente apoio em uma Unidade Básica "
                    "de Saúde (UBS) ou Centro de Atenção Psicossocial (CAPS)."
                ),
                "classe": "danger"
            }

        return render_template(
            "resultado_teste.html",
            pontos=pontos,
            resultado=resultado
        )

    return render_template("teste.html")


@bp.route("/uploads/<nome_arquivo>")
def servir_upload(nome_arquivo):

    # Só serve fotos registradas em profissionais (nunca as temporárias).
    # Fotos de cadastros pendentes, recusados ou banidos só aparecem para o admin e para o dono.
    if secure_filename(nome_arquivo) != nome_arquivo:
        abort(404)

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT p.usuario_id, p.status_aprovacao, u.status
            FROM profissionais p
            INNER JOIN usuarios u ON u.id = p.usuario_id
            WHERE p.foto = %s
            """,
            (nome_arquivo,)
        )

        foto = cursor.fetchone()

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    if not foto:
        abort(404)

    publica = foto["status_aprovacao"] == "aprovado" and foto["status"] == "ativo"

    if not (
        publica
        or session.get("tipo_usuario") == "admin"
        or session.get("usuario_id") == foto["usuario_id"]
    ):
        abort(404)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        nome_arquivo
    )


@bp.route("/ajuda")
def ajuda():
    locais = LOCAIS

    return render_template(
        "ajuda.html",
        locais=locais,
        revisado_em=os.getenv("AJUDA_REVISADA_EM", "").strip()
    )
