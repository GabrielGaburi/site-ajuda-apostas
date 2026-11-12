"""Profissionais: cadastro, perfil, edição do perfil e painel do profissional."""

import os
import uuid

import mysql.connector
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from db import get_db_connection
from extensoes import limiter
from servicos.cadastro import buscar_conta_existente, inserir_usuario
from servicos.emails import enviar_email_cadastro_profissional, enviar_email_conta_existente
from servicos.fotos import (
    caminho_foto_temporaria,
    descartar_foto_temporaria,
    limpar_fotos_periodicamente,
    remover_foto_perfil,
    salvar_foto_perfil,
)
from servicos.profissionais import (
    CAMPOS_CADASTRO_PROFISSIONAL,
    CAMPOS_EDITAR_PERFIL_PROFISSIONAL,
    MENSAGEM_CADASTRO_PROFISSIONAL_RECEBIDO,
    OPCOES_ESPECIALIDADE,
    REGIOES_CRP,
    validar_atuacao_profissional,
    validar_dados_profissionais,
)
from servicos.sessao import redirecionar_para_painel
from validacoes import (
    ErroCadastro,
    validar_campos_obrigatorios,
    validar_dados_pessoais,
    validar_senha_e_termos,
    validar_telefone_e_endereco,
)

bp = Blueprint("profissional", __name__)


@bp.route('/cadastro_profissional', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def cadastro_profissional():

    limpar_fotos_periodicamente()

    # A foto temporária pode ter sido apagada pela limpeza (mais de 1 hora);
    # nesse caso esquece ela, para o formulário não dizer que a foto foi mantida
    if (
        session.get("foto_temporaria_profissional")
        and not caminho_foto_temporaria(session["foto_temporaria_profissional"])
    ):
        session.pop("foto_temporaria_profissional", None)

    dados = {campo: "" for campo, _ in CAMPOS_CADASTRO_PROFISSIONAL}

    # Mostra o formulário de novo, destacando o campo com erro
    def erro(campo, mensagem):
        return render_template(
            "cadastro_profissional.html",
            dados=dados,
            campo_erro=campo,
            mensagem_erro=mensagem,
            regioes_crp=REGIOES_CRP,
            especialidades=OPCOES_ESPECIALIDADE,
            limite_upload_mb=current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        )

    if request.method == "POST":

        dados = {
            campo: request.form.get(campo, "").strip()
            for campo, _ in CAMPOS_CADASTRO_PROFISSIONAL
        }
        dados["email"] = dados["email"].lower()

        foto = request.files.get("foto")

        # A senha não passa por strip para ficar igual à digitada no login
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")
        termos = request.form.get("termos")

        # =========================
        # SALVA FOTO TEMPORÁRIA
        # =========================

        # A foto é salva antes das validações, para não precisar ser enviada de novo se houver erro
        if foto and foto.filename:
            try:
                nome_temporario = salvar_foto_perfil(foto, current_app.config["UPLOAD_FOLDER"], prefixo="temp_")
            except ValueError as e:
                return erro("foto", str(e))

            # Troca a foto anterior, se houver, pela nova
            descartar_foto_temporaria()
            session["foto_temporaria_profissional"] = nome_temporario

        foto_temporaria = session.get("foto_temporaria_profissional")

        # Validação em ordem de cima para baixo conforme o formulário
        try:
            data_nascimento = validar_dados_pessoais(dados, CAMPOS_CADASTRO_PROFISSIONAL)
            validar_dados_profissionais(dados)
            validar_senha_e_termos(senha, confirmar_senha, termos)

        except ErroCadastro as e:
            return erro(e.campo, e.mensagem)

        # =========================
        # VERIFICA FOTO
        # =========================

        caminho_temporario = caminho_foto_temporaria(foto_temporaria)

        if not caminho_temporario:
            session.pop("foto_temporaria_profissional", None)
            return erro("foto", "Selecione uma foto de perfil.")

        # O hash é gerado antes de consultar o banco, para a resposta levar
        # o mesmo tempo com ou sem conta existente (não revela quem tem conta)
        senha_hash = generate_password_hash(senha)

        extensao = os.path.splitext(foto_temporaria)[1].lower()
        nome_foto = f"{uuid.uuid4().hex}{extensao}"
        caminho_foto = os.path.join(current_app.config["UPLOAD_FOLDER"], nome_foto)
        foto_movida = False

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor(dictionary=True)

            # =========================
            # VERIFICA SE O EMAIL OU O CPF JÁ EXISTEM
            # =========================

            conta_existente = buscar_conta_existente(cursor, dados["email"], dados["cpf"])

            # Conta já existe: mostra a mesma mensagem de um cadastro novo,
            # sem revelar que a conta existe, e avisa o dono por email
            if conta_existente:
                descartar_foto_temporaria()

                # Mesmo email, profissional que ainda não confirmou: reenvia a confirmação
                if (
                    conta_existente["email"] == dados["email"]
                    and conta_existente["tipo"] == "profissional"
                    and not conta_existente["email_confirmado"]
                ):
                    enviar_email_cadastro_profissional(conta_existente["email"])
                else:
                    enviar_email_conta_existente(conta_existente["email"])

                flash(MENSAGEM_CADASTRO_PROFISSIONAL_RECEBIDO, "success")
                return redirect(url_for("login"))

            # =========================
            # VERIFICA SE O CRP JÁ EXISTE
            # =========================

            # O CRP é um registro público, então pode ser informado ao usuário
            cursor.execute(
                """
                SELECT id
                FROM profissionais
                WHERE crp = %s
                """,
                (dados["crp"],)
            )

            if cursor.fetchone():
                return erro("crp", "Este CRP já está cadastrado.")

            # =========================
            # INSERE O USUÁRIO
            # =========================

            usuario_id = inserir_usuario(cursor, dados, data_nascimento, senha_hash, "profissional")

            # =========================
            # INSERE O PROFISSIONAL
            # =========================

            cursor.execute(
                """
                INSERT INTO profissionais (
                    usuario_id,
                    crp,
                    uf_crp,
                    experiencia,
                    especialidade,
                    faculdade,
                    pos,
                    biografia,
                    foto,
                    status_aprovacao
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    usuario_id,
                    dados["crp"],
                    dados["uf_crp"],
                    dados["experiencia"],
                    dados["especialidade"],
                    dados["faculdade"],
                    dados["pos"],
                    dados["biografia"],
                    nome_foto,
                    "pendente"
                )
            )

            # =========================
            # SALVA A FOTO DEFINITIVA
            # =========================

            # A foto só é movida depois dos INSERTs e antes do commit:
            # se algo falhar, ela volta a ser temporária e o profissional não precisa enviá-la de novo.
            # O utime marca a foto como nova, para limpar_fotos_orfas não apagá-la antes do commit.
            os.replace(caminho_temporario, caminho_foto)
            os.utime(caminho_foto)
            foto_movida = True

            conexao.commit()

        except mysql.connector.IntegrityError as erro_banco:

            if conexao:
                conexao.rollback()

            if foto_movida:
                os.replace(caminho_foto, caminho_temporario)

            # 1062 = email, CPF ou CRP duplicado (outra requisição cadastrou no mesmo instante)
            if erro_banco.errno == 1062:
                descartar_foto_temporaria()
                flash(MENSAGEM_CADASTRO_PROFISSIONAL_RECEBIDO, "success")
                return redirect(url_for("login"))

            current_app.logger.exception("Erro de integridade ao cadastrar profissional.")
            flash("Ocorreu um erro ao realizar o cadastro. Tente novamente.", "danger")
            return erro(None, "")

        except Exception:

            if conexao:
                conexao.rollback()

            if foto_movida:
                os.replace(caminho_foto, caminho_temporario)

            current_app.logger.exception("Erro ao cadastrar profissional no MySQL.")
            flash("Ocorreu um erro ao realizar o cadastro. Tente novamente.", "danger")
            return erro(None, "")

        finally:
            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

        # Só esquece a foto temporária depois que o cadastro foi salvo
        session.pop("foto_temporaria_profissional", None)

        # =========================
        # ENVIA EMAIL DE CONFIRMAÇÃO
        # =========================

        if not enviar_email_cadastro_profissional(dados["email"]):
            current_app.logger.error("Falha ao enviar email de cadastro do profissional.")

        flash(MENSAGEM_CADASTRO_PROFISSIONAL_RECEBIDO, "success")
        return redirect(url_for("login"))

    return erro(None, "")


@bp.route("/perfil_profissional")
def perfil_profissional():

    if "usuario_id" not in session:
        flash("Faça login para acessar seu perfil.", "warning")
        return redirect(url_for("login"))

    if session.get("tipo_usuario") != "profissional":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("login"))

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                u.id,
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
                u.tipo,
                u.status,

                p.id AS profissional_id,
                p.crp,
                p.uf_crp,
                p.experiencia,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.biografia,
                p.foto,
                p.status_aprovacao,
                p.data_aprovacao

            FROM usuarios u

            INNER JOIN profissionais p
                ON p.usuario_id = u.id

            WHERE u.id = %s
            AND u.tipo = 'profissional'
            AND u.status = 'ativo'
            AND p.status_aprovacao = 'aprovado'
            """,
            (session["usuario_id"],)
        )

        profissional = cursor.fetchone()

        if not profissional:
            flash("Profissional não encontrado.", "danger")
            return redirect(url_for("login"))

        return render_template(
            "perfil_profissional.html",
            profissional=profissional
        )

    except Exception:
        current_app.logger.exception("Erro ao carregar perfil profissional.")

        flash(
            "Ocorreu um erro ao carregar seu perfil.",
            "danger"
        )

        return redirect(url_for("login"))

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


#Profissional editando o próprio perfil                      
@bp.route("/perfil_profissional/editar", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def editar_perfil_profissional():

    limpar_fotos_periodicamente()

    if "usuario_id" not in session:
        flash("Faça login para acessar seu perfil.", "warning")
        return redirect(url_for("login"))

    # O usuário comum edita os dados pela própria página
    if session.get("tipo_usuario") == "usuario":
        return redirect(url_for("editar_meu_perfil"))

    if session.get("tipo_usuario") != "profissional":
        abort(403)

    usuario_id = session["usuario_id"]

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                u.id,
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
                p.id AS profissional_id,
                p.crp,
                p.uf_crp,
                p.experiencia,
                p.especialidade,
                p.faculdade,
                p.pos,
                p.biografia,
                p.foto
            FROM usuarios u
            INNER JOIN profissionais p
                ON p.usuario_id = u.id
            WHERE u.id = %s
            AND u.tipo = 'profissional'
            AND u.status = 'ativo'
            AND p.status_aprovacao = 'aprovado'
            """,
            (usuario_id,)
        )

        profissional = cursor.fetchone()

        # Mesmas condições de perfil_profissional: só quem está ativo e aprovado edita o perfil
        if not profissional:
            flash("Profissional não encontrado.", "danger")
            return redirect(url_for("profissional.dashboard_profissional"))

        # Dados atuais, no mesmo formato do formulário
        dados = {
            campo: "" if profissional[campo] is None else str(profissional[campo])
            for campo, _ in CAMPOS_EDITAR_PERFIL_PROFISSIONAL
        }

        # Mostra o formulário de novo, destacando o campo com erro
        def erro(campo, mensagem):
            return render_template(
                "editar_perfil_profissional.html",
                dados=dados,
                profissional=profissional,
                campo_erro=campo,
                mensagem_erro=mensagem,
                especialidades=OPCOES_ESPECIALIDADE,
                limite_upload_mb=current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
            )

        if request.method == "POST":

            dados = {
                campo: request.form.get(campo, "").strip()
                for campo, _ in CAMPOS_EDITAR_PERFIL_PROFISSIONAL
            }

            foto = request.files.get("foto")

            # =========================
            # VALIDAÇÕES (mesmas regras do cadastro do profissional)
            # =========================

            try:
                validar_campos_obrigatorios(dados, CAMPOS_EDITAR_PERFIL_PROFISSIONAL)
                validar_telefone_e_endereco(dados)
                validar_atuacao_profissional(dados)
            except ErroCadastro as e:
                return erro(e.campo, e.mensagem)

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
                # ATUALIZAR USUÁRIO
                # =========================

                cursor.execute(
                    """
                    UPDATE usuarios
                    SET
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
                # ATUALIZAR PROFISSIONAL
                # =========================

                cursor.execute(
                    """
                    UPDATE profissionais
                    SET
                        experiencia = %s,
                        especialidade = %s,
                        faculdade = %s,
                        pos = %s,
                        biografia = %s,
                        foto = %s
                    WHERE usuario_id = %s
                    """,
                    (
                        int(dados["experiencia"]),
                        dados["especialidade"],
                        dados["faculdade"],
                        dados["pos"],
                        dados["biografia"],
                        foto_nova or profissional["foto"],
                        usuario_id
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

            flash(
                "Seu perfil foi atualizado com sucesso.",
                "success"
            )

            return redirect(
                url_for("profissional.perfil_profissional")
            )

        return erro(None, "")

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao editar perfil profissional.")

        flash(
            "Ocorreu um erro ao atualizar seu perfil.",
            "danger"
        )

        return redirect(
            url_for("profissional.perfil_profissional")
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/dashboard_profissional")
def dashboard_profissional():

    if "usuario_id" not in session:
        flash("Faça login para continuar.", "warning")
        return redirect(url_for("login"))

    if session.get("tipo_usuario") != "profissional":
        flash("Acesso não autorizado.", "danger")
        return redirecionar_para_painel()

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT u.id
            FROM usuarios u
            INNER JOIN profissionais p
                ON p.usuario_id = u.id
            WHERE u.id = %s
              AND u.tipo = 'profissional'
              AND u.status = 'ativo'
              AND p.status_aprovacao = 'aprovado'
            """,
            (session["usuario_id"],)
        )

        profissional = cursor.fetchone()

        if not profissional:
            session.clear()
            flash(
                "Sua conta está inativa ou seu cadastro profissional não está aprovado.",
                "warning"
            )
            return redirect(url_for("login"))

        return render_template("dashboard_profissional.html")

    except Exception:
        current_app.logger.exception(
            "Erro ao carregar o painel profissional."
        )

        flash(
            "Não foi possível carregar o painel profissional.",
            "danger"
        )
        return redirect(url_for("login"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
