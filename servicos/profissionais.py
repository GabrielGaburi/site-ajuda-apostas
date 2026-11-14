"""Regras do cadastro e da edição de profissionais: regiões do CRP, especialidades e validações."""

import re

from moderacao import verificar_conteudo_proibido
from servicos.cadastro import CAMPOS_CADASTRO_USUARIO
from validacoes import ErroCadastro


# Região do CRP (dois primeiros dígitos) -> UFs atendidas por ela
REGIOES_CRP = {
    "01": ["DF"], "02": ["PE"], "03": ["BA"], "04": ["MG"], "05": ["RJ"], "06": ["SP"],
    "07": ["RS"], "08": ["PR"], "09": ["GO"], "10": ["PA", "AP"], "11": ["CE"], "12": ["SC"],
    "13": ["PB"], "14": ["MS"], "15": ["AL"], "16": ["ES"], "17": ["RN"], "18": ["MT"],
    "19": ["SE"], "20": ["AM", "RR"], "21": ["PI"], "22": ["MA"], "23": ["TO"], "24": ["RO", "AC"]
}


# Campos do formulário do profissional, na ordem em que aparecem
CAMPOS_CADASTRO_PROFISSIONAL = CAMPOS_CADASTRO_USUARIO + [
    ("crp", "CRP"),
    ("uf_crp", "UF do CRP"),
    ("experiencia", "Experiência"),
    ("especialidade", "Especialidade"),
    ("faculdade", "Instituição de ensino"),
    ("pos", "Pós-graduação"),
    ("biografia", "Biografia")
]


# Campos que o profissional pode alterar em editar_perfil_profissional, na ordem do formulário.
# Nome, CPF, data de nascimento, sexo, email e CRP ficam de fora: foram conferidos pelo admin na aprovação.
CAMPOS_EDITAR_PERFIL_PROFISSIONAL = [
    (campo, nome_campo)
    for campo, nome_campo in CAMPOS_CADASTRO_PROFISSIONAL
    if campo in {
        "telefone", "cep", "estado", "cidade", "rua", "numero", "bairro",
        "experiencia", "especialidade", "faculdade", "pos", "biografia"
    }
]


# Mesma mensagem para cadastro novo, email ou CPF já cadastrados,
# para a tela não revelar quem tem conta no site
MENSAGEM_CADASTRO_PROFISSIONAL_RECEBIDO = (
    "Cadastro recebido! Se os dados estiverem corretos, seu perfil será analisado "
    "por um administrador e você receberá um e-mail com a decisão."
)


OPCOES_ESPECIALIDADE = [
    "Psicologia Clínica",
    "Terapia Cognitivo-Comportamental",
    "Dependência Química",
    "Dependência em Jogos",
    "Ansiedade",
    "Depressão",
    "Relacionamentos",
    "Infantil",
    "Casais",
    "Outro"
]


def validar_dados_profissionais(dados):
    # Valida e padroniza os campos que só o cadastro de profissional tem.
    # Levanta ErroCadastro no primeiro erro.

    # CRP (00/000000) e a UF, que depende da região do CRP.
    # A UF é conferida aqui porque o campo do formulário pode ser alterado no navegador.
    crp_partes = re.fullmatch(r"(\d{2})/?(\d{3,6})", dados["crp"])
    if not crp_partes or crp_partes.group(1) not in REGIOES_CRP:
        raise ErroCadastro("crp", "CRP inválido. Use o formato 00/000000, com uma região existente.")

    dados["crp"] = f"{crp_partes.group(1)}/{crp_partes.group(2)}"

    dados["uf_crp"] = dados["uf_crp"].upper()
    if dados["uf_crp"] not in REGIOES_CRP[crp_partes.group(1)]:
        raise ErroCadastro("uf_crp", "Selecione a UF correspondente à região do CRP.")

    validar_atuacao_profissional(dados)


def validar_atuacao_profissional(dados):
    # Experiência, especialidade, formação e biografia (cadastro e edição do perfil do profissional).
    # Levanta ErroCadastro no primeiro erro.

    # Experiência em anos (a coluna é INT)
    if not dados["experiencia"].isdigit() or int(dados["experiencia"]) > 60:
        raise ErroCadastro("experiencia", "Informe a experiência em anos, de 0 a 60.")

    if dados["especialidade"] not in OPCOES_ESPECIALIDADE:
        raise ErroCadastro("especialidade", "Selecione uma especialidade da lista.")

    # Formação e biografia aparecem no perfil público: passam pela mesma moderação do fórum
    for campo, nome_campo in (("faculdade", "Instituição de ensino"), ("pos", "Pós-graduação"), ("biografia", "Biografia")):
        if verificar_conteudo_proibido(dados[campo]):
            raise ErroCadastro(
                campo,
                f"O campo {nome_campo} contém linguagem ofensiva ou conteúdo que promove apostas."
            )
