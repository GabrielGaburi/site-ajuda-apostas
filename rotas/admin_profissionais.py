"""Administração de profissionais: aprovar e recusar cadastros, listar, detalhar, editar, banir e reativar."""

import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from db import get_db_connection
from extensoes import limiter
from servicos.emails import enviar_email_aprovacao, enviar_email_recusa
from servicos.fotos import limpar_fotos_periodicamente, remover_foto_perfil, salvar_foto_perfil
from servicos.profissionais import (
    CAMPOS_CADASTRO_PROFISSIONAL,
    OPCOES_ESPECIALIDADE,
    REGIOES_CRP,
    validar_dados_profissionais,
)
from validacoes import ErroCadastro, validar_dados_pessoais

bp = Blueprint("admin_profissionais", __name__)


@bp.route("/admin/profissionais")
def gerenciar_profissionais():


    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("auth.login"))

    # =========================
    # VERIFICA ADMIN
    # =========================

    if session.get("tipo_usuario") != "admin":
        flash("Você não tem permissão para acessar esta página.", "danger")
        return redirect(url_for("publico.index"))

    conexao = None
    cursor = None

    try:

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # =========================
        # PROFISSIONAIS PENDENTES
        # =========================

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,
                p.crp,
                p.uf_crp,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.experiencia,
                p.foto,
                p.status_aprovacao,

                u.nome,
                u.sobrenome,
                u.email,
                u.telefone,
                u.cidade,
                u.estado,
                u.email_confirmado

            FROM profissionais p

            INNER JOIN usuarios u
                ON u.id = p.usuario_id

            WHERE p.status_aprovacao = 'pendente'

            ORDER BY p.id DESC
            """
        )

        profissionais_pendentes = cursor.fetchall()

        # =========================
        # PROFISSIONAIS APROVADOS
        # =========================

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,
                p.crp,
                p.uf_crp,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.experiencia,
                p.foto,
                p.status_aprovacao,

                u.nome,
                u.sobrenome,
                u.email,
                u.telefone,
                u.cidade,
                u.estado,
                u.status,
                u.email_confirmado

            FROM profissionais p

            INNER JOIN usuarios u
                ON u.id = p.usuario_id

            WHERE p.status_aprovacao = 'aprovado'

            ORDER BY p.id DESC
            """
        )

        profissionais_aprovados = cursor.fetchall()

        return render_template(
            "admin_profissionais.html",
            profissionais=profissionais_pendentes,
            profissionais_aprovados=profissionais_aprovados
        )

    except Exception:
        current_app.logger.exception("Erro ao buscar profissionais.")

        flash(
            "Ocorreu um erro ao carregar os profissionais.",
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


@bp.route("/admin/profissionais/<int:profissional_id>")
def detalhes_profissional(profissional_id):

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

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # =========================
        # BUSCA DADOS DO PROFISSIONAL
        # =========================

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,
                p.crp,
                p.uf_crp,
                p.experiencia,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.biografia,
                p.foto,
                p.status_aprovacao,
                p.data_aprovacao,

                u.nome,
                u.sobrenome,
                u.cpf,
                u.data_nascimento,
                u.sexo,
                u.email,
                u.telefone,
                u.cep,
                u.estado,
                u.cidade,
                u.rua,
                u.numero,
                u.bairro,
                u.email_confirmado,
                u.status

            FROM profissionais p

            INNER JOIN usuarios u
                ON u.id = p.usuario_id

            WHERE p.id = %s
            """,
            (profissional_id,)
        )

        profissional = cursor.fetchone()

        # =========================
        # PROFISSIONAL NÃO ENCONTRADO
        # =========================

        if not profissional:
            flash(
                "Profissional não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin_profissionais.gerenciar_profissionais")
            )

        return render_template(
            "admin_profissional_detalhes.html",
            profissional=profissional
        )

    except Exception:
        current_app.logger.exception(
            "Erro ao buscar detalhes do profissional."
        )

        flash(
            "Ocorreu um erro ao carregar o cadastro.",
            "danger"
        )

        return redirect(
            url_for("admin_profissionais.gerenciar_profissionais")
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route(
    "/admin/profissionais/<int:profissional_id>/aprovar",
    methods=["POST"]
)
def aprovar_profissional(profissional_id):

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
        # BUSCA O PROFISSIONAL
        # =========================

        cursor.execute(
            """
            SELECT
                p.id,
                p.usuario_id,
                p.status_aprovacao,
                u.nome,
                u.email,
                u.email_confirmado
            FROM profissionais p
            INNER JOIN usuarios u
                ON u.id = p.usuario_id
            WHERE p.id = %s
            """,
            (profissional_id,)
        )

        profissional = cursor.fetchone()

        if not profissional:

            flash(
                "Profissional não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin_profissionais.gerenciar_profissionais")
            )

        # =========================
        # VERIFICA SE JÁ FOI DECIDIDO
        # =========================

        if profissional["status_aprovacao"] != "pendente":

            flash(
                "Este cadastro já foi analisado.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_profissionais.detalhes_profissional",
                    profissional_id=profissional_id
                )
            )

        # =========================
        # VERIFICA SE O EMAIL FOI CONFIRMADO
        # =========================

        # Garante que o email é mesmo do profissional antes de aprovar
        if not profissional["email_confirmado"]:

            flash(
                "O profissional ainda não confirmou o e-mail. "
                "Ele pode pedir um novo link em \"Reenviar e-mail de confirmação\" na tela de login.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_profissionais.detalhes_profissional",
                    profissional_id=profissional_id
                )
            )

        # =========================
        # APROVA O PROFISSIONAL
        # =========================

        cursor.execute(
            """
            UPDATE profissionais
            SET
                status_aprovacao = 'aprovado',
                data_aprovacao = NOW()
            WHERE id = %s
            """,
            (profissional_id,)
        )

        conexao.commit()

        # =========================
        # ENVIA EMAIL DE APROVAÇÃO
        # =========================

        email_enviado = enviar_email_aprovacao(
            profissional["email"],
            profissional["nome"]
        )

    
        # =========================
        # MENSAGEM PARA O ADMIN
        # =========================

        if email_enviado:

            flash(
                f"O cadastro de {profissional['nome']} foi aprovado e o profissional foi notificado por email.",
                "success"
            )

        else:

            flash(
                f"O cadastro de {profissional['nome']} foi aprovado, mas não foi possível enviar o email.",
                "warning"
            )

        return redirect(
            url_for("admin_profissionais.gerenciar_profissionais")
        )

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao aprovar profissional.")

        flash(
            "Ocorreu um erro ao aprovar o cadastro.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_profissionais.detalhes_profissional",
                profissional_id=profissional_id
            )
        )

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route(
    "/admin/profissionais/<int:profissional_id>/recusar",
    methods=["POST"]
)
def recusar_profissional(profissional_id):

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
            "Você não tem permissão para realizar esta ação.",
            "danger"
        )
        return redirect(url_for("publico.index"))

    motivo = request.form.get("motivo_recusa", "").strip()

    # =========================
    # VALIDA O MOTIVO
    # =========================

    if not motivo:

        flash(
            "Informe o motivo da recusa.",
            "warning"
        )

        return redirect(
            url_for(
                "admin_profissionais.detalhes_profissional",
                profissional_id=profissional_id
            )
        )

    conexao = None
    cursor = None

    try:

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # =========================
        # BUSCA O PROFISSIONAL
        # =========================

        cursor.execute(
            """
            SELECT
                p.id,
                p.usuario_id,
                p.status_aprovacao,
                u.nome,
                u.email
            FROM profissionais p
            INNER JOIN usuarios u
                ON u.id = p.usuario_id
            WHERE p.id = %s
            """,
            (profissional_id,)
        )

        profissional = cursor.fetchone()

        if not profissional:

            flash(
                "Profissional não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin_profissionais.gerenciar_profissionais")
            )

        # =========================
        # VERIFICA SE JÁ FOI ANALISADO
        # =========================

        if profissional["status_aprovacao"] != "pendente":

            flash(
                "Este cadastro já foi analisado.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_profissionais.detalhes_profissional",
                    profissional_id=profissional_id
                )
            )

        # =========================
        # RECUSA O PROFISSIONAL
        # =========================

        cursor.execute(
            """
            UPDATE profissionais
            SET
                status_aprovacao = 'recusado',
                motivo_recusa = %s,
                data_aprovacao = NOW()
            WHERE id = %s
            """,
            (
                motivo,
                profissional_id
            )
        )

        conexao.commit()


        # =========================
        # ENVIA EMAIL DE RECUSA
        # =========================

        email_enviado = enviar_email_recusa(
            profissional["email"],
            profissional["nome"],
            motivo
        )


        if email_enviado:

            flash(
                f"O cadastro de {profissional['nome']} foi recusado e o profissional foi notificado por email.",
                "success"
            )

        else:

            flash(
                f"O cadastro de {profissional['nome']} foi recusado, mas não foi possível enviar o email.",
                "warning"
            )


        return redirect(
            url_for("admin_profissionais.gerenciar_profissionais")
        )

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao recusar profissional.")

        flash(
            "Ocorreu um erro ao recusar o cadastro.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_profissionais.detalhes_profissional",
                profissional_id=profissional_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/profissionais-aprovados")
def gerenciar_profissionais_aprovados():

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

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # =========================
        # BUSCA PROFISSIONAIS APROVADOS
        # =========================

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,

                p.crp,
                p.uf_crp,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.experiencia,
                p.foto,
                p.status_aprovacao,
                p.data_aprovacao,

                u.nome,
                u.sobrenome,
                u.email,
                u.telefone,
                u.cidade,
                u.estado,
                u.status,
                u.email_confirmado

            FROM profissionais p

            INNER JOIN usuarios u
                ON u.id = p.usuario_id

            WHERE p.status_aprovacao = 'aprovado'

            ORDER BY p.id DESC
            """
        )

        profissionais = cursor.fetchall()

        return render_template(
            "gerenciar_profissionais_aprovados.html",
            profissionais=profissionais
        )

    except Exception:
        current_app.logger.exception(
            "Erro ao buscar profissionais aprovados."
        )

        flash(
            "Ocorreu um erro ao carregar os profissionais aprovados.",
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


@bp.route("/admin/profissionais-aprovados/<int:profissional_id>")
def detalhes_profissional_aprovado(profissional_id):

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

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,

                p.crp,
                p.uf_crp,
                p.experiencia,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.biografia,
                p.foto,
                p.status_aprovacao,
                p.data_aprovacao,

                u.nome,
                u.sobrenome,
                u.cpf,
                u.data_nascimento,
                u.sexo,
                u.email,
                u.telefone,
                u.cep,
                u.estado,
                u.cidade,
                u.rua,
                u.numero,
                u.bairro,
                u.email_confirmado,
                u.status

            FROM profissionais p

            INNER JOIN usuarios u
                ON u.id = p.usuario_id

            WHERE p.id = %s
              AND p.status_aprovacao = 'aprovado'
            """,
            (profissional_id,)
        )

        profissional = cursor.fetchone()

        if not profissional:

            flash(
                "Profissional aprovado não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin_profissionais.gerenciar_profissionais_aprovados")
            )

        return render_template(
            "detalhes_profissional_aprovado.html",
            profissional=profissional
        )

    except Exception:
        current_app.logger.exception(
            "Erro ao carregar profissional aprovado."
        )

        flash(
            "Ocorreu um erro ao carregar os dados do profissional.",
            "danger"
        )

        return redirect(
            url_for("admin_profissionais.gerenciar_profissionais_aprovados")
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# Administrador editando um profissional aprovado
@bp.route("/admin/profissionais-aprovados/<int:profissional_id>/editar", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def editar_profissional_aprovados(profissional_id):

    limpar_fotos_periodicamente()

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

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,
                p.crp,
                p.uf_crp,
                p.experiencia,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.biografia,
                p.foto,
                u.nome,
                u.sobrenome,
                u.cpf,
                u.data_nascimento,
                u.sexo,
                u.email,
                u.telefone,
                u.cep,
                u.estado,
                u.cidade,
                u.rua,
                u.numero,
                u.bairro
            FROM profissionais p
            INNER JOIN usuarios u
                ON u.id = p.usuario_id
            WHERE p.id = %s
              AND p.status_aprovacao = 'aprovado'
            """,
            (profissional_id,)
        )

        profissional = cursor.fetchone()

        if not profissional:
            flash("Profissional aprovado não encontrado.", "danger")
            return redirect(url_for("admin_profissionais.gerenciar_profissionais_aprovados"))

        usuario_id = profissional["usuario_id"]

        # Dados atuais, no mesmo formato do formulário
        dados = {
            campo: "" if profissional.get(campo) is None else str(profissional[campo])
            for campo, _ in CAMPOS_CADASTRO_PROFISSIONAL
        }
        dados["data_de_nascimento"] = (
            profissional["data_nascimento"].strftime("%d/%m/%Y")
            if profissional["data_nascimento"] else ""
        )

        email_atual = (profissional["email"] or "").lower()

        # Mostra o formulário de novo, destacando o campo com erro
        def erro(campo, mensagem):
            return render_template(
                "editar_profissional.html",
                dados=dados,
                profissional=profissional,
                campo_erro=campo,
                mensagem_erro=mensagem,
                especialidades=OPCOES_ESPECIALIDADE,
                regioes_crp=REGIOES_CRP,
                limite_upload_mb=current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
            )

        if request.method == "POST":

            dados = {
                campo: request.form.get(campo, "").strip()
                for campo, _ in CAMPOS_CADASTRO_PROFISSIONAL
            }
            dados["email"] = dados["email"].lower()

            foto = request.files.get("foto")

            # =========================
            # VALIDAÇÕES (mesmas regras do cadastro do profissional)
            # =========================

            try:
                data_nascimento = validar_dados_pessoais(dados, CAMPOS_CADASTRO_PROFISSIONAL)
                validar_dados_profissionais(dados)
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
            # FOTO (opcional: sem arquivo, mantém a atual)
            # =========================

            # Mesma validação do cadastro: confere a imagem com o Pillow e grava uma cópia sem metadados
            foto_nova = None

            if foto and foto.filename:
                try:
                    foto_nova = salvar_foto_perfil(foto, current_app.config["UPLOAD_FOLDER"])
                except ValueError as e:
                    return erro("foto", str(e))

            # A foto é obrigatória, como no cadastro: só pode ficar sem enviar quem já tem uma
            elif not profissional["foto"]:
                return erro("foto", "Selecione uma foto de perfil.")

            try:

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
                      AND tipo = 'profissional'
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

                # =========================
                # ATUALIZA PROFISSIONAL
                # =========================

                cursor.execute(
                    """
                    UPDATE profissionais
                    SET
                        crp = %s,
                        uf_crp = %s,
                        experiencia = %s,
                        especialidade = %s,
                        faculdade = %s,
                        pos = %s,
                        biografia = %s,
                        foto = %s
                    WHERE id = %s
                    """,
                    (
                        dados["crp"],
                        dados["uf_crp"],
                        int(dados["experiencia"]),
                        dados["especialidade"],
                        dados["faculdade"],
                        dados["pos"],
                        dados["biografia"],
                        foto_nova or profissional["foto"],
                        profissional_id
                    )
                )

                conexao.commit()

            except Exception:
                # A foto nova não chegou a ser registrada no banco
                if foto_nova:
                    remover_foto_perfil(foto_nova)
                raise

            # A foto antiga deixou de ser usada
            if foto_nova and profissional["foto"]:
                remover_foto_perfil(profissional["foto"])

            # O profissional entra no site com o e-mail cadastrado: avisa quando o admin troca
            if dados["email"] != email_atual:
                flash(
                    f"Informações atualizadas. O e-mail de acesso passou a ser {dados['email']}; "
                    "avise o profissional.",
                    "success"
                )
            else:
                flash(
                    "Informações do profissional atualizadas com sucesso.",
                    "success"
                )

            return redirect(
                url_for(
                    "admin_profissionais.detalhes_profissional_aprovado",
                    profissional_id=profissional_id
                )
            )

        return erro(None, "")

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao editar profissional.")

        flash(
            "Ocorreu um erro ao editar o profissional.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_profissionais.detalhes_profissional_aprovado",
                profissional_id=profissional_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/profissionais-aprovados/<int:profissional_id>/banir", methods=["POST"])
@limiter.limit("10 per minute")
def banir_profissional(profissional_id):

    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("auth.login"))

    # =========================
    # VERIFICA SE É ADMIN
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
        # BUSCA O PROFISSIONAL
        # =========================

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,
                u.nome,
                u.email,
                u.status,
                p.status_aprovacao
            FROM profissionais p
            INNER JOIN usuarios u
                ON u.id = p.usuario_id
            WHERE p.id = %s
            """,
            (profissional_id,)
        )

        profissional = cursor.fetchone()

        if not profissional:

            flash(
                "Profissional não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin_profissionais.gerenciar_profissionais_aprovados")
            )

        # =========================
        # VERIFICA SE JÁ ESTÁ BANIDO
        # =========================

        if profissional["status"] == "banido":

            flash(
                "Este profissional já está banido.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_profissionais.detalhes_profissional_aprovado",
                    profissional_id=profissional_id
                )
            )

        # =========================
        # BANIR PROFISSIONAL
        # =========================

        cursor.execute(
            """
            UPDATE usuarios
            SET status = 'banido'
            WHERE id = %s
            """,
            (profissional["usuario_id"],)
        )

        conexao.commit()

        flash(
            f"O profissional {profissional['nome']} foi banido com sucesso.",
            "success"
        )

        return redirect(
            url_for("admin_profissionais.gerenciar_profissionais_aprovados")
        )

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao banir profissional.")

        flash(
            "Ocorreu um erro ao banir o profissional.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_profissionais.detalhes_profissional_aprovado",
                profissional_id=profissional_id
            )
        )
    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/profissionais-aprovados/<int:profissional_id>/reativar", methods=["POST"])
@limiter.limit("10 per minute")
def reativar_profissional(profissional_id):

    # =========================
    # VERIFICA LOGIN
    # =========================

    if "usuario_id" not in session:
        flash("Você precisa estar logado.", "warning")
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
        # BUSCA PROFISSIONAL
        # =========================

        cursor.execute(
            """
            SELECT
                p.id AS profissional_id,
                p.usuario_id,
                u.nome,
                u.email,
                u.status
            FROM profissionais p
            INNER JOIN usuarios u
                ON u.id = p.usuario_id
            WHERE p.id = %s
            """,
            (profissional_id,)
        )

        profissional = cursor.fetchone()

        if not profissional:

            flash(
                "Profissional não encontrado.",
                "danger"
            )

            return redirect(
                url_for("admin_profissionais.gerenciar_profissionais_aprovados")
            )

        # =========================
        # VERIFICA SE JÁ ESTÁ ATIVO
        # =========================

        if profissional["status"] == "ativo":

            flash(
                "Este profissional já está ativo.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin_profissionais.detalhes_profissional_aprovado",
                    profissional_id=profissional_id
                )
            )

        # =========================
        # REATIVA O PROFISSIONAL
        # =========================

        cursor.execute(
            """
            UPDATE usuarios
            SET status = 'ativo'
            WHERE id = %s
            """,
            (profissional["usuario_id"],)
        )

        conexao.commit()

        flash(
            f"O profissional {profissional['nome']} foi reativado com sucesso.",
            "success"
        )

        return redirect(
            url_for("admin_profissionais.gerenciar_profissionais_aprovados")
        )

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao reativar profissional.")

        flash(
            "Ocorreu um erro ao reativar o profissional.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_profissionais.detalhes_profissional_aprovado",
                profissional_id=profissional_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
