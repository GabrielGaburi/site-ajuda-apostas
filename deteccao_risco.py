"""Detecção de situações de risco e de pedido de atendimento humano no chat.

Não depende do Flask nem do banco, para poder ser testado sozinho (testes/test_deteccao_risco.py).
"""

import re

from normalizacao import juntar_letras_soltas, limpar_unicode


# ============================ DETECÇÃO DE CRITICIDADE ============================ #
def _normalize_base(s: str) -> str:
    s = limpar_unicode(s or "")  # minúsculas, sem acentos e com os disfarces de Unicode desfeitos
    s = re.sub(r"[’'`´]", "'", s)
    s = re.sub(r"[^\w\s'!?💔😭😢😞]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _leet_to_plain(s: str) -> str:
    return (s.replace("0", "o")
             .replace("1", "i")
             .replace("3", "e")
             .replace("4", "a")
             .replace("5", "s")
             .replace("7", "t"))

def _collapse_repeats(s: str) -> str:
    return re.sub(r"(.)\1{2,}", r"\1\1", s)

def _normalize_all(s: str) -> str:
    return _collapse_repeats(_leet_to_plain(_normalize_base(s)))

def _lev_dist(a: str, b: str, limite=None) -> int:
    # Com limite, para assim que a distância já passou dele (devolve limite + 1)
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev = i - 1
        dp[0] = i
        for j, cb in enumerate(b, 1):
            tmp = dp[j]
            dp[j] = prev if ca == cb else 1 + min(prev, dp[j], dp[j-1])
            prev = tmp
        if limite is not None and min(dp) > limite:
            return limite + 1
    return dp[-1]


# Máximo de trechos do texto comparados por padrão. Um texto cheio de quase-acertos
# ("quero mor quero mor ...") não pode deixar a resposta lenta; ficam trechos espaçados por todo o texto.
MAX_JANELAS = 40

def _fuzzy_includes(hay: str, needle: str, max_edits: int = 1) -> bool:
    if needle in hay:
        return True
    n = len(needle)
    if n == 0 or len(hay) < max(1, n - max_edits):
        return False
    max_edits = min(max_edits + n // 12, 2)

    # Com até k edições, pelo menos um de k+1 pedaços do termo aparece intacto.
    # Só calcula a distância nas janelas ao redor desses pedaços; comparar a
    # janela de cada posição do texto levava segundos numa mensagem longa.
    pedacos = max_edits + 1
    tamanho = n // pedacos
    if tamanho == 0:
        return False

    janelas = set()
    for p in range(pedacos):
        inicio = p * tamanho
        fim = n if p == pedacos - 1 else inicio + tamanho
        pedaco = needle[inicio:fim]
        pos = hay.find(pedaco)
        while pos != -1:
            for i in range(pos - inicio - max_edits, pos - inicio + max_edits + 1):
                if 0 <= i <= len(hay):
                    janelas.add(i)
            pos = hay.find(pedaco, pos + 1)

    # O comprimento da janela também varia: uma inserção deixa o trecho
    # correspondente em hay mais longo que o termo, e uma remoção o deixa
    # mais curto. Fixar o comprimento em len(needle) perdia esses casos.
    if len(janelas) > MAX_JANELAS:
        ordenadas = sorted(janelas)
        passo = len(ordenadas) / MAX_JANELAS
        janelas = {ordenadas[int(k * passo)] for k in range(MAX_JANELAS)} | {ordenadas[-1]}

    for i in janelas:
        for comprimento in range(max(1, n - max_edits), n + max_edits + 1):
            fim = i + comprimento
            if fim > len(hay):
                continue
            if _lev_dist(hay[i:fim], needle, max_edits) <= max_edits:
                return True

    return False

_normalizados = {}

def _normalizar_variante(v: str) -> str:
    if v not in _normalizados:
        _normalizados[v] = _normalize_all(v)
    return _normalizados[v]

def _fuzzy_any(hay: str, variants, max_edits: int = 1) -> bool:
    return any(_fuzzy_includes(hay, _normalizar_variante(v), max_edits) for v in variants if v)

CRITICAL_PATTERNS = {
    "suicidio": [
        "suicidio","me matar","tirar minha vida","acabar com tudo",
        "quero morrer","sem vontade de viver","nao quero mais viver",
        "pensando em morrer","ideacao suicida","quero sumir"
    ],
    "distress": [
        "nao aguento","nao aguento mais","desespero","sem saida","sem saída",
        "to mal","tô mal","muito mal","pior dia","crise de panico","crise panico",
        "ataque de panico","ansiedade forte","desesperado","no fundo do poco","no fundo do poço",
        "sou um lixo","nao presto","nao vejo futuro","sofrendo demais"
    ],
    "help": [
        "quero ajuda","preciso de ajuda","socorro","me ajuda","ajuda por favor",
        "falar com alguem","conversar com alguem","preciso falar com alguem",
        "posso falar com alguem","quero conversar com alguem","apoio agora"
    ],
    "gambling_crisis": [
        "nao consigo parar de apostar","nao consigo parar","compulsao por apostar","compulsao por jogo",
        "recaida","recaída","voltei a apostar","perdi tudo","perdi meu salario","perdi meu salário",
        "endividado","muita divida","muitas dividas","divida com agiota","cobranca pesada",
        "quebrado","rompi limite"
    ],
    "family": [
        "meu marido aposta","minha esposa aposta","meu filho viciado","minha filha viciada",
        "meu pai viciado","minha mae viciada","meu irmão viciado","minha irmã viciada",
        "meu namorado aposta","minha namorada aposta","alguem proximo viciado","alguém próximo viciado",
        "ajuda para familia","sou familiar de viciado","sou parente de viciado"
    ]
}
# Frases de risco de vida e de autolesão que a lista acima não cobria
CRITICAL_PATTERNS["risco_de_vida"] = [
    "me suicidar","acabar com minha vida","acabar com a minha vida","acabar com a vida",
    "tirar a minha vida","tirar a propria vida","tirar minha propria vida","me enforcar",
    "me jogar da","me jogar na frente","me jogar de","pular da ponte","pular do predio",
    "nao quero acordar","nao quero mais acordar","dormir e nao acordar","melhor eu nao existir",
    "melhor sem mim","ficaria melhor sem mim","ficariam melhor sem mim","ninguem sentiria minha falta",
    "quero desaparecer","dar fim a tudo","dar um fim em tudo","dar fim a minha vida",
    "nao tenho motivo para viver","nao tenho motivos pra viver","nao tenho motivos para viver",
    "nao vejo sentido em viver","nao vejo mais sentido","preferia estar morto","preferia estar morta",
    "queria estar morto","queria estar morta","tomei todos os remedios","tomar todos os remedios",
    "overdose","me machucar","me cortar","me ferir","automutilacao","i want to die","kill myself",
    "cansei de tudo"
]

# Parte de palavras que já indica o assunto ("suicidar", "suicida", "suicidio")
RADICAIS_CRITICOS = ["suicid"]

CORE_SIGNALS = [
    "me matar","acabar com tudo","quero morrer","nao aguento mais",
    "preciso de ajuda","socorro","sem saida","muito mal",
    "nao consigo parar","perdi tudo","endividado"
]

def _tem_sinal_critico(n: str) -> bool:
    if any(radical in n for radical in RADICAIS_CRITICOS):
        return True
    for variants in CRITICAL_PATTERNS.values():
        if _fuzzy_any(n, variants, 1):
            return True
    return _fuzzy_any(n, CORE_SIGNALS, 2)


# Versões sem espaço dos padrões mais longos, para texto com letras separadas ("q u e r o m o r r e r")
_PADROES_COMPACTOS = None


def _padroes_compactos():
    global _PADROES_COMPACTOS
    if _PADROES_COMPACTOS is None:
        todos = [p for lista in CRITICAL_PATTERNS.values() for p in lista] + CORE_SIGNALS
        _PADROES_COMPACTOS = {
            c for c in (_normalizar_variante(p).replace(" ", "") for p in todos) if len(c) >= 8
        }
    return _PADROES_COMPACTOS


def detect_critical(text: str) -> bool:
    if not text or not text.strip():
        return False

    n = _normalize_all(text)

    if _tem_sinal_critico(n):
        return True

    # Letras separadas por espaço, ponto ou hífen: "q u e r o  m o r r e r"
    juntas = juntar_letras_soltas(n)

    if juntas != n:
        if _tem_sinal_critico(juntas):
            return True

        sem_espaco = juntas.replace(" ", "")

        if any(padrao in sem_espaco for padrao in _padroes_compactos()):
            return True

    return False

PEDIDOS_DE_PROFISSIONAL = [
    "quero conversar com um profissional",
    "quero falar com um profissional",
    "preciso conversar com um profissional",
    "preciso falar com um profissional",
    "quero atendimento profissional",
    "preciso de atendimento profissional",
    "quero ajuda de um profissional",
    "preciso de ajuda de um profissional",
    "quero falar com psicologo",
    "quero conversar com psicologo",
    "preciso falar com psicologo",
    "preciso conversar com psicologo",
    # Outros jeitos de pedir uma pessoa de verdade
    "quero falar com um psicologo",
    "quero conversar com um psicologo",
    "preciso falar com um psicologo",
    "preciso conversar com um psicologo",
    "queria falar com um psicologo",
    "queria falar com um profissional",
    "quero um psicologo",
    "preciso de um psicologo",
    "quero ajuda de um psicologo",
    "preciso de um terapeuta",
    "quero um terapeuta",
    "quero falar com um terapeuta",
    "quero falar com um humano",
    "preciso falar com um humano",
    "quero um atendente",
    "quero falar com um atendente",
    "quero falar com atendente",
    "tem algum atendente",
    "tem atendente",
    "atendimento humano",
    "quero falar com uma pessoa",
    "quero falar com uma pessoa de verdade",
    "quero falar com alguem de verdade",
    "falar com uma pessoa de verdade",
    "me passa para um profissional",
    "me passe para um profissional",
    "pode chamar um profissional",
    "chama um profissional",
]


def pediu_profissional(texto):
    if not texto:
        return False

    texto = _normalize_all(texto)

    return _fuzzy_any(texto, PEDIDOS_DE_PROFISSIONAL, 1)
