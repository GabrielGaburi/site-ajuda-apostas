import secrets, re, json, os, traceback, uuid, mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
# =========================
# CONEXÃO COM MYSQL
# =========================

db_config = {
    "host": "localhost",
    "user": "root",
    "port": 3305,
    "password": "Behemoth666**",
    "database": "plataforma_apostas"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def testar_banco():
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute("SELECT DATABASE()")
        banco = cursor.fetchone()

        print("================================")
        print("BANCO CONECTADO:", banco[0])
        print("================================")

        cursor.close()
        conexao.close()

    except Exception as erro:
        print("================================")
        print("ERRO AO CONECTAR AO MYSQL:")
        print(erro)
        print("================================")
        
        
usuarios = []
profissionais = []

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)



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
        "cpf": "",
        "data_de_nascimento": "",
        "sexo": "",
        "email": "",
        "telefone": "",
        "cep": "",
        "rua": "",
        "numero": "",
        "bairro": "",
        "cidade": "",
        "estado": ""
    }

    if request.method == 'POST':
        
        print("================================")
        print("ENTROU NO POST DO CADASTRO")
        print("EMAIL RECEBIDO:", request.form.get("email"))
        print("SENHA RECEBIDA:", bool(request.form.get("senha")))
        print("================================")
        
        

        # captura TODOS os campos
        dados = {
            "tipo": "usuario",
            "nome": request.form.get("nome", "").strip(),
            "sobrenome": request.form.get("sobrenome", "").strip(),
            "cpf": request.form.get("cpf", "").strip(),
            "data_de_nascimento": request.form.get("data_de_nascimento", "").strip(),
            "sexo": request.form.get("sexo", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "telefone": request.form.get("telefone", "").strip(),
            "cep": request.form.get("cep", "").strip(),
            "rua": request.form.get("rua", "").strip(),
            "numero": request.form.get("numero", "").strip(),
            "bairro": request.form.get("bairro", "").strip(),
            "cidade": request.form.get("cidade", "").strip(),
            "estado": request.form.get("estado", "").strip()
        }
        
        senha = request.form.get('senha', '').strip()
        confirmar_senha = request.form.get("confirmar_senha", "").strip()
        termos = request.form.get("termos")

        # Validação em ordem de cima para baixo conforme o formulário
        campos_validacao = [
            ("nome", "Nome"),
            ("sobrenome", "Sobrenome"),
            ("cpf", "CPF"),
            ("data_de_nascimento", "Data de nascimento"),
            ("sexo", "Sexo"),
            ("email", "E-mail"),
            ("telefone", "Telefone"),
            ("cep", "CEP"),
            ("rua", "Rua"),
            ("numero", "Número"),
            ("bairro", "Bairro"),
            ("cidade", "Cidade"),
            ("estado", "Estado")
        ]

        # Valida campos obrigatórios
        for campo, nome_campo in campos_validacao:
            if not dados[campo]:
                return render_template(
                    "cadastro_usuario.html",
                    dados=dados,
                    campo_erro=campo,
                    mensagem_erro=f"O campo {nome_campo} é obrigatório."
                )

        # Valida CPF
        if not validar_cpf(dados["cpf"]):
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="cpf",
                mensagem_erro="CPF inválido."
            )

        # Valida data de nascimento
        try:
            data_nascimento = datetime.strptime(dados["data_de_nascimento"], "%d/%m/%Y")
        except ValueError:
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="data_de_nascimento",
                mensagem_erro="Data de nascimento inválida."
            )

        hoje = datetime.today()
        idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
        if idade < 18 or idade > 100:
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="data_de_nascimento",
                mensagem_erro="Idade deve estar entre 18 e 100 anos."
            )

        # Valida email
        padrao = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(padrao, dados["email"]):
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="email",
                mensagem_erro="Digite um e-mail válido."
            )

        # Valida senha
        if not senha or not confirmar_senha:
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="senha",
                mensagem_erro="Informe e confirme sua senha."
            )

        if senha != confirmar_senha:
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="senha",
                mensagem_erro="As senhas não coincidem."
            )

        if not senha_valida(senha):
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="senha",
                mensagem_erro="A senha deve ter entre 8 e 16 caracteres, conter letra maiúscula, número e caractere especial."
            )

        # Valida termos (por último)
        if termos != "aceito":
            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro="termos",
                mensagem_erro="Você deve aceitar os Termos de Uso e a Política de Privacidade."
            )
        # =========================
        # VERIFICA SE O EMAIL JÁ EXISTE NO MYSQL
        # =========================

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            cursor.execute(
                "SELECT id FROM usuarios WHERE email = %s",
                (dados["email"],)
            )

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                flash("Este email já está cadastrado.", "warning")

                return render_template(
                    "cadastro_usuario.html",
                    dados=dados,
                    campo_erro=None,
                    mensagem_erro=""
                )

            # =========================
            # CRIA O HASH DA SENHA
            # =========================

            senha_hash = generate_password_hash(senha)

            # =========================
            # INSERE O USUÁRIO NO MYSQL
            # =========================
            
            print("================================")
            print("VALOR DO NUMERO:", repr(dados["numero"]))
            print("TAMANHO DO NUMERO:", len(dados["numero"]))
            print("================================")

            cursor.execute(
                """
                INSERT INTO usuarios (
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
                    senha_hash,
                    tipo,
                    status,
                    email_confirmado,
                    termos_aceitos
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s
                )
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
                    senha_hash,
                    "usuario",
                    "ativo",
                    False,
                    True
                )
            )

            conexao.commit()

            print("USUÁRIO INSERIDO NO MYSQL:", dados["email"])

        except Exception as erro:

            if conexao:
                conexao.rollback()

            print("ERRO AO CADASTRAR USUÁRIO NO MYSQL:")
            traceback.print_exc()

            flash(
                "Ocorreu um erro ao realizar o cadastro. Tente novamente.",
                "danger"
            )

            return render_template(
                "cadastro_usuario.html",
                dados=dados,
                campo_erro=None,
                mensagem_erro=""
            )

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

        # =========================
        # EMAIL DE CONFIRMAÇÃO
        # =========================

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

    # =========================
    # GET
    # =========================

    return render_template(
        'cadastro_usuario.html',
        dados=dados,
        campo_erro=None,
        mensagem_erro=""
    )
    
@app.route('/confirmar_email/<token>')
def confirmar_email(token):

    try:
        email = serializer.loads(
            token,
            salt='confirmacao-email',
            max_age=3600
        )

    except Exception:
        flash("Link inválido ou expirado.", "danger")
        return redirect(url_for("login"))

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
            WHERE email = %s
            """,
            (email.lower(),)
        )

        usuario = cursor.fetchone()

        # Email não encontrado
        if not usuario:
            flash("Cadastro não encontrado.", "danger")
            return redirect(url_for("login"))

        # Já confirmado
        if usuario["email_confirmado"]:
            flash(
                "E-mail já confirmado. Faça login.",
                "info"
            )
            return redirect(url_for("login"))

        # Confirma o email
        cursor.execute(
            """
            UPDATE usuarios
            SET email_confirmado = TRUE
            WHERE id = %s
            """,
            (usuario["id"],)
        )

        conexao.commit()

        print("================================")
        print("EMAIL CONFIRMADO")
        print("ID:", usuario["id"])
        print("EMAIL:", usuario["email"])
        print("TIPO:", usuario["tipo"])
        print("================================")

        flash(
            "E-mail confirmado com sucesso! Agora você pode fazer login.",
            "success"
        )

        return redirect(url_for("login"))

    except Exception:

        if conexao:
            conexao.rollback()

        print("ERRO AO CONFIRMAR EMAIL NO MYSQL:")
        traceback.print_exc()

        flash(
            "Ocorreu um erro ao confirmar o email.",
            "danger"
        )

        return redirect(url_for("login"))

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()

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




@app.route('/cadastro_profissional', methods=['GET', 'POST'])
def cadastro_profissional():

    dados = {
        "tipo": "profissional",
        "nome": "",
        "sobrenome": "",
        "data_de_nascimento": "",
        "sexo": "",
        "email": "",
        "telefone": "",
        "cpf": "",
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
        "biografia": "",
        "termos": ""
    }

    if request.method == "POST":
        dados = {
            "tipo": "profissional",
            "nome": request.form.get("nome", "").strip(),
            "sobrenome": request.form.get("sobrenome", "").strip(),
            "data_de_nascimento": request.form.get("data_de_nascimento", "").strip(),
            "sexo": request.form.get("sexo", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "telefone": request.form.get("telefone", "").strip(),
            "cpf": request.form.get("cpf", "").strip(),
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
            "biografia": request.form.get("biografia", "").strip(),
            "termos": request.form.get("termos", "").strip()
        }

        foto = request.files.get("foto")
        senha = request.form.get("senha", "").strip()
        confirmar_senha = request.form.get("confirmar_senha", "").strip()
        termos = request.form.get("termos")

        # Validação em ordem de cima para baixo conforme o formulário
        campos_validacao = [
            ("nome", "Nome"),
            ("sobrenome", "Sobrenome"),
            ("cpf", "CPF"),
            ("data_de_nascimento", "Data de nascimento"),
            ("sexo", "Sexo"),
            ("email", "E-mail"),
            ("telefone", "Telefone"),
            ("cep", "CEP"),
            ("rua", "Rua"),
            ("numero", "Número"),
            ("bairro", "Bairro"),
            ("cidade", "Cidade"),
            ("estado", "Estado"),
            ("crp", "CRP"),
            ("uf_crp", "UF do CRP"),
            ("experiencia", "Experiência"),
            ("especialidade", "Especialidade"),
            ("faculdade", "Instituição de ensino"),
            ("pos", "Pós-graduação"),
            ("biografia", "Biografia")
        ]

        # Valida campos obrigatórios (de cima para baixo)
        for campo, nome_campo in campos_validacao:
            if not dados[campo]:
                return render_template(
                    "cadastro_profissional.html",
                    dados=dados,
                    campo_erro=campo,
                    mensagem_erro=f"O campo {nome_campo} é obrigatório."
                )

        # Valida CPF
        if not validar_cpf(dados["cpf"]):
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="cpf",
                mensagem_erro="CPF inválido."
            )

        # Valida data de nascimento
        try:
            data_nascimento = datetime.strptime(dados["data_de_nascimento"], "%d/%m/%Y")
        except ValueError:
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="data_de_nascimento",
                mensagem_erro="Data de nascimento inválida."
            )

        hoje = datetime.today()
        idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
        if idade < 18 or idade > 100:
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="data_de_nascimento",
                mensagem_erro="Idade deve estar entre 18 e 100 anos."
            )

        # Valida email
        padrao = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(padrao, dados["email"]):
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="email",
                mensagem_erro="Digite um e-mail válido."
            )

        # Valida foto
        if not foto or foto.filename == "":
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="foto",
                mensagem_erro="Selecione uma foto de perfil."
            )

        nome_original = secure_filename(foto.filename)
        extensao = os.path.splitext(nome_original)[1].lower()
        extensoes_validas = {".jpg", ".jpeg", ".png"}

        if extensao not in extensoes_validas:
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="foto",
                mensagem_erro="Formato de imagem inválido. Use JPG ou PNG."
            )

        # Valida senha
        if not senha or not confirmar_senha:
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="senha",
                mensagem_erro="Informe e confirme sua senha."
            )

        if senha != confirmar_senha:
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="senha",
                mensagem_erro="As senhas não coincidem."
            )

        if not senha_valida(senha):
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="senha",
                mensagem_erro="A senha deve ter entre 8 e 16 caracteres, conter letra maiúscula, número e caractere especial."
            )

        # Valida termos (por último)
        if termos != "aceito":
            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro="termos",
                mensagem_erro="Você deve aceitar os Termos de Uso e a Política de Privacidade."
            )

                # =========================
        # VERIFICA SE O EMAIL JÁ EXISTE NO MYSQL
        # =========================

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE email = %s
                """,
                (dados["email"],)
            )

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                flash("Este email já está cadastrado.", "warning")

                return render_template(
                    "cadastro_profissional.html",
                    dados=dados,
                    campo_erro="email",
                    mensagem_erro="Este email já está cadastrado."
                )

            # =========================
            # CRIA O HASH DA SENHA
            # =========================

            senha_hash = generate_password_hash(senha)

            # =========================
            # SALVA A FOTO
            # =========================

            nome_original = secure_filename(foto.filename)
            extensao = os.path.splitext(nome_original)[1].lower()

            nome_foto = f"{uuid.uuid4().hex}{extensao}"

            caminho_foto = os.path.join(
                app.config["UPLOAD_FOLDER"],
                nome_foto
            )

            foto.save(caminho_foto)

            # =========================
            # INSERE O USUÁRIO
            # =========================

            cursor.execute(
                """
                INSERT INTO usuarios (
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
                    senha_hash,
                    tipo,
                    status,
                    email_confirmado,
                    termos_aceitos
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s
                )
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
                    senha_hash,
                    "profissional",
                    "ativo",
                    False,
                    True
                )
            )

            # ID do usuário recém-criado
            usuario_id = cursor.lastrowid

            print("================================")
            print("USUÁRIO PROFISSIONAL CRIADO")
            print("ID:", usuario_id)
            print("EMAIL:", dados["email"])
            print("================================")

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

            conexao.commit()

            print("================================")
            print("PROFISSIONAL INSERIDO NO MYSQL")
            print("USUARIO_ID:", usuario_id)
            print("CRP:", dados["crp"])
            print("================================")

        except Exception:
            if conexao:
                conexao.rollback()

            print("ERRO AO CADASTRAR PROFISSIONAL NO MYSQL:")
            traceback.print_exc()

            flash(
                "Ocorreu um erro ao realizar o cadastro. Tente novamente.",
                "danger"
            )

            return render_template(
                "cadastro_profissional.html",
                dados=dados,
                campo_erro=None,
                mensagem_erro=""
            )

        finally:
            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

        # =========================
        # ENVIA EMAIL DE CONFIRMAÇÃO
        # =========================

        if enviar_email_confirmacao(dados["email"]):

            flash(
                "Cadastro realizado! Confirme seu email.",
                "success"
            )

        else:

            flash(
                "Cadastro criado, mas houve erro no envio do email.",
                "warning"
            )

        return redirect(url_for("login"))

    return render_template(
        "cadastro_profissional.html",
        dados=dados,
        campo_erro=None,
        mensagem_erro=""
    )
   

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

def validar_cpf(cpf):

    cpf = cpf.replace(".", "").replace("-", "")

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    soma = 0

    for i in range(9):
        soma += int(cpf[i]) * (10 - i)

    resto = (soma * 10) % 11

    if resto == 10:
        resto = 0

    if resto != int(cpf[9]):
        return False


    soma = 0

    for i in range(10):
        soma += int(cpf[i]) * (11 - i)

    resto = (soma * 10) % 11

    if resto == 10:
        resto = 0

    if resto != int(cpf[10]):
        return False


    return True

# Página principal do fórum
@app.route("/forum")
def forum_home():
    return render_template("forum.html", forum=forum)

# Criar novo tópico
@app.route("/forum/novo", methods=["GET", "POST"])
def forum_novo():

    if "usuario_id" not in session:
        flash("Você precisa estar logado para criar um tópico.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":

        titulo = request.form.get("titulo", "").strip()
        mensagem = request.form.get("mensagem", "").strip()

        if titulo and mensagem:

            novo_topico = {
                "id": len(forum) + 1,

                # Dono do tópico
                "usuario_id": session["usuario_id"],
                "usuario_nome": session["usuario_nome"],

                "titulo": titulo,

                "mensagens": [
                    {
                        "usuario_id": session["usuario_id"],
                        "autor": session["usuario_nome"],
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

    topico = next(
        (t for t in forum if t["id"] == topico_id),
        None
    )

    if not topico:
        abort(404)

    # Verifica se existe usuário logado
    usuario_id = session.get("usuario_id")

    # Verifica se é administrador
    moderador = session.get("tipo_usuario") == "admin"

    # =====================================
    # RESPOSTA NO TÓPICO
    # =====================================

    if request.method == "POST":

        # Visitante não pode responder
        if not usuario_id:
            flash(
                "Você precisa estar logado para participar do fórum.",
                "warning"
            )

            return redirect(url_for("login"))

        mensagem = request.form.get("mensagem", "").strip()

        if mensagem:

            topico["mensagens"].append({
                "usuario_id": usuario_id,
                "mensagem": mensagem,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            })

            salvar_forum(forum)

            return redirect(
                url_for(
                    "forum_topico",
                    topico_id=topico_id
                )
            )

    # =====================================
    # MOSTRA O TÓPICO
    # =====================================

    return render_template(
        "topico.html",
        topico=topico,
        usuario_id=usuario_id,
        moderador=moderador
    )
    
@app.route("/forum/<int:topico_id>/excluir", methods=["POST"])
def excluir_topico(topico_id):

    # Precisa estar logado
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))

    # Procura o tópico
    topico = next(
        (t for t in forum if t["id"] == topico_id),
        None
    )

    if not topico:
        abort(404)

    # =====================================
    # ADMINISTRADOR
    # =====================================

    if session.get("tipo_usuario") == "admin":

        forum.remove(topico)
        salvar_forum(forum)

        flash("Tópico excluído com sucesso.", "success")

        return redirect(url_for("forum_home"))

    # =====================================
    # IDENTIFICA O DONO DO TÓPICO
    # =====================================



    dono_id = topico.get("usuario_id")

    # =====================================
    # VERIFICA SE O USUÁRIO É O DONO
    # =====================================

    if dono_id != usuario_id:

        flash(
            "Você só pode excluir seus próprios tópicos.",
            "danger"
        )

        return redirect(
            url_for("forum_topico", topico_id=topico_id)
        )

    # =====================================
    # EXCLUI O TÓPICO
    # =====================================

    forum.remove(topico)
    salvar_forum(forum)

    flash("Tópico excluído com sucesso.", "success")

    return redirect(url_for("forum_home"))


@app.route(
    "/forum/<int:topico_id>/mensagem/<int:msg_index>/excluir",
    methods=["POST"]
)
def excluir_mensagem(topico_id, msg_index):

    # Precisa estar logado
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))

    # Procura o tópico
    topico = next(
        (t for t in forum if t["id"] == topico_id),
        None
    )

    if not topico:
        abort(404)

    # Verifica se a mensagem existe
    if msg_index < 0 or msg_index >= len(topico["mensagens"]):
        abort(404)

    mensagem = topico["mensagens"][msg_index]

    # =====================================
    # ADMINISTRADOR
    # =====================================

    if session.get("tipo_usuario") == "admin":

        topico["mensagens"].pop(msg_index)
        salvar_forum(forum)

        flash("Mensagem excluída com sucesso.", "success")

        return redirect(
            url_for("forum_topico", topico_id=topico_id)
        )
        
    # A mensagem inicial não pode ser excluída pelo usuário
    if msg_index == 0 and session.get("tipo_usuario") != "admin":

        flash(
            "A mensagem inicial não pode ser excluída.",
            "warning"
        )

        return redirect(
            url_for("forum_topico", topico_id=topico_id)
        )

    # =====================================
    # VERIFICA SE A MENSAGEM É DO USUÁRIO
    # =====================================

    if mensagem.get("usuario_id") != usuario_id:

        flash(
            "Você só pode excluir suas próprias mensagens.",
            "danger"
        )

        return redirect(
            url_for("forum_topico", topico_id=topico_id)
        )

    # =====================================
    # EXCLUI A MENSAGEM
    # =====================================

    topico["mensagens"].pop(msg_index)

    salvar_forum(forum)

    flash("Mensagem excluída com sucesso.", "success")

    return redirect(
        url_for("forum_topico", topico_id=topico_id)
    )





@app.route("/login", methods=["GET", "POST"])
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
                    id,
                    nome,
                    sobrenome,
                    email,
                    senha_hash,
                    tipo,
                    status,
                    email_confirmado
                FROM usuarios
                WHERE email = %s
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            # =========================
            # EMAIL NÃO ENCONTRADO
            # =========================

            if usuario is None:

                flash(
                    "Email não encontrado.",
                    "danger"
                )

                return render_template(
                    "login.html",
                    email=email
                )

            # =========================
            # VERIFICA STATUS
            # =========================

            if usuario["status"] == "banido":

                flash(
                    "Esta conta está bloqueada.",
                    "danger"
                )

                return render_template(
                    "login.html",
                    email=email
                )

            # =========================
            # VERIFICA EMAIL
            # =========================

            if not usuario["email_confirmado"]:

                flash(
                    "Confirme seu email antes de fazer login.",
                    "warning"
                )

                return render_template(
                    "login.html",
                    email=email
                )

            # =========================
            # VERIFICA SENHA
            # =========================

            if not check_password_hash(
                usuario["senha_hash"],
                senha
            ):

                flash(
                    "Senha incorreta.",
                    "danger"
                )

                return render_template(
                    "login.html",
                    email=email
                )

            # =========================
            # LOGIN REALIZADO
            # =========================

            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            session["tipo_usuario"] = usuario["tipo"]

            print("================================")
            print("LOGIN REALIZADO")
            print("ID:", usuario["id"])
            print("NOME:", usuario["nome"])
            print("EMAIL:", usuario["email"])
            print("TIPO:", usuario["tipo"])
            print("================================")

            flash(
                f"Bem-vindo(a), {usuario['nome']}!",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        except Exception:

            if conexao:
                conexao.rollback()

            print("ERRO AO REALIZAR LOGIN NO MYSQL:")
            traceback.print_exc()

            flash(
                "Ocorreu um erro ao realizar o login. Tente novamente.",
                "danger"
            )

            return render_template(
                "login.html",
                email=email
            )

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    # =========================
    # GET
    # =========================

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
        app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
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

        if usuario is None:
            usuario = next(
                (p for p in profissionais if p["email"].lower() == email),
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

    except Exception:
        flash("Link inválido ou expirado.", "danger")
        return redirect(url_for("login"))

    usuario = next(
        (u for u in usuarios if u["email"].lower() == email.lower()),
        None
    )

    if usuario is None:
        usuario = next(
            (p for p in profissionais if p["email"].lower() == email.lower()),
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

testar_banco()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
    


