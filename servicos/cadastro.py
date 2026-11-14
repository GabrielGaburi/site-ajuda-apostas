"""Cadastro de contas: campos dos formulários, busca de conta existente e criação do usuário."""

import re

from config import TERMOS_VERSAO


# Campos do formulário, na ordem em que aparecem (a validação segue essa ordem)
CAMPOS_CADASTRO_USUARIO = [
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


# Campos que o próprio usuário pode alterar em editar_meu_perfil.
# O CPF fica de fora: identifica a conta (é único no banco) e só o admin corrige,
# como no perfil do profissional.
CAMPOS_EDITAR_MEU_PERFIL = [
    (campo, nome_campo)
    for campo, nome_campo in CAMPOS_CADASTRO_USUARIO
    if campo != "cpf"
]


# Mesma mensagem para cadastro novo, email ou CPF já cadastrados,
# para a tela não revelar quem tem conta no site
MENSAGEM_CADASTRO_RECEBIDO = (
    "Cadastro recebido! Se os dados estiverem corretos, enviamos um e-mail para "
    "confirmar sua conta. Não recebeu? Use \"Reenviar e-mail de confirmação\" na tela de login."
)


def buscar_conta_existente(cursor, email, cpf):
    # Procura uma conta com o mesmo email ou CPF (cadastros de usuário e de profissional).
    # O CPF é comparado só pelos dígitos, porque cadastros antigos podem estar sem máscara
    cursor.execute(
        """
        SELECT email, tipo, email_confirmado
        FROM usuarios
        WHERE email = %s
           OR REPLACE(REPLACE(cpf, '.', ''), '-', '') = %s
        ORDER BY email = %s DESC
        LIMIT 1
        """,
        (email, re.sub(r"\D", "", cpf), email)
    )

    return cursor.fetchone()


def inserir_usuario(cursor, dados, data_nascimento, senha_hash, tipo):
    # Insere a conta na tabela usuarios e devolve o ID criado (sem commit)
    cursor.execute(
        """
        INSERT INTO usuarios (
            nome,
            sobrenome,
            cpf,
            data_nascimento,
            sexo,
            email,
            telefone,
            cep,
            estado,
            cidade,
            rua,
            numero,
            bairro,
            senha_hash,
            tipo,
            status,
            email_confirmado,
            termos_aceitos,
            termos_aceitos_em,
            termos_versao
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, NOW(), %s
        )
        """,
        (
            dados["nome"],
            dados["sobrenome"],
            dados["cpf"],
            data_nascimento.strftime("%Y-%m-%d"),
            dados["sexo"],
            dados["email"],
            dados["telefone"],
            dados["cep"],
            dados["estado"],
            dados["cidade"],
            dados["rua"],
            dados["numero"],
            dados["bairro"],
            senha_hash,
            tipo,
            "ativo",
            False,
            True,
            TERMOS_VERSAO
        )
    )

    return cursor.lastrowid
