import secrets, re, json, os, traceback
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
MODERADOR = True
app.secret_key = secrets.token_hex(16)
usuarios = []
profissional = []


# app.config['SERVER_NAME'] = '192.168.1.11:5000'
app.config['PREFERRED_URL_SCHEME'] = 'http'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# CONTA GMAIL REMETENTE
app.config['MAIL_USERNAME'] = 'gabrielgaburi6@gmail.com'

# SENHA DE APP DO GMAIL (via terminal)
app.config['MAIL_PASSWORD'] = "dans hivz zvpt xswd"

# REMETENTE PRECISA SER O MESMO GMAIL
app.config['MAIL_DEFAULT_SENDER'] = 'gabrielgaburi6@gmail.com'

app.config['MAIL_SUPPRESS_SEND'] = False

mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)
noticias = [
    {
        "id": 1,
        "titulo": "Vício em apostas online atinge milhões no Brasil e já é considerado problema de saúde pública",
        "resumo": "Número de apostadores com comportamento de risco cresce e preocupa especialistas. Perdas financeiras e impactos emocionais afetam famílias e sociedade.",
        "introducao": "Casos de jogo compulsivo como o dele vêm se tornando cada vez mais comuns no Brasil. O Levantamento Nacional de Álcool e Drogas (LENAD III), com dados de 2023, aponta que cerca de 10,8 milhões de pessoas a partir de 14 anos jogam de forma arriscada ou problemática. Segundo especialistas, o vício em jogos virtuais, as chamadas “bets”, que podem ou não ser esportivas, já é considerado problema de saúde pública e tem Classificação Internacional de Doenças (CID): Transtorno do Jogo.",
        "fonte": "https://g1.globo.com/ce/ceara/noticia/2025/12/17/vicio-em-apostas-online-atinge-milhoes-no-brasil-e-ja-e-considerado-problema-de-saude-publica.ghtml",
        "imagem": "https://s2-g1.glbimg.com/eJu2gcoIP1mcZbf1yQbBc8zjbBk=/0x0:1920x1080/984x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2023/B/j/8jYBXsTD2iSC0kW5mYIw/apostas-esportivas-foto-joedson-alves-abr-agencia-brasil.jpg"
    },
    {
        "id": 2,
        "titulo": "As estratégias de brasileiros contra o vício em apostas: 'Perdi R$ 53 mil e hoje meu pai controla todo meu dinheiro'",
        "resumo": "Quase 11 milhões de brasileiros estão em risco de saúde mental e financeira devido a apostas, segundo levantamento da Universidade Federal de São Paulo.",
        "introducao": "Em 2023, cerca de 28 milhões de brasileiros de 14 anos ou mais (ou 17,6% da população nesta faixa de idade) diziam ter apostado no ano anterior, segundo estudo publicado pela Universidade Federal de São Paulo (Unifesp), em parceria com o Ministério da Justiça e Segurança Pública, em abril deste ano.",
        "fonte": "https://www.bbc.com/portuguese/articles/ckgzk0g8317o",
        "imagem": "https://ichef.bbci.co.uk/ace/ws/800/cpsprodpb/c3cd/live/45471ec0-98a5-11f0-b37c-21373da9ac07.jpg.webp"
    },
    {
        "id": 3,
        "titulo": "Tributação das Bets no Brasil: regras, desafios e as Bets regulamentadas",
        "resumo": "NO texto trata da regulamentação das apostas online no Brasil, estabelecida pela Lei nº 14.790/2023, que define regras de funcionamento e tributação para empresas e apostadores. O objetivo é aumentar a arrecadação, garantir segurança jurídica e tornar o mercado mais transparente.",
        "introducao": "O mercado de apostas online, também conhecido como “bets”, está em pleno crescimento no Brasil. Estima-se que o país já seja o terceiro maior mercado de apostas do mundo, movimentando só em 2024 cerca de R$ 130 bilhões. Com isso, a regulamentação e a tributação desse setor tornaram-se prioridades para o governo. A aprovação da Lei nº 14.790/2023 trouxe mudanças importantes para a operação e fiscalização das bets, estabelecendo regras fiscais e regulamentares que as empresas devem seguir para atuar de forma legal no país.",
        "fonte": "https://www.taxgroup.com.br/intelligence/tributacao-das-bets-no-brasil-regras-desafios-e-as-bets-regulamentadas/",
        "imagem": "https://www.gov.br/secom/pt-br/fatos/brasil-contra-fake/noticias/2024/09/regulamentacao-da-legislacao-de-bets-torna-atividade-mais-segura-no-brasil/mg_8621.jpg/@@images/eb802195-03da-4422-a5ee-1b826d57aa5d.jpeg"
    },
    {   
         "id": 4,
        "titulo": "Entretenimento ou armadilha? Como apostas online e jogo do tigrinho afetam a vida dos 60+",
        "resumo": "Gasto mensal do público idoso com jogos digitais é 30 vezes maior em comparação aos mais jovens, segundo dados do Banco Central.",
        "introducao": "O avanço acelerado das apostas online no Brasil tem produzido um efeito colateral cada vez mais evidente à população idosa: o comprometimento severo da renda com plataformas de apostas esportivas e jogos de cassino online, popularmente associados a termos como bets e tigrinho (os caça-níqueis online).",
        "fonte": "https://gauchazh.clicrbs.com.br/comportamento/60-mais/noticia/2026/01/tigrinho-apostas-online-e-60-quando-o-entretenimento-vira-problema-financeiro-e-social-cmk7brmmn025j014i4w3lbxs2.html",
        "imagem": "https://www.rbsdirect.com.br/filestore/9/2/3/9/0/6/5_f411465a2662a86/5609329_74835350f8ddcb8.jpg?format=webp&w=700"
    }
]

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()  # remove todos os dados da sessão
    flash("Você saiu da sua conta com sucesso.", "success")
    return redirect(url_for("login"))


# =========================
# PERFIL
# =========================
@app.route("/perfil")
def perfil():
    # se não estiver logado
    if "usuario_id" not in session:
        flash("Faça login para acessar seu perfil.", "warning")
        return redirect(url_for("login"))

    # procura usuário na lista
    usuario = next(
        (u for u in usuarios if u["id"] == session["usuario_id"]),
        None
    )

    # segurança extra
    if not usuario:
        session.clear()
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("login"))

    # renderiza página de perfil
    return render_template(
        "perfil.html",
        usuario=usuario
    )
# Arquivo JSON para salvar o fórum
FORUM_FILE = "forum.json"
# =========================
# CADASTRO_USUÁRIO 
# =========================
@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():

    # dicionário com TODOS os campos para manter o formulário preenchido
    dados = {
        "tipo": "usuario",
        "nome": "",
        "sobrenome": "",
        "email": "",
        "telefone": "",
        "cep": "",
        "UF": "",
        "rua": "",
        "numero": "",
        "bairro": "",
        "cidade": "",
        "estado": ""
    }

    if request.method == 'POST':

        # captura TODOS os campos
        dados = {
            "tipo": request.form.get("tipo", "usuario"),
            "nome": request.form.get("nome", "").strip(),
            "sobrenome": request.form.get("sobrenome", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "telefone": request.form.get("telefone", "").strip(),
            "cep": request.form.get("cep", "").strip(),
            "rua": request.form.get("rua", "").strip(),
            "numero": request.form.get("numero", "").strip(),
            "bairro": request.form.get("bairro", "").strip(),
            "cidade": request.form.get("cidade", "").strip(),
            "estado": request.form.get("estado", "").strip()
        }

        senha = request.form.get('senha', '')
        
        confirmar_senha = request.form.get("confirmar_senha", "")

        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "danger")
            return render_template(
            "cadastro_usuario.html",
            dados=dados
        )

        # Só continua se as senhas forem iguais
        senha_hash = generate_password_hash(senha)

        # CAMPOS OBRIGATÓRIOS
        if not dados["nome"] or not dados["email"] or not senha:
            flash("Preencha todos os campos obrigatórios.", "danger")

            return render_template(
                "cadastro_usuario.html",
                dados=dados
            )

        # SENHA INVÁLIDA
        if not senha_valida(senha):
            flash(
                "A senha deve ter 8-16 caracteres, incluindo maiúscula, número e caractere especial.",
                "danger"
            )

            # devolve TODOS os campos preenchidos
            return render_template(
                "cadastro_usuario.html",
                dados=dados
            )

        # EMAIL JÁ CADASTRADO
        usuario_existente = next(
            (u for u in usuarios if u["email"].lower() == dados["email"]),
            None
        )

        if usuario_existente:
            flash("Este email já está cadastrado.", "warning")

            return render_template(
                "cadastro_usuario.html",
                dados=dados
            )

        # SENHA HASH
        senha_hash = generate_password_hash(senha)

        # NOVO USUÁRIO
        novo_usuario = {
            "id": len(usuarios) + 1,
            "nome": dados["nome"],
            "sobrenome": dados["sobrenome"],
            "email": dados["email"],
            "telefone": dados["telefone"],
            "cep": dados["cep"],
            "rua": dados["rua"],
            "numero": dados ["numero"],
            "bairro": dados ["bairro"],
            "cidade": dados["cidade"],
            "estado": dados["estado"],
            "senha": senha_hash,
            "email_confirmado": False,
            "tipo": dados["tipo"]
        }

        usuarios.append(novo_usuario)

        # EMAIL
        if enviar_email_confirmacao(dados["email"]):
            flash(
                "Conta criada! Verifique seu email para confirmar o cadastro.",
                "success"
            )
        else:
            flash(
                "Conta criada, mas houve erro ao enviar o email de confirmação.",
                "warning"
            )

        return redirect(url_for('login'))

    # GET
    return render_template(
        'cadastro_usuario.html',
        dados=dados
    )
    
@app.route('/confirmar_email/<token>')
def confirmar_email(token):

    try:
        email = serializer.loads(
            token,
            salt='confirmacao-email',
            max_age=3600  # 1 hora
        )

    except Exception:
        flash("Link inválido ou expirado.", "danger")
        return redirect(url_for("login"))

    # Procura primeiro entre os usuários
    cadastro = next(
        (u for u in usuarios if u["email"].lower() == email.lower()),
        None
    )

    # Se não encontrou, procura entre os profissionais
    if cadastro is None:
        cadastro = next(
            (p for p in profissional if p["email"].lower() == email.lower()),
            None
        )

    # Não encontrou em nenhuma lista
    if cadastro is None:
        flash("Cadastro não encontrado.", "danger")
        return redirect(url_for("login"))

    # Já confirmou anteriormente
    if cadastro["email_confirmado"]:
        flash("E-mail já confirmado. Faça login.", "info")
        return redirect(url_for("login"))

    # Confirma o cadastro
    cadastro["email_confirmado"] = True

    flash("E-mail confirmado com sucesso! Agora você pode fazer login.", "success")
    return redirect(url_for("login"))
# Funções auxiliares
def carregar_forum():
    try:
        with open(FORUM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def salvar_forum(forum):
    with open(FORUM_FILE, "w", encoding="utf-8") as f:
        json.dump(forum, f, ensure_ascii=False, indent=4)
        
def senha_valida(senha):
    if len(senha) < 8 or len(senha) > 16:
        return False
    
    if not re.search(r"[A-Z]", senha):  # letra maiúscula
        return False
    
    if not re.search(r"[0-9]", senha):  # número
        return False
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):  # especial
        return False

    return True

# Carregar tópicos existentes
forum = carregar_forum()


# Usuário atual e flag de moderador (apenas para exemplo, normalmente viria do login)
usuario_atual = "Anônimo"
moderador = True  # Defina como True apenas para você, o moderador

@app.route('/cadastro_profissional', methods=['GET', 'POST'])
def cadastro_profissional():

    # dicionário com TODOS os campos para manter o formulário preenchido
    dados = {
    "tipo": "profissional",
    "nome": "",
    "sobrenome": "",
    "email": "",
    "telefone": "",
    "cep": "",
    "rua": "",
    "numero": "",
    "bairro": "",
    "cidade": "",
    "estado": "",

    "crp": "",
    "uf_crp": "",
    "experiencia": "",
    "especialidade": "",
    "faculdade": "",
    "pos": "",
    "online": False,
    "presencial": False,
    "biografia": ""
}

    if request.method == 'POST':

        # captura TODOS os campos
        dados = {
            "tipo": request.form.get("tipo", "profissional"),
            "nome": request.form.get("nome", "").strip(),
            "sobrenome": request.form.get("sobrenome", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "telefone": request.form.get("telefone", "").strip(),
            "cep": request.form.get("cep", "").strip(),
            "rua": request.form.get("rua", "").strip(),
            "numero": request.form.get("numero", "").strip(),
            "bairro": request.form.get("bairro", "").strip(),
            "cidade": request.form.get("cidade", "").strip(),
            "estado": request.form.get("estado", "").strip(),
            "crp": request.form.get("crp", "").strip(),
            "uf_crp": request.form.get("uf_crp", "").strip(),
            "experiencia": request.form.get("experiencia", "").strip(),
            "especialidade": request.form.get("especialidade", "").strip(),
            "faculdade": request.form.get("faculdade", "").strip(),
            "pos": request.form.get("pos", "").strip(),
            "online": request.form.get("online") == "1",
            "presencial": request.form.get("presencial") == "1",
            "biografia": request.form.get("biografia", "").strip(),
            "email_confirmado": False
        }

        senha = request.form.get('senha', '')
        
        confirmar_senha = request.form.get("confirmar_senha", "")

        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "danger")
            return render_template(
            "cadastro_profissional.html",
            dados=dados
        )

        # Só continua se as senhas forem iguais
        senha_hash = generate_password_hash(senha)

        # CAMPOS OBRIGATÓRIOS
        if not dados["nome"] or not dados["email"] or not senha:
            flash("Preencha todos os campos obrigatórios.", "danger")

            return render_template(
                'cadastro_profissional.html',
                dados=dados
            )

        # SENHA INVÁLIDA
        if not senha_valida(senha):
            flash(
                "A senha deve ter 8-16 caracteres, incluindo maiúscula, número e caractere especial.",
                "danger"
            )

            # devolve TODOS os campos preenchidos
            return render_template(
                "cadastro_profissional.html",
                dados=dados
            )

        # EMAIL JÁ CADASTRADO
        usuario_existente = next(
            (u for u in usuarios if u["email"].lower() == dados["email"]),
            None
        )

        if usuario_existente:
            flash("Este email já está cadastrado.", "warning")

            return render_template(
                "cadastro_profissional.html",
                dados=dados
            )

        # SENHA HASH
        senha_hash = generate_password_hash(senha)

        # NOVO PROFISSIONAL
        novo_profissional = {
            "id": len(usuarios) + 1,
            "nome": dados["nome"],
            "sobrenome": dados["sobrenome"],
            "email": dados["email"],
            "telefone": dados["telefone"],

            "crp": dados["crp"],
            "uf_crp": dados["uf_crp"],
            "experiencia": dados["experiencia"],
            "especialidade": dados["especialidade"],
            "faculdade": dados["faculdade"],
            "pos": dados["pos"],
            "biografia": dados["biografia"],

            "online": dados["online"],
            "presencial": dados["presencial"],

            "senha": senha_hash,
            "email_confirmado": False,
            "tipo": dados["tipo"]
        }

        profissional.append(novo_profissional)

        # EMAIL
        if enviar_email_confirmacao(dados["email"]):
            flash(
                "Conta criada! Verifique seu email para confirmar o cadastro.",
                "success"
            )
        else:
            flash(
                "Conta criada, mas houve erro ao enviar o email de confirmação.",
                "warning"
            )

        return redirect(url_for('login'))

    # GET
    return render_template(
        'cadastro_profissional.html',
        dados=dados
    )

# Funções auxiliares
def carregar_forum():
    try:
        with open(FORUM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def salvar_forum(forum):
    with open(FORUM_FILE, "w", encoding="utf-8") as f:
        json.dump(forum, f, ensure_ascii=False, indent=4)
        
def senha_valida(senha):
    if len(senha) < 8 or len(senha) > 16:
        return False
    
    if not re.search(r"[A-Z]", senha):  # letra maiúscula
        return False
    
    if not re.search(r"[0-9]", senha):  # número
        return False
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):  # especial
        return False

    return True

@app.route("/")
def index():
    return render_template("index.html", noticias=noticias[:3])

@app.route("/noticias")
def todas_noticias():
    return render_template("noticia.html", noticias=noticias)

@app.route("/noticia/<int:noticia_id>")
def noticia_detalhe(noticia_id):
    noticia_encontrada = next((n for n in noticias if n["id"] == noticia_id), None)
    if noticia_encontrada is None:
        abort(404)
    return render_template("noticia.html", noticia=noticia_encontrada)

@app.route("/bloqueio")
def bloqueio():
    return render_template("bloqueio.html")

@app.route("/bloqueio-cpf")
def bloqueio_cpf():
    return render_template("bloqueio_cpf.html")

# Página principal do fórum
@app.route("/forum")
def forum_home():
    return render_template("forum.html", forum=forum)

# Criar novo tópico
@app.route("/forum/novo", methods=["GET", "POST"])
def forum_novo():
    if request.method == "POST":
        titulo = request.form.get("titulo")
        autor = request.form.get("autor") or "Anônimo"
        mensagem = request.form.get("mensagem")
        
        if titulo and mensagem:
            novo_topico = {
                "id": len(forum) + 1,
                "titulo": titulo,
                "mensagens": [
                    {
                        "autor": autor,
                        "mensagem": mensagem,
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                ]
            }
            forum.append(novo_topico)
            salvar_forum(forum)
            return redirect(url_for("forum_home"))
    return render_template("novo_topico.html")


@app.route("/forum/<int:topico_id>", methods=["GET", "POST"])
def forum_topico(topico_id):
    topico = next((t for t in forum if t["id"] == topico_id), None)
    if not topico:
        abort(404)

    usuario_atual = request.form.get("autor") or "Anônimo"

    if request.method == "POST":
        mensagem = request.form.get("mensagem")

        if mensagem:
            topico["mensagens"].append({
                "autor": usuario_atual,
                "mensagem": mensagem,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            })
            salvar_forum(forum)
            return redirect(url_for("forum_topico", topico_id=topico_id))

    return render_template(
        "topico.html",
        topico=topico,
        usuario_atual=usuario_atual,
        moderador=MODERADOR
    )


@app.route("/forum/<int:topico_id>/mensagem/<int:msg_index>/excluir", methods=["POST"])
def excluir_mensagem(topico_id, msg_index):
    topico = next((t for t in forum if t["id"] == topico_id), None)
    if not topico:
        abort(404)

    try:
        topico["mensagens"].pop(msg_index)
        salvar_forum(forum)
    except IndexError:
        abort(404)

    return redirect(url_for("forum_topico", topico_id=topico_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # mantém os dados digitados caso dê erro
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        # procura usuário pelo email
        usuario = next(
            (u for u in usuarios if u["email"].lower() == email),
            None
        )

        # verifica se existe
        if not usuario:
            flash("Email não encontrado.", "danger")
            return render_template("login.html", email=email)

        # verifica confirmação de email
        if not usuario.get("email_confirmado", False):
            flash("Confirme seu email antes de fazer login.", "warning")
            return render_template("login.html", email=email)

        if not check_password_hash(usuario["senha"], senha):
            flash("Senha incorreta.", "danger")

            # mantém o email preenchido
            return render_template(
                "login.html",
                email=email
            )

        # login OK
        session["usuario_id"] = usuario["id"]
        session["usuario_nome"] = usuario["nome"]
        session["tipo_usuario"] = usuario.get("tipo", "usuario")

        flash(f"Bem-vindo(a), {usuario['nome']}!", "success")

        return redirect(url_for("dashboard"))

    # GET
    return render_template("login.html")

@app.route('/escolher_cadastro')
def escolher_cadastro():
    return render_template('escolher_cadastro.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    # pega o tipo salvo no login/cadastro
    tipo_usuario = session.get("tipo_usuario", "usuario")

    # DASHBOARD USUÁRIO NORMAL
    if tipo_usuario == "usuario":
        return render_template("dashboard_usuario.html")

    # DASHBOARD PROFISSIONAL
    elif tipo_usuario == "profissional":
        return render_template("dashboard_profissional.html")

    # segurança extra
    flash("Tipo de usuário inválido.", "danger")
    return redirect(url_for("login"))

def enviar_email_confirmacao(email):
    try:
        token = serializer.dumps(email, salt='confirmacao-email')

        print("HOST:", request.host)
        print("URL_ROOT:", request.url_root)

        link = url_for(
            'confirmar_email',
            token=token,
            _external=True
        )


        msg = Message(
            subject='Confirme seu cadastro - Apoio & Consciência',
            recipients=[email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )

        # VERSÃO TEXTO
        msg.body = f"""
Confirme seu cadastro acessando o link abaixo:

{link}

Se você não criou essa conta, ignore esta mensagem.
        """

        # VERSÃO HTML PROFISSIONAL
        msg.html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
</head>
<body style="
    margin:0;
    padding:0;
    background-color:#f4f6f9;
    font-family:Arial, Helvetica, sans-serif;
">

    <div style="
        max-width:600px;
        margin:40px auto;
        background:#ffffff;
        border-radius:16px;
        overflow:hidden;
        box-shadow:0 8px 25px rgba(0,0,0,0.08);
    ">

        <!-- TOPO -->
        <div style="
            background:linear-gradient(135deg, #1d3557, #457b9d);
            padding:30px;
            text-align:center;
            color:white;
        ">
            <h1 style="margin:0; font-size:28px;">
                Apoio & Consciência
            </h1>
            <p style="margin-top:8px; font-size:15px; opacity:0.9;">
                Segurança e cuidado no seu cadastro
            </p>
        </div>

        <!-- CONTEÚDO -->
        <div style="padding:40px 30px; color:#333;">

            <h2 style="
                color:#1d3557;
                margin-top:0;
                text-align:center;
            ">
                Confirme seu cadastro
            </h2>

            <p style="
                font-size:16px;
                line-height:1.6;
                text-align:center;
                color:#555;
            ">
                Obrigado por se cadastrar em nossa plataforma.<br>
                Para ativar sua conta com segurança, confirme seu e-mail clicando no botão abaixo:
            </p>

            <!-- BOTÃO -->
            <div style="text-align:center; margin:35px 0;">
                <a href="{link}" style="
                    background:linear-gradient(135deg, #198754, #20c997);
                    color:white;
                    padding:14px 30px;
                    text-decoration:none;
                    border-radius:10px;
                    display:inline-block;
                    font-size:16px;
                    font-weight:bold;
                    box-shadow:0 4px 12px rgba(25,135,84,0.3);
                ">
                    Confirmar Cadastro
                </a>
            </div>

            <!-- LINK -->
            <p style="
                font-size:14px;
                color:#666;
                text-align:center;
                margin-bottom:8px;
            ">
                Se o botão não funcionar, copie e cole este link no navegador:
            </p>

            <div style="
                background:#f8f9fa;
                border:1px solid #dee2e6;
                padding:12px;
                border-radius:8px;
                word-break:break-all;
                font-size:13px;
                color:#0d6efd;
                text-align:center;
            ">
                {link}
            </div>

        </div>

        <!-- RODAPÉ -->
        <div style="
            background:#f8f9fa;
            padding:20px;
            text-align:center;
            font-size:13px;
            color:#6c757d;
            border-top:1px solid #e9ecef;
        ">
            Se você não criou essa conta, ignore esta mensagem com segurança.<br>
            © Apoio & Consciência
        </div>

    </div>

</body>
</html>
        """

        print("MAIL_USERNAME:", app.config['MAIL_USERNAME'])
        print("MAIL_PASSWORD:", os.getenv("MAIL_PASSWORD"))
        print("MAIL_DEFAULT_SENDER:", app.config['MAIL_DEFAULT_SENDER'])
        print("DESTINATÁRIO:", email)
        print("LINK:", link)

        mail.send(msg)

        print("EMAIL ENVIADO PARA:", email)
        return True

    except Exception as e:
        print("ERRO AO ENVIAR EMAIL:")
        traceback.print_exc()
        return False


@app.route("/teste-email")
def teste_email():
    email_teste = "gabrielgaburi6@gmail.com"  # troque se quiser

    sucesso = enviar_email_confirmacao(email_teste)

    if sucesso:
        return "Email enviado com sucesso! Verifique caixa de entrada, spam e lixo eletrônico."
    else:
        return "Falha no envio. Veja o terminal."
    
def enviar_email_recuperacao(email):
    try:
        token = serializer.dumps(email, salt='recuperar-senha')

        link = url_for(
            'redefinir_senha',
            token=token,
            _external=True
        )

        msg = Message(
            subject='Redefinição de senha - Apoio & Consciência',
            recipients=[email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )

        # =========================
        # VERSÃO TEXTO
        # =========================
        msg.body = f"""
Redefina sua senha acessando o link abaixo:

{link}

Se você não solicitou essa alteração, ignore este email com segurança.
        """

        # =========================
        # VERSÃO HTML PROFISSIONAL
        # =========================
        msg.html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
</head>
<body style="
    margin:0;
    padding:0;
    background-color:#f4f6f9;
    font-family:Arial, Helvetica, sans-serif;
">

    <div style="
        max-width:600px;
        margin:40px auto;
        background:#ffffff;
        border-radius:16px;
        overflow:hidden;
        box-shadow:0 8px 25px rgba(0,0,0,0.08);
    ">

        <!-- TOPO -->
        <div style="
            background:linear-gradient(135deg, #0d6efd, #3a86ff);
            padding:30px;
            text-align:center;
            color:white;
        ">
            <h1 style="margin:0; font-size:28px;">
                Apoio & Consciência
            </h1>
            <p style="margin-top:8px; font-size:15px; opacity:0.9;">
                Segurança para redefinição da sua conta
            </p>
        </div>

        <!-- CONTEÚDO -->
        <div style="padding:40px 30px; color:#333;">

            <h2 style="
                color:#0d6efd;
                margin-top:0;
                text-align:center;
            ">
                Redefinição de Senha
            </h2>

            <p style="
                font-size:16px;
                line-height:1.6;
                text-align:center;
                color:#555;
            ">
                Recebemos uma solicitação para redefinir sua senha.<br>
                Clique no botão abaixo para criar uma nova senha com segurança:
            </p>

            <!-- BOTÃO -->
            <div style="text-align:center; margin:35px 0;">
                <a href="{link}" style="
                    background:linear-gradient(135deg, #0d6efd, #3a86ff);
                    color:white;
                    padding:14px 30px;
                    text-decoration:none;
                    border-radius:10px;
                    display:inline-block;
                    font-size:16px;
                    font-weight:bold;
                    box-shadow:0 4px 12px rgba(13,110,253,0.3);
                ">
                    Redefinir Senha
                </a>
            </div>

            <!-- LINK -->
            <p style="
                font-size:14px;
                color:#666;
                text-align:center;
                margin-bottom:8px;
            ">
                Se o botão não funcionar, copie e cole este link no navegador:
            </p>

            <div style="
                background:#f8f9fa;
                border:1px solid #dee2e6;
                padding:12px;
                border-radius:8px;
                word-break:break-all;
                font-size:13px;
                color:#0d6efd;
                text-align:center;
            ">
                {link}
            </div>

        </div>

        <!-- ALERTA -->
        <div style="
            margin:0 30px 25px;
            padding:14px;
            background:#fff3cd;
            border:1px solid #ffe69c;
            border-radius:8px;
            color:#856404;
            font-size:14px;
            text-align:center;
        ">
            Se você não solicitou esta redefinição, ignore este email. Sua conta continuará segura.
        </div>

        <!-- RODAPÉ -->
        <div style="
            background:#f8f9fa;
            padding:20px;
            text-align:center;
            font-size:13px;
            color:#6c757d;
            border-top:1px solid #e9ecef;
        ">
            Protegendo seu acesso com responsabilidade.<br>
            © Apoio & Consciência
        </div>

    </div>

</body>
</html>
        """

        # DEBUG
        print("MAIL_USERNAME:", app.config['MAIL_USERNAME'])
        print("MAIL_DEFAULT_SENDER:", app.config['MAIL_DEFAULT_SENDER'])
        print("DESTINATÁRIO:", email)
        print("LINK RECUPERAÇÃO:", link)

        mail.send(msg)

        print("EMAIL DE RECUPERAÇÃO ENVIADO PARA:", email)
        return True

    except Exception as e:
        print("ERRO AO ENVIAR EMAIL DE RECUPERAÇÃO:")
        traceback.print_exc()
        return False
    
@app.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        usuario = next(
            (u for u in usuarios if u["email"].lower() == email),
            None
        )

        if not usuario:
            flash("Email não encontrado.", "danger")
            return render_template("esqueci_senha.html", email=email)

        if enviar_email_recuperacao(email):
            flash("Enviamos um link para redefinição de senha.", "success")
        else:
            flash("Erro ao enviar email de recuperação.", "danger")

        return redirect(url_for("login"))

    return render_template("esqueci_senha.html")

@app.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    try:
        email = serializer.loads(
            token,
            salt='recuperar-senha',
            max_age=3600
        )

    except:
        flash("Link inválido ou expirado.", "danger")
        return redirect(url_for("login"))

    usuario = next(
        (u for u in usuarios if u["email"].lower() == email.lower()),
        None
    )

    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":

        nova_senha = request.form.get("senha", "")

        if not senha_valida(nova_senha):
            flash("Senha inválida. Use 8-16 caracteres, maiúscula, número e especial.", "danger")
            return render_template("redefinir_senha.html")

        usuario["senha"] = generate_password_hash(nova_senha)

        flash("Senha redefinida com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("redefinir_senha.html")

@app.route("/ajuda")
def ajuda():
    locais = [

        # 🏥 Atendimento Público / Especializado

        {
            "nome": "Pro-AMJO – HC FMUSP (Jogo Patológico)",
            "cidade": "São Paulo",
            "tipo": "Atendimento Público / Especializado",
            "telefone" : "(11) 2661-7805",
            "endereco": "R. Dr. Ovídio Pires de Campos, 785 - Cerqueira César, São Paulo - SP",
            "lat": -23.5578,
            "lng": -46.6680
        },
        {
            "nome": "Instituto de Psiquiatria HC-FMUSP",
            "cidade": "São Paulo",
            "tipo": "Atendimento Público / Especializado",
            "telefone": "(11) 2661-6000",
            "endereco": "Rua Dr. Ovídio Pires de Campos, 785 - Cerqueira César, São Paulo - SP",
            "lat": -23.5576,
            "lng": -46.6682
        },
        {
            "nome": "PROAD – UNIFESP",
            "cidade": "São Paulo",
            "tipo": "Atendimento Público / Especializado",
            "telefone": "(11) 5576-4990",
            "endereco": "Rua Borges Lagoa, 570, Vila Clementino, em São Paulo - SP",
            "lat": -23.5945,
            "lng": -46.6536
        },
        
          {
            "nome": "CAPSad - Presidente Prudente",
            "cidade": "Presidente Prudente",
            "tipo": "Atendimento Público / Especializado",
            "telefone": "(18) 3907-6753",
            "endereco": "Rua dos Ipês Roxos, 480, Presidente Prudente - SP",
            "lat": -22.1297,
            "lng": -51.3897
        },
        {
            "nome": "Sanatório São João - Presidente Prudente",
            "cidade": "Presidente Prudente",
            "tipo": "Atendimento Público / Especializado",
            "telefone": "(18) 3222-2155",
            "endereco": "Rua Coronel Albino, 872, Presidente Prudente - SP",
            "lat": -22.1246,
            "lng": -51.3802
        },
        {
            "nome": "Sanatório Alan Kardec - Presidente Prudente",
            "cidade": "Presidente Prudente",
            "tipo": "Atendimento Público / Especializado",
            "telefone": "(18) 3222-8383",
            "endereco": "Rua Benedicto Franco, 200, Presidente Prudente - SP",
            "lat": -22.1183,
            "lng": -51.3972
        },
        
         {
            "nome": "CAPS II Saúde Mental - Itapetininga",
            "cidade": "Itapetininga",
            "tipo": "Atendimento Público / Especializado",
            "telefone": "(15) 3271-7789",
            "endereco": "Rua Gumercindo Soares Hungria, S/Nº, Itapetininga - SP",
            "lat": -23.5882,
            "lng": -48.0440
            
        },
        
         # 🧠 Clínicas-Escola / Atendimento Psicológico
        {
            "nome": "Hospital das Clínicas da Faculdade de Medicina de Ribeirão Preto",
            "cidade": "Ribeirão Preto",
            "tipo": "Hospital Universitário",
            "telefone": "(16) 3602-1000",
            "endereco": "Avenida Bandeirantes, 3900 - Monte Alegre, Ribeirão Preto - SP",
            "lat": -21.1767,
            "lng": -47.8208
        },
        {
            "nome": "Hospital de Clínicas UNICAMP",
            "cidade": "Campinas",
            "tipo": "Hospital Universitário",
            "telefone": "(19) 3521-2121",
            "endereco": "Rua Vital Brasil, 251, no distrito de Barão Geraldo. Campinas - SP",
            "lat": -22.8156,
            "lng": -47.0647
        },

        {
            "nome": "Clínica Psicológica USP",
            "cidade": "São Paulo",
            "tipo": "Hospital Universitário",
            "telefone": "(11) 3091-5015",
            "endereco": " Av. Professor Mello Moraes, 1721 - Butantã, São Paulo - SP", 
            "lat": -23.5658,
            "lng": -46.7237
        },
        {
            "nome": "Clínica-Escola Mackenzie",
            "cidade": "São Paulo",
            "tipo": "Hospital Universitário",
            "telefone": "(11) 2114-8342",
            "endereco": "Campus Higienópolis: R. Itambé, 143 – andar térreo, São Paulo - SP",
            "lat": -23.5475,
            "lng": -46.6521
        },
        {
            "nome": "Clínica-Escola UNIP",
            "cidade": "Bauru",
            "tipo": "Hospital Universitário",
            "telefone": "(14) 3312-7018",
            "endereco": "Rua Luiz Levorato, 2-140 - Chácaras Bauruenses, Bauru - SP ",
            "lat": -22.3250,
            "lng": -49.0667
        },
        {
            "nome": "Clínica-Escola UNINOVE",
            "cidade": "São Paulo",
            "tipo": "Hospital Universitário",
            "telefone": "(11) 4130-9050",
            "endereco": "Clinica Uninove, R. Dr. Siqueira Campos, 172 - Liberdade, São Paulo - SP",
            "lat": -23.5276,
            "lng": -46.6659
        },
        {
            "nome": "Clínica-Escola PUC Campinas",
            "cidade": "Campinas",
            "tipo": "Hospital Universitário",
            "telefone": "(19) 3343-6846",
            "endereco": "Avenida John Boyd Dunlop, s/n, Jardim Ipaussurama, Campinas - SP",
            "lat": -22.9099,
            "lng": -47.0626
        },

        # 🤝 Grupos de Apoio

        {
            "nome": "Grupo Pioneiro",
            "cidade": "São Paulo",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Guaporé, 335 - Luz - São Paulo - SP",
            "lat": -23.55052,
            "lng": -46.63331
        },
        {
            "nome": "Grupo Mauá",
            "cidade": "Mauá",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Praça Monsenhor Alexandre Venâncio Arminas, 01 - Matriz - Mauá - SP",
            "lat": -23.6675,
            "lng": -46.4614
        },
        {
            "nome": "Grupo Itaim",
            "cidade": "São Paulo",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Clodomiro Amazonas, 50 - Itaim Bibi - São Paulo - SP",
            "lat": -23.55052,
            "lng": -46.63331
        },
        {
            "nome": "Grupo Jabaquara",
            "cidade": "São Paulo",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Av. Jabaquara, 2682 - Jabaquara - São Paulo - SP",
            "lat": -23.9608,
            "lng": -46.3336
        },
        {
            "nome": "Grupo Buscando a Serenidade",
            "cidade": "São Paulo",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Pedreira de Magalhães, 100 - Artur Alvim - São Paulo - SP",
            "lat": -23.55052,
            "lng": -46.63331
        },
        {
            "nome": "Grupo Santos",
            "cidade": "Santos",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Av. Dr. Pedro Lessa, 2262 - Ponta da Praia - Santos - SP",
            "lat": -23.9608,
            "lng": -46.3336
        },
        {
            "nome": "Grupo Nova Chance",
            "cidade": "São Paulo",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Av. João Dias, 822 - Santo Amaro - São Paulo - SP",
            "lat": -23.55052,
            "lng": -46.63331
        },
        {
            "nome": "Grupo Santa Ifigênia",
            "cidade": "São Paulo",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Santa Ifigênia, 30 - Centro - São Paulo - SP",
            "lat": -23.55052,
            "lng": -46.63331
        },
        {
            "nome": "Grupo São Bernardo do Campo",
            "cidade": "São Bernardo do Campo",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Estrada Dos Casa, 3230 - São Bernardo do Campo - SP",
            "lat": -23.6920,
            "lng": -46.5649
        },
        {
            "nome": "Grupo Taubaté",
            "cidade": "Taubaté",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Maria Tereza de Moura, 150 - Taubaté - SP",
            "lat": -23.0207,
            "lng": -45.5558
        },
        {
            "nome": "Grupo Renascer - Campinas",
            "cidade": "Campinas",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Guaraci, 38 - Campinas - SP",
            "lat": -22.9056,
            "lng": -47.0608
        },
        {
            "nome": "Grupo Semeando Recomeços",
            "cidade": "São José dos Campos",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Bertioga, 191 - São José dos Campos - SP",
            "lat": -23.2038,
            "lng": -45.9009
        },
        {
            "nome": "Grupo Pindamonhangaba",
            "cidade": "Pindamonhangaba",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Homem de Melo, s/n - Pindamonhangaba - SP",
            "lat": -22.9308,
            "lng": -45.4772
        },
        {
            "nome": "Grupo Limeira",
            "cidade": "Limeira",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua Oscar Buzolin, 1-63 - Limeira - SP",
            "lat": -22.5647,
            "lng": -47.4016
        },
        {
            "nome": "Grupo Atibaia",
            "cidade": "Atibaia",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Av. Jerônimo de Camargo, 3111 - Atibaia - SP",
            "lat": -23.1189,
            "lng": -46.5559
        },
        {
            "nome": "Grupo São José do Rio Preto",
            "cidade": "São José do Rio Preto",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua José Martins Romero, 590 - São José do Rio Preto - SP",
            "lat": -20.8167,
            "lng": -49.3756
        },
        {
            "nome": "Grupo Bertioga",
            "cidade": "Bertioga",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Av. Anchieta, 1450 - Bertioga - SP",
            "lat": -23.8236,
            "lng": -45.4269
        },
        {
            "nome": "Grupo Sorocaba",
            "cidade": "Sorocaba",
            "tipo": "Grupo de Apoio",
            "telefone": "",
            "endereco": "Rua José Mesquita Sobrinho, 129 - Sorocaba - SP",
            "lat": -23.5015,
            "lng": -47.4526
        },

    
        
        
        {
            "nome": "Seção Núcleo de Atenção ao Toxicodependente (Senat) - Santos",
            "cidade": "Santos",
            "tipo": "Grupo de Apoio",
            "telefone": "(13) 3237-2681",
            "endereco": "Rua Silva Jardim, 354 - Encruzilhada, Santos - SP", 
            "lat": -23.9608,
            "lng": -46.3336
        },
       
        
        
        
      

    ]

    return render_template("ajuda.html", locais=locais)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
    


