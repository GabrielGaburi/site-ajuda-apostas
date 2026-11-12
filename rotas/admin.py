"""Administração: painel do admin e gerenciamento de usuários (listar, detalhar, editar, banir e reativar)."""

import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from db import get_db_connection
from extensoes import limiter
from servicos.cadastro import CAMPOS_CADASTRO_USUARIO
from servicos.sessao import redirecionar_para_painel
from validacoes import ErroCadastro, validar_dados_pessoais

bp = Blueprint("admin", __name__)


@bp.route("/dashboard_admin")
def dashboard_admin():

    if "usuario_id" not in session:
        flash("Faça login para continuar.", "warning")
        return redirect(url_for("auth.login"))

    if session.get("tipo_usuario") != "admin":
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
              AND tipo = 'admin'
              AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        administrador = cursor.fetchone()

        if not administrador:
            session.clear()
            flash(
                "Sua conta administrativa está inativa ou não possui autorização.",
                "warning"
            )
            return redirect(url_for("auth.login"))

        return render_template("dashboard_admin.html")

    except Exception:
        current_app.logger.exception(
            "Erro ao carregar o painel administrativo."
        )

        flash(
            "Não foi possível carregar o painel administrativo.",
            "danger"
        )
        return redirect(url_for("auth.login"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/usuarios")
def gerenciar_usuarios():

    # =========================
    # VERIFICA SE ESTÁ LOGADO
    # =========================

    if "usuario_id" not in session:
        flash(
            "Você precisa estar logado.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    # =========================
    # VERIFICA SE É ADMIN
    # =========================

    if session.get("tipo_usuario") != "admin":
        flash(
            "Você não tem permissão para acessar esta página.",
            "danger"
        )
        return redirect(url_for("publico.index"))

    conexao = None
    cursor = None

    try:

        # =========================
        # CONECTA AO MYSQL
        # =========================

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)
        
        
        # =========================
        # VALIDA SE O ADMIN ESTÁ ATIVO NO BANCO
        # =========================

        cursor.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = %s
              AND tipo = 'admin'
              AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        administrador = cursor.fetchone()

        if not administrador:
            session.clear()

            flash(
                "Sua conta administrativa está inativa ou não possui autorização.",
                "warning"
            )

            return redirect(url_for("auth.login"))


        # =========================
        # BUSCA USUÁRIOS COMUNS
        # =========================

        cursor.execute(
            """
            SELECT
                id,
                nome,
                sobrenome,
                cpf,
                data_nascimento,
                sexo,
                email,
                telefone,
                cep,
                estado,
                cidade,
                rua,
                numero,
                bairro,
                status,
                email_confirmado,
                termos_aceitos
            FROM usuarios
            WHERE tipo = 'usuario'
            ORDER BY id DESC
            """
        )

        usuarios = cursor.fetchall()

       
        return render_template(
            "gerenciar_usuarios.html",
            usuarios=usuarios
        )

    except Exception:

        current_app.logger.exception(
            "Erro ao carregar a lista de usuários."
        )

        flash(
            "Ocorreu um erro ao carregar os usuários.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard_admin")
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/usuarios/<int:usuario_id>")
def detalhes_usuario(usuario_id):

    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash(
            "Você precisa estar logado.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    # =========================
    # VERIFICA ADMIN
    # =========================

    if session.get("tipo_usuario") != "admin":
        flash(
            "Você não tem permissão para acessar esta página.",
            "danger"
        )
        return redirect(url_for("publico.index"))

    conexao = None
    cursor = None

    try:

        # =========================
        # CONECTA AO MYSQL
        # =========================

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)
        
        
        # =========================
        # VALIDA SE O ADMIN ESTÁ ATIVO NO BANCO
        # =========================

        cursor.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = %s
              AND tipo = 'admin'
              AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        administrador = cursor.fetchone()

        if not administrador:
            session.clear()

            flash(
                "Sua conta administrativa está inativa ou não possui autorização.",
                "warning"
            )

            return redirect(url_for("auth.login"))


        # =========================
        # BUSCA O USUÁRIO
        # =========================
        # IMPORTANTE:
        # Não filtramos pelo status.
        # Assim, usuários ativos E banidos
        # podem ser visualizados pelo administrador.

        cursor.execute(
            """
            SELECT
                id,
                nome,
                sobrenome,
                cpf,
                data_nascimento,
                sexo,
                email,
                telefone,
                cep,
                estado,
                cidade,
                rua,
                numero,
                bairro,
                status,
                email_confirmado,
                termos_aceitos
            FROM usuarios
            WHERE id = %s
              AND tipo = 'usuario'
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        # =========================
        # USUÁRIO NÃO ENCONTRADO
        # =========================

        if usuario is None:

            flash(
                "Usuário não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin.gerenciar_usuarios")
            )


        # =========================
        # ABRE O PERFIL
        # =========================

        return render_template(
            "detalhes_usuario.html",
            usuario=usuario
        )

    except Exception:

        current_app.logger.exception(
            "Erro ao carregar detalhes do usuário."
        )

        flash(
            "Ocorreu um erro ao carregar os dados do usuário.",
            "danger"
        )

        return redirect(
            url_for("admin.gerenciar_usuarios")
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# Administrador editando um usuário comum
@bp.route("/admin/usuarios/<int:usuario_id>/editar", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def editar_usuario(usuario_id):

    if "usuario_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("auth.login"))

    if session.get("tipo_usuario") != "admin":
        flash("Você não tem permissão para realizar esta ação.", "danger")
        return redirect(url_for("publico.index"))

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # =========================
        # BUSCA O USUÁRIO
        # =========================

        cursor.execute(
            """
            SELECT
                id,
                nome,
                sobrenome,
                cpf,
                data_nascimento,
                sexo,
                email,
                telefone,
                cep,
                estado,
                cidade,
                rua,
                numero,
                bairro
            FROM usuarios
            WHERE id = %s
              AND tipo = 'usuario'
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            flash("Usuário não encontrado.", "danger")
            return redirect(url_for("admin.gerenciar_usuarios"))

        # Dados atuais, no mesmo formato do formulário
        dados = {
            campo: "" if usuario.get(campo) is None else str(usuario[campo])
            for campo, _ in CAMPOS_CADASTRO_USUARIO
        }
        dados["data_de_nascimento"] = (
            usuario["data_nascimento"].strftime("%d/%m/%Y")
            if usuario["data_nascimento"] else ""
        )

        email_atual = (usuario["email"] or "").lower()

        # Mostra o formulário de novo, destacando o campo com erro
        def erro(campo, mensagem):
            return render_template(
                "editar_usuario.html",
                dados=dados,
                usuario=usuario,
                campo_erro=campo,
                mensagem_erro=mensagem
            )

        # =========================
        # POST
        # =========================

        if request.method == "POST":

            dados = {
                campo: request.form.get(campo, "").strip()
                for campo, _ in CAMPOS_CADASTRO_USUARIO
            }
            dados["email"] = dados["email"].lower()

            # =========================
            # VALIDAÇÕES (mesmas regras do cadastro)
            # =========================

            try:
                data_nascimento = validar_dados_pessoais(dados, CAMPOS_CADASTRO_USUARIO)
            except ErroCadastro as e:
                return erro(e.campo, e.mensagem)

            # O CPF e o e-mail são únicos no banco: não podem passar para outra conta
            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE REPLACE(REPLACE(cpf, '.', ''), '-', '') = %s
                  AND id != %s
                """,
                (re.sub(r"\D", "", dados["cpf"]), usuario_id)
            )

            if cursor.fetchone():
                return erro("cpf", "Este CPF já está sendo usado por outra conta.")

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
            # ATUALIZA USUÁRIO
            # =========================

            cursor.execute(
                """
                UPDATE usuarios
                SET
                    nome = %s,
                    sobrenome = %s,
                    cpf = %s,
                    data_nascimento = %s,
                    sexo = %s,
                    email = %s,
                    telefone = %s,
                    cep = %s,
                    estado = %s,
                    cidade = %s,
                    rua = %s,
                    numero = %s,
                    bairro = %s
                WHERE id = %s
                  AND tipo = 'usuario'
                """,
                (
                    dados["nome"],
                    dados["sobrenome"],
                    dados["cpf"],
                    data_nascimento.strftime("%Y-%m-%d"),
                    dados["sexo"],
                    dados["email"],
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

            # O usuário entra no site com o e-mail cadastrado: avisa quando o admin troca
            if dados["email"] != email_atual:
                flash(
                    f"Dados atualizados. O e-mail de acesso passou a ser {dados['email']}; "
                    "avise o usuário.",
                    "success"
                )
            else:
                flash(
                    "Dados do usuário atualizados com sucesso.",
                    "success"
                )

            return redirect(
                url_for(
                    "admin.detalhes_usuario",
                    usuario_id=usuario_id
                )
            )

        return erro(None, "")

    except Exception:

        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao editar usuário pelo administrador.")

        flash(
            "Ocorreu um erro ao editar o usuário.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/usuarios/<int:usuario_id>/banir", methods=["POST"])
@limiter.limit("10 per minute")
def banir_usuario(usuario_id):

    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash(
            "Você precisa estar logado.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    # =========================
    # VERIFICA ADMIN
    # =========================

    if session.get("tipo_usuario") != "admin":
        flash(
            "Você não tem permissão para realizar esta ação.",
            "danger"
        )
        return redirect(url_for("publico.index"))

    # =========================
    # IMPede ADMIN DE BANIR A SI MESMO
    # =========================

    if usuario_id == session["usuario_id"]:
        flash(
            "Você não pode banir sua própria conta.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

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
            AND tipo = 'admin'
            AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        administrador = cursor.fetchone()

        if not administrador:
            session.clear()
            flash(
                "Sua conta administrativa está inativa ou não possui autorização.",
                "warning"
            )
            return redirect(url_for("auth.login"))


        # =========================
        # BUSCA USUÁRIO
        # =========================

        cursor.execute(
            """
            SELECT
                id,
                nome,
                sobrenome,
                email,
                tipo,
                status
            FROM usuarios
            WHERE id = %s
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        if not usuario:

            flash(
                "Usuário não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin.gerenciar_usuarios")
            )

        # =========================
        # NÃO PERMITE BANIR OUTRO ADMIN
        # =========================

        if usuario["tipo"] == "admin":

            flash(
                "Contas administrativas não podem ser banidas por esta ação.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.detalhes_usuario",
                    usuario_id=usuario_id
                )
            )

        # =========================
        # VERIFICA SE JÁ ESTÁ BANIDO
        # =========================

        if usuario["status"] == "banido":

            flash(
                "Este usuário já está banido.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin.detalhes_usuario",
                    usuario_id=usuario_id
                )
            )

        # =========================
        # BANIR
        # =========================

        cursor.execute(
            """
            UPDATE usuarios
            SET status = 'banido'
            WHERE id = %s
            """,
            (usuario_id,)
        )

        conexao.commit()

        flash(
            f"O usuário {usuario['nome']} foi banido.",
            "success"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

    
    except Exception:

        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao banir usuário.")


        flash(
            "Ocorreu um erro ao banir o usuário.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/usuarios/<int:usuario_id>/desbanir", methods=["POST"])
@limiter.limit("10 per minute")
def desbanir_usuario(usuario_id):

    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash(
            "Você precisa estar logado.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    # =========================
    # VERIFICA ADMIN
    # =========================

    if session.get("tipo_usuario") != "admin":
        flash(
            "Você não tem permissão para realizar esta ação.",
            "danger"
        )
        return redirect(url_for("publico.index"))

    conexao = None
    cursor = None

    try:

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)
        
        
        # =========================
        # VALIDA SE O ADMIN ESTÁ ATIVO NO BANCO
        # =========================

        cursor.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = %s
              AND tipo = 'admin'
              AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        administrador = cursor.fetchone()

        if not administrador:
            session.clear()

            flash(
                "Sua conta administrativa está inativa ou não possui autorização.",
                "warning"
            )

            return redirect(url_for("auth.login"))


        # =========================
        # BUSCA USUÁRIO
        # =========================

        cursor.execute(
            """
            SELECT
                id,
                nome,
                sobrenome,
                email,
                tipo,
                status
            FROM usuarios
            WHERE id = %s
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        if not usuario:

            flash(
                "Usuário não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin.gerenciar_usuarios")
            )

        # =========================
        # NÃO ALTERA ADMIN
        # =========================

        if usuario["tipo"] == "admin":

            flash(
                "Contas administrativas não podem ser alteradas por esta ação.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.detalhes_usuario",
                    usuario_id=usuario_id
                )
            )

        # =========================
        # VERIFICA SE ESTÁ BANIDO
        # =========================

        if usuario["status"] != "banido":

            flash(
                "Este usuário não está banido.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin.detalhes_usuario",
                    usuario_id=usuario_id
                )
            )

        # =========================
        # DESBANIR
        # =========================

        cursor.execute(
            """
            UPDATE usuarios
            SET status = 'ativo'
            WHERE id = %s
            """,
            (usuario_id,)
        )

        conexao.commit()


        flash(
            f"O usuário {usuario['nome']} foi desbanido.",
            "success"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

    except Exception:

        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao desbanir usuário.")

        flash(
            "Ocorreu um erro ao desbanir o usuário.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/usuarios/<int:usuario_id>/reativar", methods=["POST"])
@limiter.limit("10 per minute")
def reativar_usuario(usuario_id):

    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash(
            "Você precisa estar logado.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    # =========================
    # VERIFICA ADMIN
    # =========================

    if session.get("tipo_usuario") != "admin":
        flash(
            "Você não tem permissão para realizar esta ação.",
            "danger"
        )
        return redirect(url_for("publico.index"))

    conexao = None
    cursor = None

    try:

        # =========================
        # CONECTA AO MYSQL
        # =========================

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)
        
        
        # =========================
        # VALIDA SE O ADMIN ESTÁ ATIVO NO BANCO
        # =========================

        cursor.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = %s
              AND tipo = 'admin'
              AND status = 'ativo'
            """,
            (session["usuario_id"],)
        )

        administrador = cursor.fetchone()

        if not administrador:
            session.clear()

            flash(
                "Sua conta administrativa está inativa ou não possui autorização.",
                "warning"
            )

            return redirect(url_for("auth.login"))


        # =========================
        # BUSCA O USUÁRIO
        # =========================

        cursor.execute(
            """
            SELECT
                id,
                nome,
                email,
                tipo,
                status
            FROM usuarios
            WHERE id = %s
            """,
            (usuario_id,)
        )

        usuario = cursor.fetchone()

        # =========================
        # USUÁRIO NÃO ENCONTRADO
        # =========================

        if not usuario:

            flash(
                "Usuário não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin.gerenciar_usuarios")
            )

        # =========================
        # NÃO PERMITIR ALTERAR ADMIN
        # =========================

        if usuario["tipo"] == "admin":

            flash(
                "Esta ação não pode ser realizada em uma conta administrativa.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.detalhes_usuario",
                    usuario_id=usuario_id
                )
            )

        # =========================
        # VERIFICA SE JÁ ESTÁ ATIVO
        # =========================

        if usuario["status"] == "ativo":

            flash(
                "Este usuário já está ativo.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin.detalhes_usuario",
                    usuario_id=usuario_id
                )
            )

        # =========================
        # REATIVA O USUÁRIO
        # =========================

        cursor.execute(
            """
            UPDATE usuarios
            SET status = 'ativo'
            WHERE id = %s
            """,
            (usuario_id,)
        )

        conexao.commit()


        flash(
            f"O usuário {usuario['nome']} foi reativado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

    except Exception:
        
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao reativar usuário.")

        flash(
            "Ocorreu um erro ao reativar o usuário.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.detalhes_usuario",
                usuario_id=usuario_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
