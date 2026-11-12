import os, json, traceback, mysql.connector, threading, secrets, functools
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, g
from flask_limiter.util import get_remote_address
from validacoes import (
    validar_cpf,
)

from config import (
    OPENAI_API_KEY,
    PROXIES_CONFIAVEIS,
    POLITICA_CSP,
    SESSAO_HORAS,
    TERMOS_VERSAO,
    UPLOAD_FOLDER,
    configurar_app,
)
from extensoes import limiter, csrf, iniciar_extensoes
from db import get_db_connection
from servicos.ia import processar_ia_em_background
from rotas.auth import bp as bp_auth
from servicos.sessao import (
    impressao_senha,
)
from rotas.usuario import bp as bp_usuario
from rotas.admin_profissionais import bp as bp_admin_profissionais
from rotas.admin import bp as bp_admin
from rotas.profissional import bp as bp_profissional
from rotas.forum import bp as bp_forum
from rotas.conta import bp as bp_conta
from servicos.lgpd import (
    LEGAL,
)
from rotas.publico import bp as bp_publico
from servicos.retencao import (
    RETENCAO_CONVERSAS_DIAS,
    RETENCAO_CONVERSAS_VISITANTES_DIAS,
    aplicar_retencao,
)

app = Flask(__name__)
configurar_app(app)
iniciar_extensoes(app)
app.register_blueprint(bp_auth)
app.register_blueprint(bp_usuario)
app.register_blueprint(bp_admin_profissionais)
app.register_blueprint(bp_admin)
app.register_blueprint(bp_profissional)
app.register_blueprint(bp_forum)
app.register_blueprint(bp_conta)
app.register_blueprint(bp_publico)





# Páginas e respostas que, mesmo sem login, carregam dados pessoais ou de saúde
ENDPOINTS_SEM_CACHE = {
    "auth.login", "auth.verificar_2fa", "auth.redefinir_senha", "auth.esqueci_senha", "conta.aceitar_termos", "usuario.cadastro_usuario",
    "profissional.cadastro_profissional", "auth.reenviar_confirmacao", "auth.reenviar_codigo_2fa", "chatbot_historico",
    "mensagens", "lista_sessoes",
}


@app.after_request
def cabecalhos_de_seguranca(resposta):
    """Cabeçalhos que limitam de onde o navegador aceita scripts, estilos e imagens."""

    resposta.headers.setdefault("Content-Security-Policy", POLITICA_CSP)
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resposta.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
    resposta.headers.setdefault("X-Frame-Options", "DENY")

    # Dados pessoais e de saúde não ficam no cache do navegador: o botão "voltar" depois
    # do logout, em computador compartilhado, não pode mostrar a página anterior
    if request.endpoint != "static" and (
        request.endpoint in ENDPOINTS_SEM_CACHE or "usuario_id" in session
    ):
        resposta.headers.setdefault("Cache-Control", "no-store")

    if app.config["SESSION_COOKIE_SECURE"]:
        resposta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")

    return resposta


@app.errorhandler(429)
def limite_excedido(erro):

    mensagem = "Muitas tentativas em pouco tempo. Aguarde um minuto e tente novamente."

    # Rotas chamadas por fetch (ex.: chatbot) esperam JSON
    if request.is_json or request.accept_mimetypes.best == "application/json":
        return {"erro": mensagem}, 429

    return render_template("erro_429.html", mensagem=mensagem), 429


@app.errorhandler(413)
def arquivo_grande_demais(erro):

    limite_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    mensagem = f"O arquivo enviado é grande demais. O limite é de {limite_mb} MB."

    if request.is_json or request.accept_mimetypes.best == "application/json":
        return {"erro": mensagem}, 413

    # O formulário não pode ser lido (o envio foi cortado), então volta para a mesma página
    flash(mensagem, "danger")
    return redirect(request.path)



usuarios = []
profissionais = []




from deteccao_risco import detect_critical, pediu_profissional






def chave_usuario_ou_ip():
    # Limite por conta quando logado, para não depender só do IP
    # (vários usuários podem dividir o mesmo IP, e um usuário pode trocar de IP)
    usuario_id = session.get("usuario_id")

    if usuario_id:
        return f"usuario:{usuario_id}"

    return get_remote_address()


@app.route("/chatbot", methods=["POST"])
@limiter.limit("20 per minute")
@limiter.limit("300 per day")
@limiter.limit("150 per day", key_func=chave_usuario_ou_ip)
def chatbot():

    conexao = None
    cursor = None

    try:

        dados = request.get_json(silent=True)

        if not isinstance(dados, dict):
            return {"erro": "Dados inválidos. Envie uma mensagem válida."}, 400

        mensagem = dados.get("mensagem", "")

        if not isinstance(mensagem, str):
            return {"erro": "A mensagem deve ser um texto válido."}, 400

        mensagem = mensagem.strip()
        
        
        if len(mensagem) > 2000:
            return {
                "erro": "A mensagem é muito longa. Limite de 2000 caracteres."
            }, 400

        if not mensagem:
            return {"erro": "Digite uma mensagem."}, 400

        usuario_id = session.get("usuario_id")

        # Sem consentimento para dados de saúde, a mensagem nem é salva
        if not g.get("consentimento_ok"):
            return {
                "erro": "Para conversar, é preciso aceitar o tratamento dos dados da conversa.",
                "consentimento_necessario": True
            }, 403

        if usuario_id:
            conexao_status = None
            cursor_status = None

            try:
                conexao_status = get_db_connection()
                cursor_status = conexao_status.cursor(dictionary=True)

                cursor_status.execute("""
                    SELECT status
                    FROM usuarios
                    WHERE id = %s
                    LIMIT 1
                """, (usuario_id,))

                usuario_atual = cursor_status.fetchone()

            finally:
                if cursor_status:
                    cursor_status.close()
                if conexao_status:
                    conexao_status.close()

            if not usuario_atual or usuario_atual["status"] != "ativo":
                session.clear()

                return {
                    "erro": "Sua sessão expirou ou sua conta não está ativa. Faça login novamente."
                }, 401
                

        # =========================================================
        # USUÁRIO DESLOGADO
        # =========================================================

        
        if not usuario_id:

            # Se pedir atendimento profissional, precisa fazer login
            if pediu_profissional(mensagem):

                return {
                    "resposta": (
                        "Para conversar com um profissional, "
                        "faça login ou cadastro no site."
                    ),
                    "handoff": False,
                    "login_necessario": True,
                    "exibir_direto": True
                }

            # =====================================================
            # RECUPERA ATENDIMENTO DO USUÁRIO DESLOGADO
            # =====================================================
            
            novo_atendimento = dados.get("novo_atendimento", False)

            if not isinstance(novo_atendimento, bool):
                return {"erro": "Valor inválido para novo atendimento."}, 400

            if novo_atendimento:
                session.pop("chatbot_atendimento_id", None)

            atendimento_id = session.get("chatbot_atendimento_id")
            
            #Descarta um identificador inválido da sessão.
            if atendimento_id is not None:
                if type(atendimento_id) is not int or atendimento_id <= 0:
                    session.pop("chatbot_atendimento_id", None)
                    atendimento_id = None   
            
            #Se não passar na validação, descarta o ID da sessão para que a rota crie um atendimento novo.
            
            if atendimento_id:
                cursor_temp = None
                conexao_temp = None

                try:
                    conexao_temp = get_db_connection()
                    cursor_temp = conexao_temp.cursor()

                    cursor_temp.execute("""
                        SELECT id
                        FROM atendimentos_chatbot
                        WHERE id = %s
                        AND usuario_id IS NULL
                        AND status = 'ia'
                        LIMIT 1
                    """, (atendimento_id,))

                    atendimento_valido = cursor_temp.fetchone()

                    if not atendimento_valido:
                        session.pop("chatbot_atendimento_id", None)
                        atendimento_id = None

                finally:
                    if cursor_temp:
                        cursor_temp.close()
                    if conexao_temp:
                        conexao_temp.close()
            
            

            # Se ainda não existe atendimento, cria um
            if not atendimento_id:

                cursor_temp = None
                conexao_temp = None

                try:

                    conexao_temp = get_db_connection()
                    cursor_temp = conexao_temp.cursor()

                    cursor_temp.execute("""
                        INSERT INTO atendimentos_chatbot
                            (usuario_id, status, motivo)
                        VALUES
                            (NULL, 'ia', %s)
                    """, (
                        "Conversa com o Apoio Virtual",
                    ))

                    atendimento_id = cursor_temp.lastrowid

                    conexao_temp.commit()

                    session["chatbot_atendimento_id"] = atendimento_id

                finally:

                    if cursor_temp:
                        cursor_temp.close()

                    if conexao_temp:
                        conexao_temp.close()

            # =====================================================
            # SALVA MENSAGEM DO USUÁRIO
            # =====================================================

            conexao_temp = None
            cursor_temp = None

            try:

                conexao_temp = get_db_connection()
                cursor_temp = conexao_temp.cursor()

                cursor_temp.execute("""
                    INSERT INTO mensagens_atendimento
                        (atendimento_id, usuario_id, remetente, mensagem)
                    VALUES
                        (%s, NULL, 'usuario', %s)
                """, (
                    atendimento_id,
                    mensagem
                ))

                conexao_temp.commit()

            finally:

                if cursor_temp:
                    cursor_temp.close()

                if conexao_temp:
                    conexao_temp.close()

            # =====================================================
            # DETECÇÃO DE SITUAÇÃO CRÍTICA
            # =====================================================

            if detect_critical(mensagem):

                return {
                    "resposta": (
                        "Estou aqui com você. "
                        "Se você estiver em risco agora, ligue para o CVV no 188 "
                        "(gratuito, 24 horas) ou para o SAMU no 192. "
                        "Se quiser, posso continuar conversando com você."
                    ),
                    "critico": True,
                    "exibir_direto": True,
                    "atendimento_id": atendimento_id
                }

            # =====================================================
            # IA EM BACKGROUND
            # =====================================================

            threading.Thread(
                target=processar_ia_em_background,
                args=(app, atendimento_id),
                daemon=True
            ).start()

            return {
                "resposta": "",
                "critico": False,
                "atendimento_id": atendimento_id,
                "processando": True
            }

        # =========================================================
        # USUÁRIO LOGADO
        # =========================================================

        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)    

        # =========================================================
        # RECUPERA O ATENDIMENTO DA SESSÃO ATUAL
        # =========================================================

        atendimento_id = session.get("chatbot_atendimento_id")

        atendimento = None

        if atendimento_id:

            cursor.execute("""
                SELECT *
                FROM atendimentos_chatbot
                WHERE id = %s
                AND usuario_id = %s
                AND status IN (
                    'ia',
                    'aguardando',
                    'em_atendimento'
                )
                LIMIT 1
            """, (
                atendimento_id,
                usuario_id
            ))

            atendimento = cursor.fetchone()


        # =========================================================
        # CRIA NOVO ATENDIMENTO SE NÃO EXISTIR NA SESSÃO
        # =========================================================

        if not atendimento:

            # Requisições simultâneas (duplo clique, duas abas) sem conversa na sessão criariam
            # uma conversa cada, e as respostas da IA ficariam em conversas que a tela não acompanha.
            # A trava por usuário faz uma esperar a outra terminar, e quem chega depois aproveita
            # a conversa recém-criada. A trava é liberada quando a conexão fecha.
            cursor.execute("SELECT GET_LOCK(%s, 5) AS obteve", (f"chat_novo_{usuario_id}",))
            cursor.fetchone()

            cursor.execute("""
                SELECT *
                FROM atendimentos_chatbot
                WHERE usuario_id = %s
                  AND status = 'ia'
                  AND data_inicio > DATE_SUB(NOW(), INTERVAL 10 SECOND)
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
            """, (usuario_id,))

            atendimento = cursor.fetchone()

            if atendimento:
                atendimento_id = atendimento["id"]

            else:
                cursor.execute("""
                    INSERT INTO atendimentos_chatbot
                        (usuario_id, status, motivo)
                    VALUES
                        (%s, 'ia', %s)
                """, (
                    usuario_id,
                    "Conversa com o Apoio Virtual"
                ))

                atendimento_id = cursor.lastrowid

            session["chatbot_atendimento_id"] = atendimento_id

        # =========================================================
        # SALVA MENSAGEM DO USUÁRIO
        # =========================================================

        cursor.execute("""
            INSERT INTO mensagens_atendimento
                (atendimento_id, usuario_id, remetente, mensagem)
            VALUES
                (%s, %s, 'usuario', %s)
        """, (
            atendimento_id,
            usuario_id,
            mensagem
        ))

        # =========================================================
        # PROFISSIONAL JÁ ESTÁ ATENDENDO
        # =========================================================

        if atendimento and atendimento["status"] == "em_atendimento":

            conexao.commit()

            return {
                "resposta": "",
                "handoff": True,
                "profissional_atendendo": True,
                "atendimento_id": atendimento_id
            }

        # =========================================================
        # JÁ ESTÁ AGUARDANDO PROFISSIONAL
        # =========================================================

        if atendimento and atendimento["status"] == "aguardando":

            conexao.commit()

            return {
                "resposta": (
                    "Sua solicitação de atendimento já está registrada. "
                    "Aguarde um profissional assumir a conversa."
                ),
                "handoff": True,
                "exibir_direto": True,
                "atendimento_id": atendimento_id
            }

        # =========================================================
        # DETECÇÃO DE SITUAÇÃO CRÍTICA / PEDIDO DE PROFISSIONAL
        # =========================================================

        mensagem_critica = detect_critical(mensagem)
        pedido_profissional = pediu_profissional(mensagem)

        if mensagem_critica or pedido_profissional:

            if mensagem_critica:

                motivo = (
                    "Situação crítica detectada pelo Apoio Virtual"
                )

                resposta_handoff = (
                    "Estou aqui com você. "
                    "Percebi que você está passando por uma situação difícil "
                    "e solicitei atendimento de um profissional. "
                    "Fique por aqui, alguém poderá continuar essa conversa com você. "
                    "Se você estiver em risco agora, ligue para o CVV no 188 "
                    "(gratuito, 24 horas) ou para o SAMU no 192."
                )

            else:

                motivo = (
                    "Usuário solicitou atendimento profissional"
                )

                resposta_handoff = (
                    "Claro. Sua solicitação foi registrada. "
                    "Um profissional poderá continuar essa conversa com você."
                )

            cursor.execute("""
                UPDATE atendimentos_chatbot
                SET
                    status = 'aguardando',
                    motivo = %s
                WHERE id = %s
                AND usuario_id = %s
                AND status = 'ia'
            """, (
                motivo,
                atendimento_id,
                usuario_id
            ))

            if cursor.rowcount == 0:
                # Entre o status lido no início da requisição e este UPDATE,
                # um profissional assumiu ou encerrou o atendimento (ou a IA
                # em segundo plano já tinha respondido). Não sobrescreve.
                conexao.rollback()

                return {
                    "resposta": "",
                    "handoff": True,
                    "profissional_atendendo": True,
                    "atendimento_id": atendimento_id
                }

            cursor.execute("""
                INSERT INTO mensagens_atendimento
                    (atendimento_id, usuario_id, remetente, mensagem)
                VALUES
                    (%s, %s, 'bot', %s)
            """, (
                atendimento_id,
                usuario_id,
                resposta_handoff
            ))

            conexao.commit()

            return {
                "resposta": resposta_handoff,
                "handoff": True,
                "critico": mensagem_critica,
                "atendimento_id": atendimento_id
            }

        # =========================================================
        # RESPOSTA NORMAL DA IA
        # =========================================================

        conexao.commit()

        threading.Thread(
            target=processar_ia_em_background,
            args=(app, atendimento_id),
            daemon=True
        ).start()

        return {
            "resposta": "",
            "critico": False,
            "atendimento_id": atendimento_id,
            "processando": True
        }

    except Exception:
        if conexao:
            conexao.rollback()

        app.logger.exception("Erro no chatbot.")

        return {
            "erro": (
                "Não foi possível responder agora. "
                "Tente novamente em alguns instantes."
            )
        }, 500

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@app.route("/chatbot/voltar_para_ia", methods=["POST"])
@limiter.limit("10 per minute")
def voltar_para_ia():
    """Permite ao usuário encerrar um atendimento profissional pendente ou em andamento."""

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return {"erro": "Faça login novamente."}, 401

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute("""
            UPDATE atendimentos_chatbot
            SET status = 'finalizado'
            WHERE usuario_id = %s
              AND status IN ('aguardando', 'em_atendimento')
        """, (usuario_id,))

        conexao.commit()

        return {"sucesso": True}

    except Exception:
        if conexao:
            conexao.rollback()

        app.logger.exception("Erro ao encerrar atendimento pelo usuário.")

        return {"erro": "Não foi possível encerrar o atendimento."}, 500

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@app.route("/chatbot/historico")
def chatbot_historico():

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return {"mensagens": []}

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                m.remetente,
                m.mensagem
            FROM mensagens_atendimento m
            INNER JOIN atendimentos_chatbot a
                ON m.atendimento_id = a.id
            INNER JOIN usuarios u
                ON u.id = a.usuario_id
            WHERE a.usuario_id = %s
              AND u.status = 'ativo'
            ORDER BY m.id DESC
            LIMIT 200
        """, (usuario_id,))

        mensagens = list(reversed(cursor.fetchall()))

        return {
            "mensagens": mensagens
        }

    except Exception:
        app.logger.exception("Erro ao buscar histórico do chatbot.")

        return {"mensagens": []}

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
      
        
@app.route("/profissional/atendimentos")
def profissional_atendimentos():

    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("tipo_usuario") != "profissional":
        abort(403)

    usuario_id = session["usuario_id"]

    try:
        conexao = get_db_connection()

        cursor = conexao.cursor(dictionary=True)

        # Descobre o ID do profissional logado
        cursor.execute("""
            SELECT id
            FROM profissionais
            WHERE usuario_id = %s
              AND status_aprovacao = 'aprovado'
            LIMIT 1
        """, (usuario_id,))

        profissional = cursor.fetchone()

        if not profissional:
            cursor.close()
            conexao.close()
            abort(403)

        # Busca atendimentos aguardando profissional
        cursor.execute("""
            SELECT
                a.id,
                a.usuario_id,
                a.status,
                a.motivo,
                a.data_inicio,
                u.nome,
                u.sobrenome
            FROM atendimentos_chatbot a
            INNER JOIN usuarios u
                ON u.id = a.usuario_id
            WHERE a.status = 'aguardando'
              AND u.status = 'ativo'
            ORDER BY a.data_inicio ASC
        """)

        atendimentos = cursor.fetchall()

        cursor.close()
        conexao.close()

        return render_template(
            "profissional_atendimentos.html",
            atendimentos=atendimentos
        )

    except Exception:
        app.logger.exception("Erro ao buscar atendimentos.")
        flash("Não foi possível carregar os atendimentos.", "danger")
        return redirect(url_for("profissional.dashboard_profissional"))
    

@app.route("/assumir_atendimento/<int:atendimento_id>", methods=["POST"])
def assumir_atendimento(atendimento_id):

    if "usuario_id" not in session:
        return {"erro": "Usuário não identificado."}, 401

    if session.get("tipo_usuario") != "profissional":
        return {"erro": "Acesso negado."}, 403

    usuario_id = session["usuario_id"]

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Descobre o profissional logado
        cursor.execute("""
            SELECT id
            FROM profissionais
            WHERE usuario_id = %s
              AND status_aprovacao = 'aprovado'
            LIMIT 1
        """, (usuario_id,))

        profissional = cursor.fetchone()

        if not profissional:
            return {"erro": "Profissional não autorizado."}, 403

        profissional_id = profissional["id"]

        # Verifica o estado atual do atendimento
        cursor.execute("""
            SELECT
                id,
                profissional_id,
                status
            FROM atendimentos_chatbot
            WHERE id = %s
            LIMIT 1
        """, (atendimento_id,))

        atendimento = cursor.fetchone()

        if not atendimento:
            return {"erro": "Atendimento não encontrado."}, 404

        # Já está sendo atendido pelo próprio profissional
        if (
            atendimento["status"] == "em_atendimento"
            and atendimento["profissional_id"] == profissional_id
        ):
            return {
                "sucesso": True,
                "atendimento_id": atendimento_id,
                "ja_assumido": True
            }

        # Já está sendo atendido por outro profissional
        if atendimento["status"] == "em_atendimento":
            return {
                "erro": "Este atendimento já está sendo realizado por outro profissional."
            }, 409

        # Só pode assumir atendimentos aguardando
        if atendimento["status"] != "aguardando":
            return {
                "erro": "Este atendimento não está disponível."
            }, 409

        # Assume o atendimento
        cursor.execute("""
            UPDATE atendimentos_chatbot
            SET profissional_id = %s,
                status = 'em_atendimento'
            WHERE id = %s
              AND status = 'aguardando'
              AND profissional_id IS NULL
        """, (profissional_id, atendimento_id))

        if cursor.rowcount == 0:
            conexao.rollback()

            # Outra requisição acabou de assumir. Se foi este mesmo profissional (duplo clique,
            # duas abas), é sucesso e não conflito
            cursor.execute("""
                SELECT status, profissional_id
                FROM atendimentos_chatbot
                WHERE id = %s
            """, (atendimento_id,))

            atual = cursor.fetchone()

            if (
                atual
                and atual["status"] == "em_atendimento"
                and atual["profissional_id"] == profissional_id
            ):
                return {
                    "sucesso": True,
                    "atendimento_id": atendimento_id,
                    "ja_assumido": True
                }

            return {
                "erro": "Este atendimento já foi assumido por outro profissional."
            }, 409

        conexao.commit()

        return {
            "sucesso": True,
            "atendimento_id": atendimento_id,
            "ja_assumido": False
        }

    except Exception:
        if conexao:
            conexao.rollback()

        app.logger.exception("Erro ao assumir atendimento.")

        return {
            "erro": "Não foi possível assumir o atendimento."
        }, 500

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
            
@app.route("/encerrar/<int:atendimento_id>", methods=["POST"])
def encerrar_atendimento(atendimento_id):

    if "usuario_id" not in session:
        return {"erro": "Usuário não identificado."}, 401

    if session.get("tipo_usuario") != "profissional":
        return {"erro": "Acesso negado."}, 403

    usuario_id = session["usuario_id"]

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT id
            FROM profissionais
            WHERE usuario_id = %s
              AND status_aprovacao = 'aprovado'
            LIMIT 1
        """, (usuario_id,))

        profissional = cursor.fetchone()

        if not profissional:
            return {"erro": "Profissional não autorizado."}, 403

        profissional_id = profissional["id"]

        cursor.execute("""
            UPDATE atendimentos_chatbot
            SET status = 'finalizado'
            WHERE id = %s
              AND profissional_id = %s
              AND status = 'em_atendimento'
        """, (
            atendimento_id,
            profissional_id
        ))

        if cursor.rowcount == 0:
            conexao.rollback()
            return {
                "erro": "Atendimento não encontrado ou já encerrado."
            }, 404

        conexao.commit()

        return {
            "sucesso": True
        }

    except Exception:
        if conexao:
            conexao.rollback()

        app.logger.exception("Erro ao encerrar atendimento.")

        return {
            "erro": "Não foi possível encerrar o atendimento."
        }, 500

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


@app.route("/mensagens/<int:atendimento_id>")
@limiter.limit("120 per minute")
def mensagens(atendimento_id):

    usuario_id = session.get("usuario_id")

    # Só devolve mensagens mais novas que esta, para o polling não repetir o histórico
    depois = request.args.get("depois", default=0, type=int) or 0

    # Usuário deslogado
    if not usuario_id:

        atendimento_sessao = session.get("chatbot_atendimento_id")

        if atendimento_sessao != atendimento_id:
            return {"erro": "Acesso negado."}, 403

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        if usuario_id:

            cursor.execute("""
                SELECT
                    a.id,
                    a.status
                FROM atendimentos_chatbot a
                WHERE a.id = %s
                AND a.usuario_id = %s
                LIMIT 1
            """, (atendimento_id, usuario_id))

            atendimento = cursor.fetchone()

        else:

            cursor.execute("""
                SELECT
                    a.id,
                    a.status
                FROM atendimentos_chatbot a
                WHERE a.id = %s
                AND a.usuario_id IS NULL
                LIMIT 1
            """, (atendimento_id,))

            atendimento = cursor.fetchone()

        if not atendimento:

            cursor.execute("""
                SELECT
                    a.id,
                    a.status
                FROM atendimentos_chatbot a
                INNER JOIN profissionais p
                    ON p.id = a.profissional_id
                WHERE a.id = %s
                  AND p.usuario_id = %s
                LIMIT 1
            """, (atendimento_id, usuario_id))

            atendimento = cursor.fetchone()

        if not atendimento:
            return {"erro": "Acesso negado."}, 403

        cursor.execute("""
            SELECT
                id,
                remetente,
                mensagem,
                data_envio
            FROM mensagens_atendimento
            WHERE atendimento_id = %s
              AND id > %s
            ORDER BY id ASC
        """, (atendimento_id, depois))

        mensagens_db = cursor.fetchall()

        resultado = []

        for mensagem in mensagens_db:

            if mensagem["remetente"] == "profissional":
                sender = "human"

            elif mensagem["remetente"] == "usuario":
                sender = "user"

            else:
                sender = "bot"

            resultado.append({
                "id": mensagem["id"],
                "sender": sender,
                "text": mensagem["mensagem"]
            })

        return {
            "status": atendimento["status"],
            "mensagens": resultado
        }

    except Exception:
        
        app.logger.exception("Erro ao buscar mensagens.")

        return [], 500

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
            

    
    

            
            
@app.route("/enviar_profissional/<int:atendimento_id>", methods=["POST"])
@limiter.limit("30 per minute")
def enviar_profissional(atendimento_id):

    if "usuario_id" not in session:
        return {"erro": "Usuário não identificado."}, 401

    if session.get("tipo_usuario") != "profissional":
        return {"erro": "Acesso negado."}, 403

    usuario_id = session["usuario_id"]

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return {"erro": "Nenhum dado recebido."}, 400

    mensagem = dados.get("message", "")

    if not isinstance(mensagem, str):
        return {"erro": "A mensagem deve ser um texto válido."}, 400

    mensagem = mensagem.strip()

    if not mensagem:
        return {"erro": "Digite uma mensagem."}, 400

    if len(mensagem) > 2000:
        return {
            "erro": "A mensagem é muito longa. Limite de 2000 caracteres."
        }, 400

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Descobre o profissional logado
        cursor.execute("""
            SELECT id
            FROM profissionais
            WHERE usuario_id = %s
              AND status_aprovacao = 'aprovado'
            LIMIT 1
        """, (usuario_id,))

        profissional = cursor.fetchone()

        if not profissional:
            return {"erro": "Profissional não autorizado."}, 403

        profissional_id = profissional["id"]

        # Verifica se o atendimento pertence a este profissional
        cursor.execute("""
            SELECT id
            FROM atendimentos_chatbot
            WHERE id = %s
              AND profissional_id = %s
              AND status = 'em_atendimento'
            LIMIT 1
        """, (atendimento_id, profissional_id))

        atendimento = cursor.fetchone()

        if not atendimento:
            return {
                "erro": "Este atendimento não está mais disponível."
            }, 403

        # Salva a mensagem. A condição vai dentro do próprio INSERT: entre a checagem acima e a
        # gravação, o atendimento pode ter sido encerrado (por quem escreve ou pelo usuário)
        cursor.execute("""
            INSERT INTO mensagens_atendimento
                (atendimento_id, usuario_id, remetente, mensagem)
            SELECT a.id, %s, 'profissional', %s
            FROM atendimentos_chatbot a
            WHERE a.id = %s
              AND a.profissional_id = %s
              AND a.status = 'em_atendimento'
        """, (
            usuario_id,
            mensagem,
            atendimento_id,
            profissional_id
        ))

        if cursor.rowcount == 0:
            conexao.rollback()
            return {
                "erro": "Este atendimento não está mais disponível."
            }, 403

        conexao.commit()

        return {
            "sucesso": True
        }

    except Exception:
        
        if conexao:
            conexao.rollback()

        app.logger.exception("Erro ao enviar mensagem do profissional.")

        return {
            "erro": "Não foi possível enviar a mensagem."
        }, 500

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
            
            

            
            

            
            




@app.route("/lista_sessoes")
def lista_sessoes():

    if "usuario_id" not in session:
        return {
            "aguardando": [],
            "meus_atendimentos": []
        }, 401

    if session.get("tipo_usuario") != "profissional":
        return {
            "aguardando": [],
            "meus_atendimentos": []
        }, 403

    usuario_id = session["usuario_id"]

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT id
            FROM profissionais
            WHERE usuario_id = %s
              AND status_aprovacao = 'aprovado'
            LIMIT 1
        """, (usuario_id,))

        profissional = cursor.fetchone()

        if not profissional:
            return {
                "aguardando": [],
                "meus_atendimentos": []
            }, 403

        profissional_id = profissional["id"]

        cursor.execute("""
            SELECT a.id
            FROM atendimentos_chatbot a
            INNER JOIN usuarios u
                ON u.id = a.usuario_id
            WHERE a.status = 'aguardando'
              AND u.status = 'ativo'
            ORDER BY a.data_inicio ASC
        """)

        aguardando = cursor.fetchall()

        cursor.execute("""
            SELECT id
            FROM atendimentos_chatbot
            WHERE status = 'em_atendimento'
              AND profissional_id = %s
            ORDER BY data_inicio ASC
        """, (profissional_id,))

        meus_atendimentos = cursor.fetchall()

        return {
            "aguardando": [a["id"] for a in aguardando],
            "meus_atendimentos": [a["id"] for a in meus_atendimentos]
        }

    except Exception:
        
        app.logger.exception("Erro ao listar atendimentos.")

        return {
            "aguardando": [],
            "meus_atendimentos": []
        }, 500

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()





            
            
            
            
            

            
            
# =========================
# BANIR USUÁRIO
# =========================



# =========================
# DESBANIR USUÁRIO
# =========================

            
            





       
            

            
# =========================
# CADASTRO_USUÁRIO
# =========================










    






            
            
     

        


# Rotas que não exigem o aceite da versão atual dos Termos.
# O chat e suas consultas têm a própria checagem de consentimento.
ENDPOINTS_SEM_ACEITE = {
    "static", "conta.aceitar_termos", "auth.logout", "conta.termos_de_uso", "conta.politica_privacidade",
    "conta.politica_cookies", "chatbot", "chatbot_historico", "voltar_para_ia",
    "conta.registrar_consentimento_chat", "mensagens",
}


@app.before_request
def verificar_conta_e_consentimento():
    """Encerra a sessão de quem foi banido e exige o aceite da versão atual dos Termos."""

    # Visitante sem cadastro: o consentimento fica na sessão
    g.consentimento_ok = session.get("consentimento_chat") == TERMOS_VERSAO

    if "usuario_id" not in session or request.endpoint in (None, "static"):
        return None

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT status, senha_hash, termos_versao, consentimento_saude_versao
                FROM usuarios
                WHERE id = %s
                """,
                (session["usuario_id"],)
            )
        except mysql.connector.errors.ProgrammingError:
            # Colunas novas ainda não criadas: rode migrar_lgpd.py
            app.logger.error("Colunas de consentimento ausentes na tabela usuarios. Rode migrar_lgpd.py.")

            cursor.execute(
                "SELECT status, senha_hash FROM usuarios WHERE id = %s",
                (session["usuario_id"],)
            )

        usuario = cursor.fetchone()

    except Exception:
        app.logger.exception("Erro ao verificar status do usuário.")
        # Nunca libera acesso quando não dá para confirmar o status da
        # conta (ex.: falha transitória no banco): um banimento não pode
        # passar despercebido só porque o banco falhou nesse instante.
        abort(503)

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

    if not usuario or usuario["status"] == "banido":
        session.clear()
        flash("Sua conta não está mais ativa.", "danger")
        return redirect(url_for("auth.login"))

    # Sessão aberta antes da troca de senha (ou criada sem a impressão da senha) não vale mais
    if not secrets.compare_digest(
        str(session.get("senha_v", "")),
        impressao_senha(usuario["senha_hash"])
    ):
        session.clear()
        flash("Sua sessão expirou. Faça login novamente.", "warning")
        return redirect(url_for("auth.login"))

    g.consentimento_ok = usuario.get("consentimento_saude_versao") == TERMOS_VERSAO

    if request.endpoint in ENDPOINTS_SEM_ACEITE or "termos_versao" not in usuario:
        return None

    if usuario["termos_versao"] != TERMOS_VERSAO:
        proximo = request.path if request.method == "GET" else None

        return redirect(url_for("conta.aceitar_termos", proximo=proximo))

    return None


            
            

    


    















        


# Página principal do fórum








            
            
            
            


            
            
                        








        
    


                


@functools.lru_cache(maxsize=512)
def _versao_arquivo_estatico(filename):
    # Lê a data de modificação uma única vez por arquivo (cache em memória);
    # os arquivos estáticos não mudam enquanto o processo está no ar.
    try:
        caminho = os.path.join(app.static_folder, filename)
        return int(os.path.getmtime(caminho))
    except (OSError, TypeError, ValueError):
        return None


@app.url_defaults
def versionar_arquivos_estaticos(endpoint, values):
    # Acrescenta ?v=<data de modificação> nos CSS/JS, para o navegador
    # baixar de novo sempre que o arquivo mudar em vez de usar o cache antigo
    if endpoint == "static" and values.get("filename") and "v" not in values:
        versao = _versao_arquivo_estatico(values["filename"])
        if versao is not None:
            values["v"] = versao


@app.context_processor
def injetar_dados_legais():
    return {
        "legal": LEGAL,
        "termos_versao": TERMOS_VERSAO,
        "consentimento_chat_ok": bool(g.get("consentimento_ok")),
        "retencao_conversas_dias": RETENCAO_CONVERSAS_DIAS,
        "retencao_visitantes_dias": RETENCAO_CONVERSAS_VISITANTES_DIAS,
    }


# =========================
# CONSENTIMENTO
# =========================


# =========================
# RETENÇÃO DE DADOS
# =========================


@app.cli.command("aplicar-retencao")
def comando_aplicar_retencao():
    """Rotina de retenção. Agende para rodar uma vez por dia."""

    for nome, quantidade in aplicar_retencao().items():
        print(f"{nome}: {quantidade}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
    

