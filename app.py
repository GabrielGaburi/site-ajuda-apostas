from flask import Flask, render_template, abort

app = Flask(__name__)

# LISTA DE NOTÍCIAS
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
    }
]


@app.route("/")
def index():
    return render_template("index.html", noticias=noticias[:3])

@app.route("/noticias")
def todas_noticias():
    return render_template("noticia.html", noticias=noticias)

@app.route("/noticia/<int:noticia_id>")

def noticia_detalhe(noticia_id):
    noticia_encontrada = next(
        (n for n in noticias if n["id"] == noticia_id),
        None
    )

    if noticia_encontrada is None:
        abort(404)

    return render_template(
        "noticia.html",
        noticia=noticia_encontrada
    )


if __name__ == "__main__":
    app.run(debug=True)
