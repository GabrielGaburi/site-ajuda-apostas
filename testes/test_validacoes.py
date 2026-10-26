# Testes das validações compartilhadas pelos cadastros (validacoes.py).
# Rodar na raiz do projeto: .venv\Scripts\python -m unittest discover -s testes

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validacoes import (
    ErroCadastro,
    formatar_cpf,
    senha_valida,
    validar_cpf,
    validar_dados_pessoais,
    validar_senha_e_termos
)

CAMPOS = [
    ("nome", "Nome"),
    ("sobrenome", "Sobrenome"),
    ("cpf", "CPF"),
    ("data_de_nascimento", "Data de nascimento"),
    ("sexo", "Sexo"),
    ("email", "E-mail"),
    ("telefone", "Telefone"),
    ("cep", "CEP"),
    ("estado", "UF"),
    ("cidade", "Cidade"),
    ("rua", "Rua"),
    ("numero", "Número"),
    ("bairro", "Bairro")
]


def dados_validos(**alteracoes):
    dados = {
        "nome": "Maria",
        "sobrenome": "da Silva-Souza",
        "cpf": "529.982.247-25",
        "data_de_nascimento": "15/03/1990",
        "sexo": "Feminino",
        "email": "maria@exemplo.com",
        "telefone": "(11) 98765-4321",
        "cep": "01001-000",
        "estado": "sp",
        "cidade": "São Paulo",
        "rua": "Praça da Sé",
        "numero": "1",
        "bairro": "Sé"
    }
    dados.update(alteracoes)
    return dados


def data_com_idade(anos, dias_a_mais=0):
    # Data de nascimento de quem faz "anos" hoje (dias_a_mais > 0 = ainda não fez)
    hoje = datetime.today()
    data = hoje.replace(year=hoje.year - anos) if not (hoje.month == 2 and hoje.day == 29) else hoje.replace(year=hoje.year - anos, day=28)
    if dias_a_mais:
        from datetime import timedelta
        data = data + timedelta(days=dias_a_mais)
    return data.strftime("%d/%m/%Y")


class TestCPF(unittest.TestCase):

    def test_cpfs_validos(self):
        for cpf in ("529.982.247-25", "52998224725", "111.444.777-35", " 111 444 777 35 "):
            self.assertTrue(validar_cpf(cpf), cpf)

    def test_cpfs_invalidos(self):
        for cpf in ("529.982.247-24", "111.111.111-11", "123", "", None, "5299822472a", "529.982.247/25"):
            self.assertFalse(validar_cpf(cpf), cpf)

    def test_formatar(self):
        self.assertEqual(formatar_cpf("52998224725"), "529.982.247-25")
        self.assertEqual(formatar_cpf("529.982.247-25"), "529.982.247-25")


class TestSenha(unittest.TestCase):

    def test_senha_valida(self):
        self.assertTrue(senha_valida("Senha@123"))
        self.assertTrue(senha_valida("A1!" + "a" * 61))  # 64 caracteres

    def test_senha_invalida(self):
        for senha in ("Sen@1", "senha@123", "Senha@abc", "Senha1234", "A1!" + "a" * 62):
            self.assertFalse(senha_valida(senha), senha)

    def test_ordem_e_mensagens(self):
        casos = [
            (("", "", "aceito"), "senha", "Informe uma senha."),
            (("fraca", "fraca", "aceito"), "senha", None),
            (("Senha@123", "", "aceito"), "confirmar_senha", "Confirme sua senha."),
            (("Senha@123", "Senha@124", "aceito"), "confirmar_senha", "As senhas não coincidem."),
            (("Senha@123", "Senha@123", None), "termos", None),
        ]
        for argumentos, campo, mensagem in casos:
            with self.assertRaises(ErroCadastro) as contexto:
                validar_senha_e_termos(*argumentos)
            self.assertEqual(contexto.exception.campo, campo)
            if mensagem:
                self.assertEqual(contexto.exception.mensagem, mensagem)

        validar_senha_e_termos("Senha@123", "Senha@123", "aceito")


class TestDadosPessoais(unittest.TestCase):

    def assertErro(self, campo, **alteracoes):
        with self.assertRaises(ErroCadastro) as contexto:
            validar_dados_pessoais(dados_validos(**alteracoes), CAMPOS)
        self.assertEqual(contexto.exception.campo, campo)
        return contexto.exception.mensagem

    def test_dados_validos_padronizados(self):
        dados = dados_validos(cpf="52998224725", telefone="11987654321", cep="01001000")
        data = validar_dados_pessoais(dados, CAMPOS)

        self.assertEqual(data, datetime(1990, 3, 15))
        self.assertEqual(dados["cpf"], "529.982.247-25")
        self.assertEqual(dados["telefone"], "(11) 98765-4321")
        self.assertEqual(dados["cep"], "01001-000")
        self.assertEqual(dados["estado"], "SP")

    def test_telefone_fixo(self):
        dados = dados_validos(telefone="1132654321")
        validar_dados_pessoais(dados, CAMPOS)
        self.assertEqual(dados["telefone"], "(11) 3265-4321")

    def test_obrigatorio_na_ordem_do_formulario(self):
        mensagem = self.assertErro("nome", nome="", cpf="")
        self.assertEqual(mensagem, "O campo Nome é obrigatório.")

    def test_tamanho_maximo(self):
        mensagem = self.assertErro("nome", nome="a" * 101)
        self.assertEqual(mensagem, "O campo Nome deve ter no máximo 100 caracteres.")

    def test_nome_so_letras(self):
        self.assertErro("sobrenome", sobrenome="Silva2")
        self.assertErro("nome", nome="Ma  ria")

    def test_cpf(self):
        self.assertEqual(self.assertErro("cpf", cpf="529.982.247-24"), "CPF inválido.")

    def test_data_de_nascimento(self):
        self.assertEqual(self.assertErro("data_de_nascimento", data_de_nascimento="31/02/1990"), "Data de nascimento inválida.")
        self.assertErro("data_de_nascimento", data_de_nascimento="1990-03-15")
        self.assertEqual(
            self.assertErro("data_de_nascimento", data_de_nascimento=data_com_idade(18, dias_a_mais=1)),
            "Idade deve estar entre 18 e 100 anos."
        )
        self.assertErro("data_de_nascimento", data_de_nascimento=data_com_idade(101))

        validar_dados_pessoais(dados_validos(data_de_nascimento=data_com_idade(18)), CAMPOS)
        validar_dados_pessoais(dados_validos(data_de_nascimento=data_com_idade(100)), CAMPOS)

    def test_sexo(self):
        self.assertErro("sexo", sexo="Outro")

    def test_email(self):
        for email in ("maria", "maria@exemplo", "ma ria@exemplo.com"):
            self.assertErro("email", email=email)

    def test_telefone(self):
        for telefone in ("(11) 8765-432", "(01) 98765-4321", "(11) 88765-4321", "119876543210"):
            self.assertEqual(
                self.assertErro("telefone", telefone=telefone),
                "Telefone inválido. Use o formato (00) 00000-0000."
            )

    def test_cep(self):
        for cep in ("0100-000", "01001-00a", "010010000"):
            self.assertEqual(self.assertErro("cep", cep=cep), "CEP inválido. Use o formato 00000-000.")

    def test_uf(self):
        self.assertEqual(self.assertErro("estado", estado="XX"), "UF inválida.")

    def test_sem_cpf_na_lista_de_campos(self):
        # A edição do próprio perfil não envia o CPF: ele não é obrigatório nem validado
        campos_sem_cpf = [c for c in CAMPOS if c[0] != "cpf"]
        dados = dados_validos()
        del dados["cpf"]
        validar_dados_pessoais(dados, campos_sem_cpf)
        self.assertNotIn("cpf", dados)


if __name__ == "__main__":
    unittest.main()
