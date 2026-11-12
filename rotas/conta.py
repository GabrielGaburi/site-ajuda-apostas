"""Conta e privacidade (LGPD): termos, política de privacidade e cookies, consentimentos, exportação e exclusão de dados."""

import secrets

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import TERMOS_VERSAO
from db import get_db_connection
from extensoes import limiter
from servicos.lgpd import MENSAGEM_REMOVIDA, apagar_conversas_do_usuario, montar_texto_meus_dados
from servicos.sessao import destino_seguro, usuario_comum_logado

bp = Blueprint("conta", __name__)


@bp.route("/termos")
def termos_de_uso():
    return render_template("termos.html")


@bp.route("/privacidade")
def politica_privacidade():
    return render_template("privacidade.html")


@bp.route("/cookies")
def politica_cookies():
    return render_template("cookies.html")


@bp.route("/aceitar_termos", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def aceitar_termos():
    """Registra o aceite da versão atual dos Termos e o consentimento para dados de saúde."""

    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    proximo = destino_seguro(request.values.get("proximo"))

    if request.method == "GET":
        return render_template("aceitar_termos.html", proximo=proximo)

    if request.form.get("termos") != "aceito":
        flash(
            "Para continuar, aceite os Termos de Uso e a Política de Privacidade.",
            "warning"
        )
        return render_template("aceitar_termos.html", proximo=proximo), 400

    consentimento_saude = request.form.get("consentimento_saude") == "aceito"

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE usuarios
            SET termos_aceitos = 1,
                termos_aceitos_em = NOW(),
                termos_versao = %s
            WHERE id = %s
            """,
            (TERMOS_VERSAO, session["usuario_id"])
        )

        if consentimento_saude:
            cursor.execute(
                """
                UPDATE usuarios
                SET consentimento_saude_em = NOW(),
                    consentimento_saude_versao = %s
                WHERE id = %s
                """,
                (TERMOS_VERSAO, session["usuario_id"])
            )

        conexao.commit()

        flash("Preferências de privacidade registradas.", "success")

        return redirect(proximo)

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao registrar o aceite dos termos.")

        flash("Não foi possível registrar o aceite. Tente novamente.", "danger")

        return render_template("aceitar_termos.html", proximo=proximo), 500

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/chatbot/consentimento", methods=["POST"])
@limiter.limit("10 per minute")
def registrar_consentimento_chat():
    """Consentimento para usar o chat. Visitante: guardado na sessão. Logado: na conta."""

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        session["consentimento_chat"] = TERMOS_VERSAO

        return {"sucesso": True}

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE usuarios
            SET consentimento_saude_em = NOW(),
                consentimento_saude_versao = %s
            WHERE id = %s
            """,
            (TERMOS_VERSAO, usuario_id)
        )

        conexao.commit()

        return {"sucesso": True}

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao registrar o consentimento do chat.")

        return {"erro": "Não foi possível registrar o consentimento."}, 500

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/conta/privacidade")
def minha_privacidade():

    usuario_id, resposta = usuario_comum_logado()

    if resposta:
        return resposta

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                tipo,
                termos_versao,
                termos_aceitos_em,
                consentimento_saude_em,
                consentimento_saude_versao
            FROM usuarios
            WHERE id = %s
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        return render_template("minha_privacidade.html", usuario=usuario)

    except Exception:
        current_app.logger.exception("Erro ao carregar a página de privacidade.")

        flash("Não foi possível carregar a página.", "danger")

        return redirect(url_for("publico.index"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/conta/exportar", methods=["POST"])
@limiter.limit("5 per hour")
def exportar_meus_dados():

    usuario_id, resposta = usuario_comum_logado()

    if resposta:
        return resposta

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        conta = cursor.fetchone() or {}
        conta.pop("senha_hash", None)

        cursor.execute("SELECT * FROM profissionais WHERE usuario_id = %s", (usuario_id,))
        profissional = cursor.fetchone()

        cursor.execute(
            """
            SELECT id, status, motivo, data_inicio
            FROM atendimentos_chatbot
            WHERE usuario_id = %s
            ORDER BY id
            """,
            (usuario_id,)
        )
        atendimentos = cursor.fetchall()

        cursor.execute(
            """
            SELECT m.atendimento_id, m.remetente, m.mensagem, m.data_envio
            FROM mensagens_atendimento m
            INNER JOIN atendimentos_chatbot a
                ON a.id = m.atendimento_id
            WHERE a.usuario_id = %s
            ORDER BY m.id
            """,
            (usuario_id,)
        )
        mensagens_chat = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, titulo, data_criacao
            FROM forum_topicos
            WHERE usuario_id = %s
            ORDER BY id
            """,
            (usuario_id,)
        )
        topicos = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, topico_id, mensagem, data_criacao
            FROM forum_mensagens
            WHERE usuario_id = %s
            ORDER BY id
            """,
            (usuario_id,)
        )
        mensagens_forum = cursor.fetchall()

        texto = montar_texto_meus_dados(
            conta, profissional, atendimentos, mensagens_chat, topicos, mensagens_forum
        )

        return Response(
            texto,
            mimetype="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=meus-dados.txt",
                "Content-Type": "text/plain; charset=utf-8",
                "Cache-Control": "no-store",
            }
        )

    except Exception:
        current_app.logger.exception("Erro ao exportar dados da conta.")

        flash("Não foi possível exportar seus dados agora.", "danger")

        return redirect(url_for("conta.minha_privacidade"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/conta/revogar_consentimento", methods=["POST"])
@limiter.limit("10 per hour")
def revogar_consentimento_saude():

    usuario_id, resposta = usuario_comum_logado()

    if resposta:
        return resposta

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE usuarios
            SET consentimento_saude_em = NULL,
                consentimento_saude_versao = NULL
            WHERE id = %s
            """,
            (usuario_id,)
        )

        # Encerra o que estiver em andamento com a IA ou com profissionais
        cursor.execute(
            """
            UPDATE atendimentos_chatbot
            SET status = 'finalizado'
            WHERE usuario_id = %s
              AND status IN ('ia', 'aguardando', 'em_atendimento')
            """,
            (usuario_id,)
        )

        conexao.commit()

        flash(
            "Consentimento revogado. O chat e o fórum ficam bloqueados até você consentir novamente.",
            "success"
        )

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao revogar o consentimento.")

        flash("Não foi possível revogar o consentimento.", "danger")

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    return redirect(url_for("conta.minha_privacidade"))


@bp.route("/conta/apagar_conversas", methods=["POST"])
@limiter.limit("10 per hour")
def apagar_minhas_conversas():

    usuario_id, resposta = usuario_comum_logado()

    if resposta:
        return resposta

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        apagar_conversas_do_usuario(cursor, usuario_id)

        conexao.commit()

        session.pop("chatbot_atendimento_id", None)

        flash("Suas conversas com o Apoio Virtual foram apagadas.", "success")

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao apagar conversas do usuário.")

        flash("Não foi possível apagar as conversas.", "danger")

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    return redirect(url_for("conta.minha_privacidade"))


@bp.route("/conta/excluir", methods=["POST"])
@limiter.limit("5 per hour")
def excluir_minha_conta():
    """Exclui a conta: apaga as conversas e anonimiza o cadastro e as mensagens do fórum."""

    usuario_id, resposta = usuario_comum_logado()

    if resposta:
        return resposta

    if session.get("tipo_usuario") != "usuario":
        flash(
            "Contas de profissionais e administradores são excluídas pelo e-mail de privacidade.",
            "warning"
        )
        return redirect(url_for("conta.minha_privacidade"))

    senha = request.form.get("senha", "")

    if request.form.get("confirmacao", "").strip().upper() != "EXCLUIR":
        flash('Digite "EXCLUIR" para confirmar.', "warning")
        return redirect(url_for("conta.minha_privacidade"))

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT senha_hash FROM usuarios WHERE id = %s AND tipo = 'usuario'",
            (usuario_id,)
        )

        conta = cursor.fetchone()

        if not conta or not check_password_hash(conta["senha_hash"], senha):
            flash("Senha incorreta.", "danger")
            return redirect(url_for("conta.minha_privacidade"))

        apagar_conversas_do_usuario(cursor, usuario_id)

        cursor.execute("DELETE FROM codigos_2fa WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM tokens_recuperacao_senha WHERE usuario_id = %s", (usuario_id,))

        # O fórum guarda a estrutura das discussões, mas sem o conteúdo do autor
        cursor.execute(
            "UPDATE forum_mensagens SET mensagem = %s WHERE usuario_id = %s",
            (MENSAGEM_REMOVIDA, usuario_id)
        )
        cursor.execute(
            "UPDATE forum_topicos SET titulo = %s WHERE usuario_id = %s",
            ("[tópico removido pelo autor]", usuario_id)
        )

        # O CPF e o e-mail são únicos, então recebem valores que não se repetem
        cursor.execute(
            """
            UPDATE usuarios
            SET nome = 'Usuário',
                sobrenome = 'removido',
                cpf = %s,
                email = %s,
                data_nascimento = '1900-01-01',
                sexo = NULL,
                telefone = NULL,
                cep = NULL,
                estado = NULL,
                cidade = NULL,
                rua = NULL,
                numero = NULL,
                bairro = NULL,
                senha_hash = %s,
                status = 'banido',
                email_confirmado = 0,
                consentimento_saude_em = NULL,
                consentimento_saude_versao = NULL,
                excluido_em = NOW()
            WHERE id = %s
            """,
            (
                f"EXCL{usuario_id:010d}",
                f"excluido-{usuario_id}@invalido.local",
                generate_password_hash(secrets.token_hex(32)),
                usuario_id,
            )
        )

        conexao.commit()

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao excluir a conta.")

        flash("Não foi possível excluir a conta. Nada foi alterado.", "danger")

        return redirect(url_for("conta.minha_privacidade"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    session.clear()

    flash("Sua conta foi excluída e seus dados pessoais foram removidos.", "success")

    return redirect(url_for("publico.index"))
