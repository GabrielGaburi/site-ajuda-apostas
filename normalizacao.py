"""Normalização de texto usada na detecção de risco e na moderação.

Desfaz os truques mais comuns para escapar de filtros: letras de largura total ou em
negrito, caracteres invisíveis (zero-width), letras parecidas de outros alfabetos,
entidades HTML, "leet speak" e letras separadas por espaço, ponto ou hífen.

Não depende do Flask nem do banco, para poder ser testado sozinho (testes/test_normalizacao.py).
"""

import html
import re
import unicodedata
from urllib.parse import unquote

# Letras de outros alfabetos que se parecem com letras latinas (já em minúsculas)
_HOMOGLIFOS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ј": "j",
    "ѕ": "s", "к": "k", "м": "m", "т": "t", "н": "h", "в": "b",
    "α": "a", "ο": "o", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
    "ı": "i",
})

_LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s",
})


def limpar_unicode(texto):
    """Minúsculas e sem acentos, com os disfarces de Unicode desfeitos. Mantém a pontuação."""

    texto = html.unescape(unquote(texto or ""))

    # Largura total, letras matemáticas, circuladas etc. viram letras comuns
    texto = unicodedata.normalize("NFKC", texto)

    # Caracteres invisíveis (zero-width, soft hyphen, marcas de direção) somem;
    # os de controle viram espaço
    texto = "".join(
        "" if unicodedata.category(c) == "Cf" else (" " if unicodedata.category(c) == "Cc" else c)
        for c in texto
    )

    texto = texto.lower().translate(_HOMOGLIFOS)

    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def forma_canonica(texto):
    """Só palavras em minúsculas e sem acento, separadas por um espaço.

    Troca "leet speak" por letras, tira pontuação e reduz letras repetidas a uma só
    ("apooooste" e "aposte" ficam iguais). Use a mesma função nas frases da lista."""

    texto = limpar_unicode(texto).translate(_LEET)
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    texto = re.sub(r"([a-z0-9])\1+", r"\1", texto)

    return texto.strip()


def forma_colada(texto):
    """Como forma_canonica, mas sem os separadores entre letras: "pu.ta" e "f.d.p" viram "puta" e "fdp".

    Serve para palavras ofensivas, que são raras dentro de outras palavras. Em frases comuns
    ela juntaria palavras ("aposte.agora"), por isso as frases usam só a forma_canonica."""

    texto = re.sub(r"(?<=[^\W_])[.\-_*·•|/\\]+(?=[^\W_])", "", limpar_unicode(texto))

    return forma_canonica(texto)


def juntar_letras_soltas(canonico):
    """Junta letras isoladas em sequência: "p u t a" vira "puta"."""

    resultado = []
    corrida = []

    for palavra in canonico.split():
        if len(palavra) == 1:
            corrida.append(palavra)
            continue

        if corrida:
            resultado.append("".join(corrida))
            corrida = []

        resultado.append(palavra)

    if corrida:
        resultado.append("".join(corrida))

    return " ".join(resultado)


def frase_presente(texto, frase):
    """Diz se a frase aparece no texto como palavras inteiras (ambos na forma canônica)."""

    return bool(frase) and f" {frase} " in f" {texto} "
