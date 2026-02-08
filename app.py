
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



if __name__ == "__main__":
    app.run(debug=True)
    


