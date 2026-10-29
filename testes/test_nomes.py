# Testes do nome exibido no fórum (nomes.py).
# Rodar na raiz do projeto: .venv\Scripts\python -m unittest discover -s testes

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nomes import nome_publico


class TestNomePublico(unittest.TestCase):

    def test_usuario_comum_aparece_abreviado(self):
        self.assertEqual(nome_publico("Maria", "Silva"), "Maria S.")
        self.assertEqual(nome_publico("Maria", "silva souza", "usuario"), "Maria S.")
        self.assertEqual(nome_publico("  João  Pedro ", " de Almeida "), "João D.")

    def test_nunca_mostra_o_sobrenome_completo(self):
        texto = nome_publico("Maria", "Zxqwvutsr")
        self.assertNotIn("Zxqw", texto)
        self.assertEqual(texto, "Maria Z.")

    def test_profissional_e_admin_com_nome_completo(self):
        self.assertEqual(nome_publico("Ana", "Souza", "profissional"), "Ana Souza")
        self.assertEqual(nome_publico("Administrador", "Geral", "admin"), "Administrador Geral")

    def test_conta_excluida(self):
        self.assertEqual(nome_publico("Usuário", "removido"), "Usuário removido")

    def test_dados_incompletos_nao_quebram(self):
        self.assertEqual(nome_publico("Maria", ""), "Maria")
        self.assertEqual(nome_publico("Maria", None), "Maria")
        self.assertEqual(nome_publico("", "Silva"), "Participante S.")
        self.assertEqual(nome_publico(None, None), "Participante")
        self.assertEqual(nome_publico("", "", "profissional"), "Participante")

    def test_html_nao_e_interpretado_aqui(self):
        # O escape é do Jinja; a função só devolve texto
        self.assertEqual(nome_publico("<b>Maria", "<i>Silva"), "<b>Maria <.")


if __name__ == "__main__":
    unittest.main()
