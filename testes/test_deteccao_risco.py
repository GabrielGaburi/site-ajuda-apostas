# Testes da detecção de risco e do pedido de atendimento humano (deteccao_risco.py).
# Rodar na raiz do projeto: .venv\Scripts\python -m unittest discover -s testes

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deteccao_risco import detect_critical, pediu_profissional

ZERO_WIDTH = "​"


def largura_total(texto):
    return "".join(chr(ord(c) + 0xFEE0) if "a" <= c <= "z" else c for c in texto)


def negrito(texto):
    return "".join(chr(0x1D5EE + ord(c) - ord("a")) if "a" <= c <= "z" else c for c in texto)


def circulado(texto):
    return "".join(chr(0x24D0 + ord(c) - ord("a")) if "a" <= c <= "z" else c for c in texto)


class TestDeteccaoDeRisco(unittest.TestCase):

    def assertDetecta(self, frases):
        nao_detectadas = [f for f in frases if not detect_critical(f)]
        self.assertEqual(nao_detectadas, [], "frases de risco que passaram sem alerta")

    def test_padroes_com_variacoes(self):
        self.assertDetecta([
            "quero morrer", "QUERO MORRER", "Quero Morrer.", "quero    morrer", "quero\nmorrer", "quero\tmorrer",
            "qu3ro m0rr3r", "kero morrer", "quero morer", "quero morrerrrr", "queroooo morrer", "quero morrer 😭",
            "quero morrer!!!", "eu quero morrer hoje", "vou me matar", "estou pensando em me matar",
            "não quero mais viver", "nao quero mais viver", "quero sumir", "quero acabar com tudo",
            "vou tirar minha vida", "não aguento mais", "perdi tudo apostando", "não consigo parar de apostar",
            "preciso de ajuda", "socorro", "estou endividado",
        ])

    def test_disfarces_de_formatacao(self):
        self.assertDetecta([
            "q u e r o  m o r r e r", "q.u.e.r.o m.o.r.r.e.r", "q-u-e-r-o m-o-r-r-e-r", "quero_morrer",
            largura_total("quero morrer"), negrito("quero morrer"), circulado("quero morrer"),
            "quero morrer" + ZERO_WIDTH, "quero mor" + ZERO_WIDTH + "rer", "quеro morrer",
            "quero morrér", "quero&nbsp;morrer", "quero%20morrer",
        ])

    def test_frases_de_risco_fora_das_listas_originais(self):
        self.assertDetecta([
            "vou me suicidar", "quero me suicidar", "pensei em suicídio ontem", "quero acabar com a minha vida",
            "vou tirar a própria vida", "não quero acordar amanhã", "seria melhor eu não existir", "vou me enforcar",
            "vou pular da ponte", "tomei todos os remédios", "ninguém sentiria minha falta", "quero desaparecer",
            "minha família ficaria melhor sem mim", "não tenho motivos pra viver", "cansei de tudo", "vou dar fim a tudo",
            "vou me machucar", "vou me cortar", "quero dormir e não acordar mais", "não vejo mais sentido em viver",
            "preferia estar morto", "vou me jogar na frente do carro", "i want to die", "quero me matar",
        ])

    def test_mensagens_comuns_nao_acionam_o_alerta(self):
        for frase in [
            "oi, tudo bem?", "bom dia", "como funciona o site?", "hoje foi um dia ótimo", "meu time ganhou ontem",
            "preciso de uma receita de bolo", "como faço para me cadastrar?", "obrigado pela conversa",
            "vou ao mercado comprar pão", "estou bem, e você?", "a ansiedade é normal?",
            "queria entender melhor sobre os jogos de azar", "minha vida está melhorando", "parei de apostar há 3 meses",
            "a e i o u", "o gato e o rato", "quero saber o horário", "vou a pé e volto de ônibus",
        ]:
            self.assertFalse(detect_critical(frase), frase)

    def test_frase_de_risco_escondida_em_texto_longo_e_repetitivo(self):
        # O limite de trechos comparados por padrão não pode esconder uma frase de risco
        quase = "quero mor " * 80
        self.assertTrue(detect_critical(quase + "kero morrer " + quase))
        self.assertTrue(detect_critical("quero mor " * 40 + "kero morrer " + "quero mor " * 120))
        self.assertTrue(detect_critical("quero mor " * 160 + "vou me suicidar"))
        self.assertFalse(detect_critical("quero mor " * 190))

    def test_vazio(self):
        for vazio in ("", "   ", None):
            self.assertFalse(detect_critical(vazio))

    def test_desempenho_com_mensagem_de_2000_caracteres(self):
        for nome, texto in {
            "quase padrão": "quero mor " * 200, "letra única": "a" * 2000, "padrão repetido": "nao aguento " * 160,
            "letras soltas": "q u e r o m o r " * 130, "espaços": " " * 1990 + "oi", "unicode": "é" * 2000,
        }.items():
            inicio = time.time()
            detect_critical(texto)
            pediu_profissional(texto)
            self.assertLess(time.time() - inicio, 2.0, nome)


class TestPedidoDeProfissional(unittest.TestCase):

    def test_pedidos_reconhecidos(self):
        for frase in [
            "quero falar com um profissional", "Quero Conversar com um profissional!", "preciso falar com um psicólogo",
            "quero atendimento profissional", "quero falar com um humano", "tem algum atendente?", "queria falar com um psicólogo",
            "quero um psicólogo", "me passa para um profissional", "pode chamar um profissional?", "preciso de um terapeuta",
            "quero falar com uma pessoa de verdade", "quero falar com alguém de verdade", "quero ajuda de um psicologo",
        ]:
            self.assertTrue(pediu_profissional(frase), frase)

    def test_conversa_comum_nao_e_pedido(self):
        for frase in ["oi, tudo bem?", "como funciona o site?", "meu pai é psicólogo", "quero parar de apostar", "bom dia", "", None]:
            self.assertFalse(pediu_profissional(frase), frase)


if __name__ == "__main__":
    unittest.main()
