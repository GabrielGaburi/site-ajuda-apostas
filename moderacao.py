"""Moderação de conteúdo do fórum e da biografia dos profissionais.

Não depende do Flask nem do banco, para poder ser testado sozinho (testes/test_moderacao.py).
"""

import re

from normalizacao import forma_canonica, forma_colada, frase_presente, juntar_letras_soltas


PALAVRAS_PROIBIDAS = [
    "porra",
    "merda",
    "caralho",
    "foda-se",
    "fodase",
    "foder",
    "fudeu",
    "puta",
    "puto",
    "putaria",
    "buceta",
    "cacete",
    "cu",
    "cuzão",
    "cusao",
    "cuzona",
    "viado",
    "veado",
    "bicha",
    "baitola",
    "retardado",
    "imbecil",
    "idiota",
    "otário",
    "otario",
    "babaca",
    "burro",
    "estúpido",
    "estupido",
    "arrombado",
    "desgraçado",
    "desgracado",
    "filho da puta",
    "filhodaputa",
    "piranha",
    "vagabunda",
    "vagabundo",
    "safado",
    "fdp",
    "vtnc",
    "bct",
    "safada"
]

FRASES_APOSTAS_PROIBIDAS = [
    "aposte agora",
    "aposta agora",
    "apostem agora",
    "vai apostar",
    "vá apostar",
    "va apostar",
    "vamos apostar",
    "bora apostar",
    "bora aposta",
    "faça uma aposta",
    "faca uma aposta",
    "faz uma aposta",
    "faça sua aposta",
    "faca sua aposta",
    "faz sua aposta",
    "coloque uma aposta",
    "coloca uma aposta",
    "faça sua fezinha",
    "faca sua fezinha",
    "faz uma fezinha",
    "tente a sorte",
    "tenta a sorte",
    "arrisque seu dinheiro",
    "arrisca seu dinheiro",
    "coloque seu dinheiro",
    "coloca seu dinheiro",
    "jogue seu dinheiro",
    "joga seu dinheiro",
    "aposte nesse jogo",
    "aposta nesse jogo",
    "aposte nesse time",
    "aposta nesse time",
    "aposte nesse campeonato",
    "aposta nesse campeonato",
    "entra nessa aposta",
    "entre nessa aposta",
    "aproveite e aposte",
    "aproveita e aposta",
    "não perca essa aposta",
    "nao perca essa aposta",
    "não deixe de apostar",
    "nao deixe de apostar",
    "vale a pena apostar",
    "compensa apostar",
    "melhor apostar",
    "tem que apostar"
]

FRASES_PROMOCAO_APOSTAS = [
    "ganhe dinheiro apostando",
    "ganhar dinheiro apostando",
    "ganhe dinheiro com apostas",
    "ganhar dinheiro com apostas",
    "fique rico apostando",
    "ficar rico apostando",
    "fique rico com apostas",
    "dinheiro fácil com apostas",
    "dinheiro facil com apostas",
    "lucro garantido",
    "ganho garantido",
    "renda garantida",
    "retorno garantido",
    "lucro fácil",
    "lucro facil",
    "ganho fácil",
    "ganho facil",
    "dinheiro fácil",
    "dinheiro facil",
    "dinheiro rápido",
    "dinheiro rapido",
    "ganhe fácil",
    "ganhe facil",
    "ganhe rápido",
    "ganhe rapido",
    "ganhe muito apostando",
    "ganhe muito com apostas",
    "lucre apostando",
    "lucrar apostando",
    "lucre com apostas",
    "lucrar com apostas",
    "renda com apostas",
    "renda através de apostas",
    "renda atraves de apostas",
    "viva de apostas",
    "viver de apostas"
]

FRASES_RECUPERACAO_PERDAS = [
    "recupere seu dinheiro apostando",
    "recuperar seu dinheiro apostando",
    "recupere o dinheiro perdido",
    "recuperar o dinheiro perdido",
    "recupere suas perdas",
    "recuperar suas perdas",
    "recupere o prejuízo",
    "recuperar o prejuizo",
    "recupere o prejuízo apostando",
    "recuperar o prejuizo apostando",
    "dobre sua banca",
    "dobrar sua banca",
    "duplique sua banca",
    "duplicar sua banca",
    "aumente sua banca",
    "aumentar sua banca",
    "recupere na próxima aposta",
    "recuperar na próxima aposta",
    "recuperar na proxima aposta",
    "apostar mais para recuperar",
    "aposte mais para recuperar",
    "apostando mais você recupera",
    "apostando mais voce recupera",
    "não pare até recuperar",
    "nao pare ate recuperar"
]

FRASES_DIVULGACAO_APOSTAS = [
    "site de apostas",
    "sites de apostas",
    "casa de apostas",
    "casas de apostas",
    "plataforma de apostas",
    "plataformas de apostas",
    "aplicativo de apostas",
    "aplicativo para apostas",
    "app de apostas",
    "link de aposta",
    "link para apostar",
    "link de apostas",
    "código promocional",
    "codigo promocional",
    "cupom de aposta",
    "cupom de apostas",
    "bônus de aposta",
    "bonus de aposta",
    "bônus de apostas",
    "bonus de apostas",
    "bônus de cadastro",
    "bonus de cadastro",
    "bônus grátis",
    "bonus gratis",
    "indicação de aposta",
    "indicacao de aposta",
    "indicação de apostas",
    "indicacao de apostas"
]

TERMOS_PROMOCAO_APOSTAS = [
    "odd alta",
    "odds altas",
    "odd turbinada",
    "odds turbinadas",
    "aposta segura",
    "aposta certa",
    "aposta garantida",
    "apostas seguras",
    "apostas certas",
    "apostas garantidas",
    "palpite certeiro",
    "palpite garantido",
    "dica de aposta",
    "dicas de aposta",
    "dica para apostar",
    "dicas para apostar",
    "estratégia de aposta",
    "estrategia de aposta",
    "estratégia para apostar",
    "estrategia para apostar",
    "método para ganhar",
    "metodo para ganhar",
    "método para lucrar",
    "metodo para lucrar",
    "banca garantida",
    "banca fácil",
    "banca facil"
]

# Divulgação e promoção de apostas que as listas acima não cobriam. Marcas de casas de
# apostas ficam de fora de propósito: quem conta o que perdeu precisa poder citá-las.
FRASES_DIVULGACAO_EXTRA = [
    "cadastre-se na bet",
    "cadastre-se na casa",
    "cadastre-se na plataforma",
    "cadastre-se e ganhe",
    "ganhe bônus",
    "ganhe um bônus",
    "bônus de boas-vindas",
    "bônus de cadastro",
    "bônus de depósito",
    "código promocional",
    "cupom de bônus",
    "use o código",
    "use o cupom",
    "deposite e ganhe",
    "primeiro depósito",
    "rodadas grátis",
    "giros grátis",
    "freebet",
    "free bet",
    "aposte já",
    "aposte hoje",
    "aposte aqui",
    "aposta grátis",
    "aposta sem risco",
    "ganhe dinheiro apostando",
    "lucre apostando",
    "renda extra com apostas",
]

def normalizar_texto(texto):
    texto = texto.lower().strip()

    substituicoes = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c"
    }

    for original, substituto in substituicoes.items():
        texto = texto.replace(original, substituto)

    texto = re.sub(r"\s+", " ", texto)

    return texto


def verificar_conteudo_proibido(texto):
    texto_normalizado = normalizar_texto(texto)

    for palavra in PALAVRAS_PROIBIDAS:
        palavra_normalizada = normalizar_texto(palavra)

        if re.search(
            r"\b" + re.escape(palavra_normalizada) + r"\b",
            texto_normalizado
        ):
            return "A mensagem contém linguagem ofensiva não permitida."

    grupos_de_frases = [
        FRASES_APOSTAS_PROIBIDAS,
        FRASES_PROMOCAO_APOSTAS,
        FRASES_RECUPERACAO_PERDAS,
        FRASES_DIVULGACAO_APOSTAS,
        TERMOS_PROMOCAO_APOSTAS
    ]

    for grupo in grupos_de_frases:
        for frase in grupo:
            frase_normalizada = normalizar_texto(frase)

            if frase_normalizada in texto_normalizado:
                return (
                    "Esta mensagem contém conteúdo que incentiva, "
                    "promove ou estimula apostas."
                )

    # Segunda passada, na forma canônica: pega o que a primeira deixa escapar por disfarce
    # (letras separadas, leet, pontuação no meio, caracteres invisíveis, plural...)
    canonico = forma_canonica(texto)
    variantes_de_frase = (canonico, juntar_letras_soltas(canonico))

    for variante in variantes_de_frase + (forma_colada(texto),):

        for palavra in PALAVRAS_PROIBIDAS:
            if re.search(r"\b" + re.escape(_canonica(palavra)) + r"(?:s|es)?\b", variante):
                return "A mensagem contém linguagem ofensiva não permitida."

    for variante in variantes_de_frase:

        for grupo in grupos_de_frases + [FRASES_DIVULGACAO_EXTRA]:
            for frase in grupo:
                if frase_presente(variante, _canonica(frase)):
                    return (
                        "Esta mensagem contém conteúdo que incentiva, "
                        "promove ou estimula apostas."
                    )

    return None


_canonicas = {}


def _canonica(frase):
    if frase not in _canonicas:
        _canonicas[frase] = forma_canonica(frase)

    return _canonicas[frase]
