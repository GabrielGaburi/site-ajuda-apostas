"""Usuário comum: cadastro, perfil, edição do perfil (com troca de e-mail confirmada) e painel."""

import mysql.connector
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db_connection
from extensoes import limiter
from servicos.cadastro import (
    CAMPOS_CADASTRO_USUARIO,
    CAMPOS_EDITAR_MEU_PERFIL,
    MENSAGEM_CADASTRO_RECEBIDO,
    buscar_conta_existente,
    inserir_usuario,
)
from servicos.emails import (
    enviar_email_confirmacao_usuario,
    enviar_email_conta_existente,
    enviar_email_troca_email,
)
from servicos.sessao import redirecionar_para_painel
from validacoes import ErroCadastro, validar_dados_pessoais, validar_senha_e_termos

bp = Blueprint("usuario", __name__)


@bp.route('/cadastro_usuario', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def cadastro_usuario():

    # dicionário com TODOS os campos para manter o formulário preenchido
    dados = {campo: "" for campo, _ in CAMPOS_CADASTRO_USUARIO}

    # Mostra o formulário de novo, destacando o campo com erro
    def erro(campo, mensagem):
        return render_template(
            "cadastro_usuario.html",
            dados=dados,
            campo_erro=campo,
            mensagem_erro=mensagem
        )

    if request.method == 'POST':

        # captura TODOS os campos
        dados = {
            campo: request.form.get(campo, "").strip()
            for campo, _ in CAMPOS_CADASTRO_USUARIO
        }
        dados["email"] = dados["email"].lower()

        # A senha não passa por strip para ficar igual à digitada no login
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get("confirmar_senha", "")
        termos = request.form.get("termos")

        # Validação em ordem de cima para baixo conforme o formulário
        try:
            data_nascimento = validar_dados_pessoais(dados, CAMPOS_CADASTRO_USUARIO)
            validar_senha_e_termos(senha, confirmar_senha, termos)
        except ErroCadastro as e:
            return erro(e.campo, e.mensagem)

        # O hash é gerado antes de consultar o banco, para a resposta levar
        # o mesmo tempo com ou sem conta existente (não revela quem tem conta)
        senha_hash = generate_password_hash(senha)

        # =========================
        # VERIFICA SE O EMAIL OU O CPF JÁ EXISTEM
        # =========================

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor(dictionary=True)

            conta_existente = buscar_conta_existente(cursor, dados["email"], dados["cpf"])

            # Conta já existe: mostra a mesma mensagem de um cadastro novo,
            # sem revelar que a conta existe, e avisa o dono por email
            if conta_existente:

                # Mesmo email, ainda não confirmado: reenvia a confirmação
                if (
                    conta_existente["email"] == dados["email"]
                    and conta_existente["tipo"] == "usuario"
                    and not conta_existente["email_confirmado"]
                ):
                    enviar_email_confirmacao_usuario(conta_existente["email"])
                else:
                    enviar_email_conta_existente(conta_existente["email"])

                flash(MENSAGEM_CADASTRO_RECEBIDO, "success")
                return redirect(url_for('auth.login'))

            # =========================
            # INSERE O USUÁRIO NO MYSQL
            # =========================

            inserir_usuario(cursor, dados, data_nascimento, senha_hash, "usuario")

            conexao.commit()

        except mysql.connector.IntegrityError as erro_banco:

            if conexao:
                conexao.rollback()

            # 1062 = email ou CPF duplicado (outra requisição cadastrou no mesmo instante)
            if erro_banco.errno == 1062:
                flash(MENSAGEM_CADASTRO_RECEBIDO, "success")
                return redirect(url_for('auth.login'))

            current_app.logger.exception("Erro de integridade ao cadastrar usuário.")
            flash("Ocorreu um erro ao realizar o cadastro. Tente novamente.", "danger")
            return erro(None, "")

        except Exception:

            if conexao:
                conexao.rollback()

            current_app.logger.exception("Erro ao cadastrar usuário.")
            flash("Ocorreu um erro ao realizar o cadastro. Tente novamente.", "danger")
            return erro(None, "")

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

        # =========================
        # EMAIL DE CONFIRMAÇÃO
        # =========================

        # A conta acabou de ser criada agora mesmo (chegou até aqui passando
        # pelas checagens de conta existente acima), então avisar que o
        # envio falhou não revela nada sobre outra conta.
        if enviar_email_confirmacao_usuario(dados["email"]):
            flash(MENSAGEM_CADASTRO_RECEBIDO, "success")
        else:
            current_app.logger.error("Falha ao enviar email de confirmação do cadastro.")
            flash(
                "Cadastro recebido, mas não conseguimos enviar o e-mail de confirmação agora. "
                "Use \"Reenviar e-mail de confirmação\" na tela de login.",
                "warning"
            )

        return redirect(url_for('auth.login'))

    # =========================
    # GET
    # =========================

    return erro(None, "")


# =========================
# PERFIL
# =========================
@bp.route("/perfil")
def perfil():
    

    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash(
            "Faça login para acessar seu perfil.",
            "warning"
        )
        return redirect(url_for("auth.login"))


    conexao = None
    cursor = None

    try:

        # =========================
        # CONECTA AO MYSQL
        # =========================

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # =========================
        # BUSCA O USUÁRIO
        # =========================

        
        cursor.execute(
            """
            SELECT *
            FROM usuarios
            WHERE id = %s
              AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        usuario = cursor.fetchone()

        # =========================
        # USUÁRIO NÃO ENCONTRADO
        # =========================

        if not usuario:

            session.clear()

            flash(
                "Usuário não encontrado.",
                "danger"
            )

            return redirect(url_for("auth.login"))

        # =========================
        # IDENTIFICA O TIPO
        # =========================

        tipo = usuario["tipo"]

        # =========================
        # ADMINISTRADOR
        # =========================

        if tipo == "admin":

            return render_template(
                "dashboard_admin.html",
                usuario=usuario
            )

        # =========================
        # PROFISSIONAL
        # =========================

        elif tipo == "profissional":

            return render_template(
                "dashboard_profissional.html",
                usuario=usuario
            )

        # =========================
        # USUÁRIO COMUM
        # =========================

        elif tipo == "usuario":

            return render_template(
                "dashboard_usuario.html",
                usuario=usuario
            )

        # =========================
        # TIPO INVÁLIDO
        # =========================

        else:

            session.clear()

            flash(
                "Tipo de usuário inválido.",
                "danger"
            )

            return redirect(url_for("auth.login"))

    except Exception:
        
        current_app.logger.exception("Erro ao carregar perfil.")

        flash(
            "Ocorreu um erro ao carregar seu perfil.",
            "danger"
        )

        return redirect(url_for("publico.index"))

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/meu-perfil/editar", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def editar_meu_perfil():

    if "usuario_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("auth.login"))

    # O profissional edita pelo próprio perfil, que não deixa mudar os dados conferidos na aprovação
    if session.get("tipo_usuario") == "profissional":
        return redirect(url_for("profissional.editar_perfil_profissional"))

    if session.get("tipo_usuario") != "usuario":
        abort(403)

    usuario_id = session["usuario_id"]

    conexao = None
    cursor = None

    try:

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # =========================
        # BUSCA O USUÁRIO LOGADO
        # =========================

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            WHERE id = %s
              AND status = 'ativo'
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            session.clear()

            flash(
                "Sua sessão foi encerrada. Faça login novamente.",
                "warning"
            )

            return redirect(url_for("auth.login"))

        # Dados atuais, no mesmo formato do formulário
        dados = {campo: usuario.get(campo) or "" for campo, _ in CAMPOS_EDITAR_MEU_PERFIL}
        dados["data_de_nascimento"] = (
            usuario["data_nascimento"].strftime("%d/%m/%Y")
            if usuario["data_nascimento"] else ""
        )

        email_atual = (usuario["email"] or "").lower()

        # Mostra o formulário de novo, destacando o campo com erro
        def erro(campo, mensagem):
            return render_template(
                "editar_meu_perfil.html",
                dados=dados,
                cpf=usuario["cpf"],
                email_atual=email_atual,
                campo_erro=campo,
                mensagem_erro=mensagem
            )

        # =========================
        # POST
        # =========================

        if request.method == "POST":

            dados = {
                campo: request.form.get(campo, "").strip()
                for campo, _ in CAMPOS_EDITAR_MEU_PERFIL
            }
            dados["email"] = dados["email"].lower()

            # A senha não passa por strip para ficar igual à digitada no login
            senha_atual = request.form.get("senha_atual", "")

            # Mesmas regras do cadastro, em ordem de cima para baixo conforme o formulário
            try:
                data_nascimento = validar_dados_pessoais(dados, CAMPOS_EDITAR_MEU_PERFIL)
            except ErroCadastro as e:
                return erro(e.campo, e.mensagem)

            # =========================
            # TROCA DE EMAIL
            # =========================

            # O novo email só vale depois de confirmado pelo link enviado a ele (confirmar_novo_email).
            # A senha atual é pedida para quem estiver com a sessão aberta de outra pessoa
            # não conseguir trocar o email (e depois a senha) da conta.
            email_mudou = dados["email"] != email_atual

            if email_mudou:

                if not senha_atual:
                    return erro("senha_atual", "Informe sua senha atual para trocar o e-mail.")

                if not check_password_hash(usuario["senha_hash"], senha_atual):
                    return erro("senha_atual", "Senha incorreta.")

                cursor.execute(
                    """
                    SELECT id
                    FROM usuarios
                    WHERE email = %s
                      AND id != %s
                    """,
                    (dados["email"], usuario_id)
                )

                if cursor.fetchone():
                    return erro("email", "Este e-mail já está sendo usado por outra conta.")

            # =========================
            # ATUALIZA USUÁRIO (o email continua o atual até a confirmação)
            # =========================

            cursor.execute(
                """
                UPDATE usuarios
                SET
                    nome = %s,
                    sobrenome = %s,
                    data_nascimento = %s,
                    sexo = %s,
                    telefone = %s,
                    cep = %s,
                    estado = %s,
                    cidade = %s,
                    rua = %s,
                    numero = %s,
                    bairro = %s
                WHERE id = %s
                """,
                (
                    dados["nome"],
                    dados["sobrenome"],
                    data_nascimento.strftime("%Y-%m-%d"),
                    dados["sexo"],
                    dados["telefone"],
                    dados["cep"],
                    dados["estado"],
                    dados["cidade"],
                    dados["rua"],
                    dados["numero"],
                    dados["bairro"],
                    usuario_id
                )
            )

            conexao.commit()

            # Atualiza o nome exibido na sessão
            session["usuario_nome"] = dados["nome"]

            if not email_mudou:
                flash("Seus dados foram atualizados com sucesso.", "success")

            elif enviar_email_troca_email(usuario_id, email_atual, dados["email"]):
                flash(
                    f"Seus dados foram atualizados. Enviamos um link para {dados['email']} "
                    "para confirmar o novo e-mail; até lá, continue usando o e-mail atual.",
                    "success"
                )

            else:
                flash(
                    "Seus dados foram atualizados, mas não foi possível enviar o e-mail de confirmação. "
                    "Seu e-mail não foi alterado; tente trocá-lo novamente mais tarde.",
                    "warning"
                )

            return redirect(
                url_for("usuario.perfil")
            )

        return erro(None, "")

    except Exception:

        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao editar o próprio perfil.")

        flash(
            "Ocorreu um erro ao atualizar seus dados.",
            "danger"
        )

        return redirect(
            url_for("publico.index")
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/dashboard_usuario")
def dashboard_usuario():

    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("tipo_usuario") != "usuario":
        flash("Acesso não autorizado.", "danger")
        return redirecionar_para_painel()

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = %s
              AND tipo = 'usuario'
              AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        usuario = cursor.fetchone()

        if not usuario:
            session.clear()
            flash(
                "Sua conta está inativa ou não possui autorização.",
                "warning"
            )
            return redirect(url_for("auth.login"))

        return render_template("dashboard_usuario.html")

    except Exception:
        current_app.logger.exception(
            "Erro ao carregar o painel do usuário."
        )
        flash(
            "Não foi possível carregar seu painel. Tente novamente.",
            "danger"
        )
        return redirect(url_for("auth.login"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
