
import json
from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import datetime

app = Flask(__name__)
MODERADOR = True

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


# Arquivo JSON para salvar o fórum
FORUM_FILE = "forum.json"

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

# Carregar tópicos existentes
forum = carregar_forum()


# Usuário atual e flag de moderador (apenas para exemplo, normalmente viria do login)
usuario_atual = "Anônimo"
moderador = True  # Defina como True apenas para você, o moderador

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
    app.run(debug=True)
    


