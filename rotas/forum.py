"""Fórum moderado: listagem, criação e leitura de tópicos, respostas, exclusões e painel de moderação."""

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException

from db import get_db_connection
from extensoes import limiter
from moderacao import verificar_conteudo_proibido
from nomes import nome_publico
from servicos.sessao import exigir_consentimento_saude

bp = Blueprint("forum", __name__)


@bp.route("/forum")
def forum_home():

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                t.id,
                t.titulo,
                t.usuario_id,
                u.nome,
                u.sobrenome,
                u.tipo AS tipo_autor,
                t.data_criacao
            FROM forum_topicos t
            INNER JOIN usuarios u
                ON u.id = t.usuario_id
            ORDER BY t.data_criacao DESC
            LIMIT 100
        """)

        forum = cursor.fetchall()

        # A lista é pública: visitantes não veem quem escreveu, e quem está logado vê o
        # nome abreviado. Nome e sobrenome saem do dicionário para nem chegarem ao template
        logado = "usuario_id" in session

        for topico in forum:
            nome = topico.pop("nome")
            sobrenome = topico.pop("sobrenome")
            tipo_autor = topico.pop("tipo_autor")
            topico["autor"] = nome_publico(nome, sobrenome, tipo_autor) if logado else "um participante"

        return render_template(
            "forum.html",
            forum=forum
        )

    except Exception:
        current_app.logger.exception("Erro ao carregar fórum.")

        flash(
            "Ocorreu um erro ao carregar o fórum.",
            "danger"
        )

        return redirect(url_for("publico.index"))

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/forum/novo", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def forum_novo():

    # Precisa estar logado
    if "usuario_id" not in session:
        flash("Você precisa estar logado para criar um tópico.", "warning")
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    usuario_nome = session.get("usuario_nome", "")

    if request.method == "POST":

        sem_consentimento = exigir_consentimento_saude()

        if sem_consentimento:
            return sem_consentimento

        titulo = request.form.get("titulo", "").strip()
        mensagem = request.form.get("mensagem", "").strip()

        # Validação do título
        if not titulo:
            return render_template(
                "novo_topico.html",
                usuario_nome=usuario_nome,
                campo_erro="titulo",
                mensagem_erro="O título é obrigatório."
            )

        if len(titulo) > 150:
            return render_template(
                "novo_topico.html",
                usuario_nome=usuario_nome,
                campo_erro="titulo",
                mensagem_erro="O título deve ter no máximo 150 caracteres."
            )

        # Validação da mensagem
        if not mensagem:
            return render_template(
                "novo_topico.html",
                usuario_nome=usuario_nome,
                campo_erro="mensagem",
                mensagem_erro="A mensagem é obrigatória."
            )

        if len(mensagem) > 3000:
            return render_template(
                "novo_topico.html",
                usuario_nome=usuario_nome,
                campo_erro="mensagem",
                mensagem_erro="A mensagem deve ter no máximo 3000 caracteres."
            )

        # Verifica conteúdo proibido no título e na mensagem
        conteudo_proibido = verificar_conteudo_proibido(titulo)

        if conteudo_proibido:
            return render_template(
                "novo_topico.html",
                usuario_nome=usuario_nome,
                campo_erro="titulo",
                mensagem_erro=conteudo_proibido
            )

        conteudo_proibido = verificar_conteudo_proibido(mensagem)

        if conteudo_proibido:
            return render_template(
                "novo_topico.html",
                usuario_nome=usuario_nome,
                campo_erro="mensagem",
                mensagem_erro=conteudo_proibido
            )

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            # Inicia a transação
            conexao.start_transaction()

            # Cria o tópico
            cursor.execute(
                """
                INSERT INTO forum_topicos
                    (usuario_id, titulo)
                VALUES
                    (%s, %s)
                """,
                (usuario_id, titulo)
            )

            # Obtém o ID gerado pelo MySQL
            topico_id = cursor.lastrowid

            # Cria a primeira mensagem do tópico
            cursor.execute(
                """
                INSERT INTO forum_mensagens
                    (topico_id, usuario_id, mensagem)
                VALUES
                    (%s, %s, %s)
                """,
                (topico_id, usuario_id, mensagem)
            )

            # Confirma as duas operações
            conexao.commit()

            flash("Tópico criado com sucesso.", "success")

            return redirect(
                url_for("forum.forum_topico", topico_id=topico_id)
            )

        except Exception:
            if conexao:
                conexao.rollback()

            current_app.logger.exception("Erro ao criar tópico.")

            flash(
                "Ocorreu um erro ao criar o tópico.",
                "danger"
            )

            return render_template(
                "novo_topico.html",
                usuario_nome=usuario_nome,
                campo_erro=None,
                mensagem_erro=None
            )

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template(
        "novo_topico.html",
        usuario_nome=usuario_nome
    )


@bp.route("/forum/<int:topico_id>", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def forum_topico(topico_id):

    # Precisa estar logado
    if "usuario_id" not in session:
        flash(
            "Você precisa estar logado para participar do fórum.",
            "warning"
        )
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    usuario_nome = session.get("usuario_nome", "")

    if request.method == "POST":
        sem_consentimento = exigir_consentimento_saude()

        if sem_consentimento:
            return sem_consentimento

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Busca o tópico
        cursor.execute(
            """
            SELECT
                t.id,
                t.titulo,
                t.usuario_id,
                u.nome,
                u.sobrenome,
                u.tipo AS tipo_autor,
                t.data_criacao
            FROM forum_topicos t
            INNER JOIN usuarios u
                ON u.id = t.usuario_id
            WHERE t.id = %s
            """,
            (topico_id,)
        )

        topico = cursor.fetchone()

        if not topico:
            abort(404)

        # Busca as mensagens do tópico
        cursor.execute(
            """
            SELECT
                m.id,
                m.topico_id,
                m.usuario_id,
                m.mensagem,
                m.data_criacao,
                u.nome,
                u.sobrenome,
                u.tipo AS tipo_usuario
            FROM forum_mensagens m
            INNER JOIN usuarios u
                ON u.id = m.usuario_id
            WHERE m.topico_id = %s
            ORDER BY m.data_criacao ASC
            """,
            (topico_id,)
        )

        mensagens = cursor.fetchall()

        # Nome abreviado para os outros participantes (ver nomes.py)
        topico["autor"] = nome_publico(topico.pop("nome"), topico.pop("sobrenome"), topico.pop("tipo_autor"))

        for msg in mensagens:
            msg["autor"] = nome_publico(msg.pop("nome"), msg.pop("sobrenome"), msg["tipo_usuario"])

        # Adiciona as mensagens ao objeto do tópico
        topico["mensagens"] = mensagens

        # Se estiver enviando uma nova mensagem
        if request.method == "POST":

            mensagem = request.form.get("mensagem", "").strip()

            # Mensagem vazia
            if not mensagem:
                return render_template(
                    "topico.html",
                    topico=topico,
                    usuario_nome=usuario_nome,
                    campo_erro="mensagem",
                    mensagem_erro="A mensagem é obrigatória."
                )

            # Limite de caracteres
            if len(mensagem) > 3000:
                flash(
                    "A mensagem deve ter no máximo 3000 caracteres.",
                    "warning"
                )
                return redirect(
                    url_for(
                        "forum.forum_topico",
                        topico_id=topico_id
                    )
                )

            # Verifica conteúdo proibido
            conteudo_proibido = verificar_conteudo_proibido(mensagem)

            if conteudo_proibido:
                return render_template(
                    "topico.html",
                    topico=topico,
                    usuario_nome=usuario_nome,
                    campo_erro="mensagem",
                    mensagem_erro=conteudo_proibido
                )

            # Salva a nova mensagem no MySQL
            cursor.execute(
                """
                INSERT INTO forum_mensagens
                    (topico_id, usuario_id, mensagem)
                VALUES
                    (%s, %s, %s)
                """,
                (topico_id, usuario_id, mensagem)
            )

            conexao.commit()

            flash("Mensagem enviada com sucesso.", "success")

            return redirect(
                url_for(
                    "forum.forum_topico",
                    topico_id=topico_id
                )
            )

        return render_template(
            "topico.html",
            topico=topico,
            usuario_nome=usuario_nome
        )

    except HTTPException:
        raise

    except Exception:
        
        if conexao:
            conexao.rollback()

        current_app.logger.exception(
            "Erro ao carregar ou enviar mensagem do fórum."
        )

        flash(
            "Ocorreu um erro ao carregar o tópico.",
            "danger"
        )

        return redirect(url_for("forum.forum_home"))

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/forum/<int:topico_id>/excluir", methods=["POST"])
@limiter.limit("20 per minute")
def excluir_topico(topico_id):

    # Precisa estar logado
    if "usuario_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    tipo_usuario = session.get("tipo_usuario")

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Busca o tópico e identifica o proprietário
        cursor.execute(
            """
            SELECT
                id,
                usuario_id,
                titulo
            FROM forum_topicos
            WHERE id = %s
            """,
            (topico_id,)
        )

        topico = cursor.fetchone()

        if not topico:
            abort(404)

        dono_topico = topico["usuario_id"]

        # Somente o dono ou administrador pode excluir
        if dono_topico != usuario_id and tipo_usuario != "admin":
            flash(
                "Você não tem permissão para excluir este tópico.",
                "danger"
            )
            return redirect(
                url_for(
                    "forum.forum_topico",
                    topico_id=topico_id
                )
            )

        # Exclui o tópico
        # As mensagens são excluídas automaticamente
        # por causa do ON DELETE CASCADE
        cursor.execute(
            """
            DELETE FROM forum_topicos
            WHERE id = %s
            """,
            (topico_id,)
        )

        conexao.commit()

        flash("Tópico excluído com sucesso.", "success")
        referer = request.referrer or ""

        if "/admin/forum" in referer:
            return redirect(url_for("forum.gerenciar_forum"))

        return redirect(url_for("forum.forum_home"))

    except HTTPException:
        raise

    except Exception:
        
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao excluir tópico.")

        flash(
            "Ocorreu um erro ao excluir o tópico.",
            "danger"
        )

        return redirect(
            url_for(
                "forum.forum_topico",
                topico_id=topico_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/forum/<int:topico_id>/mensagem/<int:mensagem_id>/excluir", methods=["POST"])
@limiter.limit("20 per minute")
def excluir_mensagem(topico_id, mensagem_id):

    # Precisa estar logado
    if "usuario_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    tipo_usuario = session.get("tipo_usuario")

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Busca a mensagem e verifica a qual tópico ela pertence
        cursor.execute(
            """
            SELECT
                m.id,
                m.topico_id,
                m.usuario_id,
                m.mensagem
            FROM forum_mensagens m
            WHERE m.id = %s
            AND m.topico_id = %s
            """,
            (mensagem_id, topico_id)
        )

        mensagem = cursor.fetchone()

        if not mensagem:
            abort(404)

        # Verifica se é a mensagem inicial do tópico
        cursor.execute(
            """
            SELECT
                MIN(id) AS mensagem_inicial_id
            FROM forum_mensagens
            WHERE topico_id = %s
            """,
            (topico_id,)
        )

        resultado = cursor.fetchone()

        if resultado and mensagem_id == resultado["mensagem_inicial_id"]:
            flash(
                "A mensagem inicial do tópico não pode ser excluída.",
                "warning"
            )
            return redirect(
                url_for(
                    "forum.forum_topico",
                    topico_id=topico_id
                )
            )

        # Só o autor da mensagem ou administrador pode excluir
        if (
            mensagem["usuario_id"] != usuario_id
            and tipo_usuario != "admin"
        ):
            flash(
                "Você não tem permissão para excluir esta mensagem.",
                "danger"
            )
            return redirect(
                url_for(
                    "forum.forum_topico",
                    topico_id=topico_id
                )
            )

        # Exclui a mensagem
        cursor.execute(
            """
            DELETE FROM forum_mensagens
            WHERE id = %s
            AND topico_id = %s
            """,
            (mensagem_id, topico_id)
        )

        conexao.commit()

        flash("Mensagem excluída.", "success")

        return redirect(
            url_for(
                "forum.forum_topico",
                topico_id=topico_id
            )
        )

    except HTTPException:
        raise

    except Exception:
        
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao excluir mensagem do fórum.")

        flash(
            "Ocorreu um erro ao excluir a mensagem.",
            "danger"
        )

        return redirect(
            url_for(
                "forum.forum_topico",
                topico_id=topico_id
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@bp.route("/admin/forum")
def gerenciar_forum():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session.get("tipo_usuario") != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("dashboard_usuario"))

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Buscar todos os tópicos
        cursor.execute("""
            SELECT
                t.id,
                t.titulo,
                t.usuario_id,
                t.data_criacao
            FROM forum_topicos t
            ORDER BY t.data_criacao DESC
        """)

        forum = cursor.fetchall()

        # Busca as mensagens de todos os tópicos numa única consulta, em vez
        # de uma consulta por tópico (N+1), e agrupa em Python por topico_id
        mensagens_por_topico = {topico["id"]: [] for topico in forum}

        if mensagens_por_topico:
            marcadores = ",".join(["%s"] * len(mensagens_por_topico))
            cursor.execute(f"""
                SELECT
                    m.id,
                    m.topico_id,
                    m.usuario_id,
                    m.mensagem,
                    m.data_criacao,
                    CONCAT(u.nome, ' ', u.sobrenome) AS autor
                FROM forum_mensagens m
                INNER JOIN usuarios u
                    ON u.id = m.usuario_id
                WHERE m.topico_id IN ({marcadores})
                ORDER BY m.data_criacao ASC
            """, list(mensagens_por_topico.keys()))

            for mensagem in cursor.fetchall():
                mensagens_por_topico[mensagem["topico_id"]].append(mensagem)

        for topico in forum:
            topico["mensagens"] = mensagens_por_topico[topico["id"]]

        return render_template(
            "admin_forum.html",
            forum=forum
        )

    except Exception:
        
        current_app.logger.exception("Erro ao carregar gerenciamento do fórum.")

        flash(
            "Ocorreu um erro ao carregar o gerenciamento do fórum.",
            "danger"
        )

        return redirect(url_for("admin.dashboard_admin"))

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
