"""Autenticação: login e logout, 2FA por e-mail, recuperação de senha e confirmação de e-mail."""

import hashlib
import threading

import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db_connection
from extensoes import limiter
from servicos.doisfa import preparar_codigo_2fa, validar_codigo_2fa
from servicos.emails import (
    enviar_confirmacao_em_background,
    enviar_email_email_alterado,
    enviar_recuperacao_em_background,
)
from servicos.sessao import SENHA_HASH_FALSA, impressao_senha
from servicos.tokens import serializer
from validacoes import senha_valida

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():

    if request.method == "POST":

        # =========================
        # DADOS DIGITADOS
        # =========================

        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        conexao = None
        cursor = None

        try:

            # =========================
            # CONECTA AO MYSQL
            # =========================

            conexao = get_db_connection()
            cursor = conexao.cursor(dictionary=True)

            # =========================
            # PROCURA O EMAIL
            # =========================

            cursor.execute(
                """
                SELECT
                    u.id,
                    u.nome,
                    u.sobrenome,
                    u.email,
                    u.senha_hash,
                    u.tipo,
                    u.status,
                    u.email_confirmado,
                    p.status_aprovacao
                FROM usuarios u
                LEFT JOIN profissionais p
                    ON p.usuario_id = u.id
                WHERE u.email = %s
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            # =========================
            # EMAIL NÃO ENCONTRADO
            # =========================

            if usuario is None:
                # Calcula um hash mesmo sem usuário para a resposta
                # levar o mesmo tempo de um e-mail cadastrado
                check_password_hash(SENHA_HASH_FALSA, senha)

                flash("E-mail ou senha incorretos.", "danger")
                return render_template("login.html", email=email)

            # =========================
            # VERIFICA SENHA
            # ANTES DE QUALQUER STATUS, PARA NÃO REVELAR
            # SE O E-MAIL ESTÁ CADASTRADO
            # =========================

            if not check_password_hash(usuario["senha_hash"], senha):
                flash("E-mail ou senha incorretos.", "danger")
                return render_template("login.html", email=email)

            # =========================
            # VERIFICA STATUS DA CONTA
            # =========================

            if usuario["status"] == "banido":
                flash("Esta conta está bloqueada.", "danger")
                return render_template("login.html", email=email)

            # Somente usuários comuns precisam confirmar o email.
            # Profissionais entram após aprovação do administrador.

            if (
                usuario["tipo"] == "usuario"
                and not usuario["email_confirmado"]
            ):
                flash(
                    "Confirme seu email antes de fazer login.",
                    "warning"
                )
                return render_template("login.html", email=email)

            # =========================
            # VERIFICA APROVAÇÃO
            # SOMENTE PARA PROFISSIONAL
            # =========================

            if usuario["tipo"] == "profissional":

                if usuario["status_aprovacao"] is None:
                    flash("Cadastro não encontrado", "danger")
                    return render_template("login.html", email=email)

                if usuario["status_aprovacao"] == "pendente":
                    flash(
                        "Seu cadastro profissional ainda está aguardando aprovação do administrador.",
                        "warning"
                    )
                    return render_template("login.html", email=email)

                if usuario["status_aprovacao"] == "recusado":
                    flash(
                        "Seu cadastro profissional não foi aprovado pelo administrador.",
                        "danger"
                    )
                    return render_template("login.html", email=email)

            # =========================
            # VERIFICAÇÃO 2FA
            # ADMINISTRADOR E PROFISSIONAL
            # =========================

            if usuario["tipo"] in ("admin", "profissional"):

                session.clear()
                session["2fa_usuario_id"] = usuario["id"]

                if not preparar_codigo_2fa(
                    usuario["id"],
                    usuario["email"]
                ):
                    session.clear()
                    flash(
                        "Não foi possível enviar o código de verificação. Tente novamente.",
                        "danger"
                    )
                    return render_template("login.html", email=email)

                flash(
                    "Enviamos um código de verificação para seu e-mail.",
                    "info"
                )
                return redirect(url_for("auth.verificar_2fa"))

            # =========================
            # LOGIN DIRETO DO USUÁRIO COMUM
            # =========================

            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            session["tipo_usuario"] = usuario["tipo"]
            session["senha_v"] = impressao_senha(usuario["senha_hash"])
            session.permanent = True  # a validade (PERMANENT_SESSION_LIFETIME) passa a valer para o login

            flash(
                f"Bem-vindo(a), {usuario['nome']}!",
                "success"
            )

            # =========================
            # REDIRECIONAMENTO
            # =========================

            if usuario["tipo"] == "admin":
                return redirect(url_for("admin.dashboard_admin"))

            elif usuario["tipo"] == "profissional":
                return redirect(url_for("profissional.dashboard_profissional"))

            else:
                return redirect(url_for("usuario.dashboard_usuario"))

        except Exception:
            if conexao:
                conexao.rollback()

            current_app.logger.exception(
                "Erro ao realizar login no banco de dados."
            )

            flash(
                "Ocorreu um erro ao realizar o login. Tente novamente.",
                "danger"
            )

            return render_template("login.html", email=email)

        finally:
            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@bp.route("/logout", methods=["POST"])
def logout():

    usuario_id = session.get("usuario_id")

    conexao = None
    cursor = None

    try:

        if usuario_id:

            conexao = get_db_connection()
            cursor = conexao.cursor()

            # ========================================
            # FINALIZA ATENDIMENTO ATIVO DO CHATBOT
            # ========================================

            cursor.execute("""
                UPDATE atendimentos_chatbot
                SET status = 'finalizado'
                WHERE usuario_id = %s
                  AND status IN (
                      'ia',
                      'aguardando',
                      'em_atendimento'
                  )
            """, (usuario_id,))

            conexao.commit()


    except Exception:

        if conexao:
            conexao.rollback()

        current_app.logger.exception(
            "Erro ao finalizar atendimentos durante o logout."
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    # ========================================
    # ENCERRA A SESSÃO DO USUÁRIO
    # ========================================

    session.clear()

    flash(
        "Você saiu da sua conta com sucesso.",
        "success"
    )

    return redirect(url_for("auth.login", logout="1"))


@bp.route("/verificar_2fa", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def verificar_2fa():

    usuario_id = session.get("2fa_usuario_id")

    if not usuario_id:
        flash("Faça login novamente.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        codigo = request.form.get("codigo", "").strip()

        if not codigo.isdigit() or len(codigo) != 6:
            flash("Digite um código válido de 6 dígitos.", "danger")
            return render_template("verificar_2fa.html")

        

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute("""
                SELECT id, nome, tipo, status, senha_hash
                FROM usuarios
                WHERE id = %s
            """, (usuario_id,))

            usuario = cursor.fetchone()

            if not usuario or usuario["status"] == "banido":
                session.clear()
                flash("Não foi possível autenticar esta conta.", "danger")
                return redirect(url_for("auth.login"))

            if usuario["tipo"] not in ("admin", "profissional"):
                session.clear()
                flash("Faça login novamente.", "warning")
                return redirect(url_for("auth.login"))

            if usuario["tipo"] == "profissional":
                cursor.execute("""
                    SELECT status_aprovacao
                    FROM profissionais
                    WHERE usuario_id = %s
                """, (usuario_id,))

                profissional = cursor.fetchone()

                if (
                    not profissional
                    or profissional["status_aprovacao"] != "aprovado"
                ):
                    session.clear()
                    flash("A conta profissional não está aprovada.", "danger")
                    return redirect(url_for("auth.login"))
                
            if not validar_codigo_2fa(usuario_id, codigo):
                flash(
                    "Código inválido, expirado ou com tentativas esgotadas.",
                    "danger"
                )
                return render_template("verificar_2fa.html")
                

            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            session["tipo_usuario"] = usuario["tipo"]
            session["senha_v"] = impressao_senha(usuario["senha_hash"])
            session.permanent = True  # a validade (PERMANENT_SESSION_LIFETIME) passa a valer para o login

            flash(
                f"Bem-vindo(a), {usuario['nome']}!",
                "success"
            )

            if usuario["tipo"] == "admin":
                return redirect(url_for("admin.dashboard_admin"))

            return redirect(url_for("profissional.dashboard_profissional"))

        except Exception:
            if conexao:
                conexao.rollback()

            current_app.logger.exception("Erro ao concluir autenticação 2FA.")
            flash("Ocorreu um erro na verificação. Tente novamente.", "danger")
            return render_template("verificar_2fa.html")

        finally:
            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template("verificar_2fa.html")


@bp.route("/reenviar_codigo_2fa", methods=["POST"])
@limiter.limit("5 per minute")
def reenviar_codigo_2fa():

    usuario_id = session.get("2fa_usuario_id")

    if not usuario_id:
        flash("Faça login novamente.", "warning")
        return redirect(url_for("auth.login"))

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, email, tipo, status
            FROM usuarios
            WHERE id = %s
        """, (usuario_id,))

        usuario = cursor.fetchone()

        if (
            not usuario
            or usuario["status"] == "banido"
            or usuario["tipo"] not in ("admin", "profissional")
        ):
            session.clear()
            flash("Não foi possível validar sua conta.", "danger")
            return redirect(url_for("auth.login"))

        if usuario["tipo"] == "profissional":
            cursor.execute("""
                SELECT status_aprovacao
                FROM profissionais
                WHERE usuario_id = %s
            """, (usuario_id,))

            profissional = cursor.fetchone()

            if (
                not profissional
                or profissional["status_aprovacao"] != "aprovado"
            ):
                session.clear()
                flash("A conta profissional não está aprovada.", "danger")
                return redirect(url_for("auth.login"))

        # O reenvio é reservado em uma só instrução. Com SELECT e depois INSERT, pedidos
        # simultâneos passavam todos pela espera de 1 minuto e cada um mandava um e-mail
        cursor.execute("""
            UPDATE codigos_2fa
            SET criado_em = NOW()
            WHERE usuario_id = %s
              AND criado_em <= DATE_SUB(NOW(), INTERVAL 1 MINUTE)
        """, (usuario_id,))

        reservou = cursor.rowcount == 1

        conexao.commit()

        if not reservou:
            # Sem linha de código (já apagada), a reserva é uma linha-marcador que nunca
            # valida (vencida e com as 5 tentativas gastas); salvar_codigo_2fa a substitui.
            # O índice único em usuario_id garante que só uma requisição consiga criá-la.
            cursor.execute("""
                INSERT IGNORE INTO codigos_2fa
                    (usuario_id, codigo_hash, expira_em, tentativas)
                VALUES
                    (%s, %s, NOW(), 5)
            """, (usuario_id, "0" * 64))

            reservou = cursor.rowcount == 1

            conexao.commit()

        if not reservou:
            flash(
                "Aguarde 1 minuto antes de solicitar outro código.",
                "warning"
            )
            return redirect(url_for("auth.verificar_2fa"))

        email = usuario["email"]

    except Exception:
        current_app.logger.exception("Erro ao preparar reenvio do código 2FA.")
        flash("Não foi possível reenviar o código. Tente novamente.", "danger")
        return redirect(url_for("auth.verificar_2fa"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    if preparar_codigo_2fa(usuario_id, email):
        flash("Enviamos um novo código para seu e-mail.", "success")
    else:
        flash("Não foi possível enviar o código. Tente novamente.", "danger")

    return redirect(url_for("auth.verificar_2fa"))


@bp.route("/esqueci-senha", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def esqueci_senha():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, email, tipo, status
                FROM usuarios
                WHERE LOWER(email) = %s
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            # A mensagem exibida e o tempo de resposta precisam ser os
            # mesmos independentemente de o e-mail existir, estar banido ou
            # o envio falhar. Caso contrário, alguém sem login consegue
            # descobrir quais e-mails estão cadastrados (CWE-203). Por isso
            # o envio roda em segundo plano e a resposta já é devolvida
            # com a mesma mensagem genérica em todos os casos.
            if usuario and usuario["status"] == "ativo":
                threading.Thread(
                    target=enviar_recuperacao_em_background,
                    args=(current_app._get_current_object(), email, request.host_url),
                    daemon=True
                ).start()

            flash(
                "Se o e-mail estiver cadastrado e puder receber recuperação, você receberá as instruções.",
                "info"
            )
            return redirect(url_for("auth.login"))

        except Exception:
            if conexao:
                conexao.rollback()

            current_app.logger.exception(
                "Erro ao localizar email para recuperação de senha."
            )

            flash(
                "Ocorreu um erro ao processar a solicitação.",
                "danger"
            )

            return render_template(
                "esqueci_senha.html",
                email=email
            )

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template("esqueci_senha.html")


@bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def redefinir_senha(token):

    conexao = None
    cursor = None

    try:
        # Calcula o hash do token recebido pela URL
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # No POST, bloqueia o registro durante a validação
        consulta = """
            SELECT
                u.id,
                u.email,
                u.tipo,
                u.status,
                t.id AS token_id
            FROM tokens_recuperacao_senha t
            JOIN usuarios u ON u.id = t.usuario_id
            WHERE t.token_hash = %s
              AND t.utilizado_em IS NULL
              AND t.expira_em > NOW()
              AND u.status = 'ativo'
        """

        if request.method == "POST":
            consulta += " FOR UPDATE"

        cursor.execute(consulta, (token_hash,))
        usuario = cursor.fetchone()

        # Token inexistente, expirado, utilizado ou conta inativa
        if not usuario:
            flash("Link inválido ou expirado.", "danger")
            return redirect(url_for("auth.login"))

        if request.method == "POST":

            nova_senha = request.form.get("senha", "")
            confirmar_senha = request.form.get(
                "confirmar_senha", ""
            )

            if nova_senha != confirmar_senha:
                flash(
                    "As senhas não coincidem.",
                    "danger"
                )
                return render_template("redefinir_senha.html")

            if not senha_valida(nova_senha):
                flash(
                    "Senha inválida. Use 8-64 caracteres, "
                    "letra maiúscula, número e caractere especial.",
                    "danger"
                )
                return render_template("redefinir_senha.html")

            nova_senha_hash = generate_password_hash(nova_senha)

            # Atualiza a senha da conta
            cursor.execute(
                """
                UPDATE usuarios
                SET senha_hash = %s
                WHERE id = %s
                  AND status = 'ativo'
                """,
                (nova_senha_hash, usuario["id"])
            )

            if cursor.rowcount != 1:
                conexao.rollback()
                flash(
                    "Não foi possível redefinir a senha.",
                    "danger"
                )
                return redirect(url_for("auth.login"))

            # Invalida todos os tokens ainda não utilizados
            # dessa conta, incluindo o token atual
            cursor.execute(
                """
                UPDATE tokens_recuperacao_senha
                SET utilizado_em = NOW()
                WHERE usuario_id = %s
                  AND utilizado_em IS NULL
                """,
                (usuario["id"],)
            )

            # Confirma senha e invalidação na mesma transação
            conexao.commit()

            flash(
                "Senha redefinida com sucesso! Faça login.",
                "success"
            )

            return redirect(url_for("auth.login"))

        return render_template("redefinir_senha.html")

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao redefinir senha.")

        flash(
            "Ocorreu um erro ao redefinir a senha.",
            "danger"
        )

        return redirect(url_for("auth.login"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route('/confirmar_email/<token>')
def confirmar_email(token):

    try:
        email = serializer.loads(
            token,
            salt='confirmacao-email',
            max_age=3600
        )

    except Exception:
        flash("Link inválido ou expirado.", "danger")
        return redirect(url_for("auth.login"))

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Procura o email no MySQL
        cursor.execute(
            """
            SELECT id, email, email_confirmado, tipo
            FROM usuarios
            WHERE email = %s AND tipo IN ('usuario', 'profissional')
            """,
            (email.lower(),)
        )

        usuario = cursor.fetchone()

        # Email não encontrado
        if not usuario:
            flash("Cadastro não encontrado.", "danger")
            return redirect(url_for("auth.login"))

        # Já confirmado
        if usuario["email_confirmado"]:
            flash(
                "E-mail já confirmado. Faça login.",
                "info"
            )
            return redirect(url_for("auth.login"))

        # Confirma o email
        cursor.execute(
            """
            UPDATE usuarios
            SET email_confirmado = TRUE
            WHERE id = %s AND tipo IN ('usuario', 'profissional')
            """,
            (usuario["id"],)
        )

        conexao.commit()

        if usuario["tipo"] == "profissional":
            flash(
                "E-mail confirmado! Seu cadastro agora será analisado por um administrador.",
                "success"
            )
            return redirect(url_for("auth.login"))

        flash("E-mail confirmado com sucesso! Agora você pode fazer login.", "success")
        
        return redirect(url_for("auth.login"))

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao confirmar email no MySQL.")

        flash(
            "Ocorreu um erro ao confirmar o email.",
            "danger"
        )

        return redirect(url_for("auth.login"))
    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/confirmar_novo_email/<token>")
def confirmar_novo_email(token):
    # Conclui a troca de email pedida em editar_meu_perfil

    try:
        pedido = serializer.loads(token, salt="troca-email", max_age=3600)
        usuario_id = int(pedido["id"])
        email_anterior = str(pedido["atual"]).lower()
        novo_email = str(pedido["novo"]).lower()

    except Exception:
        flash("Link inválido ou expirado.", "danger")
        return redirect(url_for("auth.login"))

    # Depois da troca, volta para o perfil se a pessoa estiver logada nessa conta
    destino = url_for("usuario.perfil") if session.get("usuario_id") == usuario_id else url_for("auth.login")

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, email
            FROM usuarios
            WHERE id = %s
              AND status = 'ativo'
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        # O link só vale enquanto a conta tiver o mesmo email de quando a troca foi pedida
        # (assim ele não pode ser usado de novo depois da troca)
        if not usuario or (usuario["email"] or "").lower() != email_anterior:
            flash("Link inválido ou expirado.", "danger")
            return redirect(destino)

        cursor.execute(
            """
            SELECT id
            FROM usuarios
            WHERE email = %s
              AND id != %s
            """,
            (novo_email, usuario_id)
        )

        if cursor.fetchone():
            flash("Este e-mail já está sendo usado por outra conta.", "warning")
            return redirect(destino)

        cursor.execute(
            """
            UPDATE usuarios
            SET email = %s
            WHERE id = %s
            """,
            (novo_email, usuario_id)
        )

        conexao.commit()

    except mysql.connector.IntegrityError as erro_banco:

        if conexao:
            conexao.rollback()

        # 1062 = outra conta passou a usar o mesmo email no mesmo instante
        if erro_banco.errno == 1062:
            flash("Este e-mail já está sendo usado por outra conta.", "warning")
            return redirect(destino)

        current_app.logger.exception("Erro de integridade ao confirmar troca de email.")
        flash("Ocorreu um erro ao confirmar o novo e-mail.", "danger")
        return redirect(destino)

    except Exception:

        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao confirmar troca de email.")
        flash("Ocorreu um erro ao confirmar o novo e-mail.", "danger")
        return redirect(destino)

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    if not enviar_email_email_alterado(email_anterior, novo_email):
        current_app.logger.error("Falha ao avisar o email antigo sobre a troca de email.")

    flash("E-mail alterado com sucesso.", "success")
    return redirect(destino)


@bp.route("/reenviar_confirmacao", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def reenviar_confirmacao():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        # Mesma mensagem em todos os casos, para não revelar quais emails têm conta
        mensagem_generica = (
            "Se o e-mail estiver cadastrado e ainda não tiver sido confirmado, "
            "você receberá um novo link de confirmação."
        )

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, tipo, email_confirmado, status
                FROM usuarios
                WHERE email = %s AND tipo IN ('usuario', 'profissional')
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            if (
                usuario
                and not usuario["email_confirmado"]
                and usuario["status"] != "banido"
            ):
                # O envio roda em segundo plano para o tempo de resposta ser o mesmo
                # com ou sem conta (ver comentário em esqueci_senha)
                threading.Thread(
                    target=enviar_confirmacao_em_background,
                    args=(current_app._get_current_object(), email, usuario["tipo"], request.host_url),
                    daemon=True
                ).start()

            flash(mensagem_generica, "info")
            return redirect(url_for("auth.login"))

        except Exception:
            current_app.logger.exception("Erro ao reenviar email de confirmação.")

            flash(
                "Ocorreu um erro ao processar a solicitação.",
                "danger"
            )

            return render_template(
                "reenviar_confirmacao.html",
                email=email
            )

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template("reenviar_confirmacao.html")
