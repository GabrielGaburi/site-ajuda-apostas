# Testes da moderação de conteúdo do fórum e da biografia (moderacao.py e normalizacao.py).
# Rodar na raiz do projeto: .venv\Scripts\python -m unittest discover -s testes

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moderacao import verificar_conteudo_proibido
from normalizacao import forma_canonica, forma_colada, frase_presente, juntar_letras_soltas, limpar_unicode

ZERO_WIDTH = "​"


def largura_total(texto):
    return "".join(chr(ord(c) + 0xFEE0) if "a" <= c <= "z" else c for c in texto)


class TestModeracao(unittest.TestCase):

    def assertBloqueia(self, textos):
        passaram = [t for t in textos if not verificar_conteudo_proibido(t)]
        self.assertEqual(passaram, [], "textos que deveriam ser bloqueados")

    def test_formas_simples(self):
        self.assertBloqueia([
            "aposte agora", "APOSTE AGORA", "Aposte   agora", "aposte agora", "aposte\nagora", "ESTRATÉGIA PARA APOSTAR",
            "estrategia para apostar", "dicas de aposta", "bora apostar", "aposta garantida", "odd turbinada",
            "caralho", "CARALHO", "filho da puta", "fdp", "você é um idiota",
        ])

    def test_disfarces_de_apostas(self):
        self.assertBloqueia([
            "a p o s t e agora", "a.p.o.s.t.e agora", "ap0ste agora", "aposte, agora", "aposte-agora", "aposte_agora",
            "aposte" + ZERO_WIDTH + " agora", "apo" + ZERO_WIDTH + "ste agora", largura_total("aposte agora"),
            "apоste agora", "apooooste agora", "**aposte** agora", "aposte&nbsp;agora", "aposte%20agora", "apostee agora",
            "aposte agorá", "faça sua aposta hoje mesmo", "aposte já", "aposte hoje",
        ])

    def test_divulgacao_de_casas_de_apostas(self):
        self.assertBloqueia([
            "cadastre-se na bet e ganhe bônus", "use o código BET100 para ganhar 100 reais", "Ganhe bônus de boas-vindas",
            "deposite e ganhe", "rodadas grátis no cassino", "código promocional ótimo",
        ])

    def test_disfarces_de_palavroes(self):
        self.assertBloqueia([
            "m3rda", "p u t a", "pu.ta", "idiotas", "viados", "caralh0", "c a r a l h o", "f.d.p", "babacas",
            "p" + ZERO_WIDTH + "uta", largura_total("puta"), "ID1OTA", "v i a d o",
        ])

    def test_mensagens_diferentes_para_cada_tipo(self):
        self.assertIn("ofensiva", verificar_conteudo_proibido("seu idiota"))
        self.assertIn("apostas", verificar_conteudo_proibido("aposte agora"))
        self.assertIn("ofensiva", verificar_conteudo_proibido("i d i o t a"))

    def test_textos_legitimos_passam(self):
        for texto in [
            "Oi pessoal, tudo bem? Estou há 3 meses sem apostar.", "Hoje consegui conversar com minha família sobre o problema.",
            "Preciso de ajuda para parar.", "Meu cunhado joga muito", "Fui ao curral", "O computador está lento",
            "Alguém conhece grupos de apoio em Bauru?", "A cultura do jogo me prejudicou muito", "Uma reputação difícil de recuperar",
            "Perdi tudo na Betano e no Tigrinho, hoje faço terapia", "Já faz 2 anos que parei",
            "Me cadastrei no site ontem", "Consegui um bom emprego", "O código de barras não funcionou", "Moro na Rua das Palmeiras, 100",
            "Eu a e o u", "tenho 50 anos e 3 filhos",
        ]:
            self.assertIsNone(verificar_conteudo_proibido(texto), texto)


class TestNormalizacao(unittest.TestCase):

    def test_limpar_unicode(self):
        self.assertEqual(limpar_unicode("ÁÉÍ Çã"), "aei ca")
        self.assertEqual(limpar_unicode(largura_total("abc")), "abc")
        self.assertEqual(limpar_unicode("a" + ZERO_WIDTH + "b"), "ab")
        self.assertEqual(limpar_unicode("оla"), "ola")
        self.assertEqual(limpar_unicode("a&nbsp;b%20c"), "a b c")
        self.assertEqual(limpar_unicode(None), "")

    def test_forma_canonica(self):
        self.assertEqual(forma_canonica("Aposte,   AGORA!!!"), "aposte agora")
        self.assertEqual(forma_canonica("ap0ste_agooora"), "aposte agora")
        self.assertEqual(forma_canonica("p.u.t.a"), "p u t a")

    def test_forma_colada(self):
        self.assertEqual(forma_colada("pu.ta"), "puta")
        self.assertEqual(forma_colada("f.d.p"), "fdp")
        self.assertEqual(forma_colada("ca-ra-lho"), "caralho")
        self.assertEqual(forma_colada("oi, tudo bem?"), "oi tudo bem")

    def test_juntar_letras_soltas(self):
        self.assertEqual(juntar_letras_soltas("p u t a"), "puta")
        self.assertEqual(juntar_letras_soltas("a p o s t e agora"), "aposte agora")
        self.assertEqual(juntar_letras_soltas("oi tudo bem"), "oi tudo bem")
        self.assertEqual(juntar_letras_soltas(""), "")

    def test_frase_presente_exige_palavras_inteiras(self):
        self.assertTrue(frase_presente("eu quero aposte agora ja", "aposte agora"))
        self.assertFalse(frase_presente("computador", "puta"))
        self.assertFalse(frase_presente("", "puta"))
        self.assertFalse(frase_presente("abc", ""))


if __name__ == "__main__":
    unittest.main()
