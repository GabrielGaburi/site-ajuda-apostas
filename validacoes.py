# Validações compartilhadas pelos cadastros de usuário e de profissional.
# Não depende do Flask nem do banco, para poder ser testado sozinho (testes/test_validacoes.py).

import re
from datetime import datetime


def validar_cpf(cpf):

    # Mantém só os dígitos; letras ou outros símbolos invalidam o CPF
    if not re.fullmatch(r"[\d.\-\s]+", cpf or ""):
        return False

    cpf = re.sub(r"\D", "", cpf)

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    soma = 0

    for i in range(9):
        soma += int(cpf[i]) * (10 - i)

    resto = (soma * 10) % 11

    if resto == 10:
        resto = 0

    if resto != int(cpf[9]):
        return False


    soma = 0

    for i in range(10):
        soma += int(cpf[i]) * (11 - i)

    resto = (soma * 10) % 11

    if resto == 10:
        resto = 0

    if resto != int(cpf[10]):
        return False


    return True


def formatar_cpf(cpf):
    # Padroniza o CPF como 000.000.000-00 antes de salvar ou comparar
    digitos = re.sub(r"\D", "", cpf or "")
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def senha_valida(senha):
    if len(senha) < 8 or len(senha) > 64:
        return False
    
    if not re.search(r"[A-Z]", senha):  # letra maiúscula
        return False
    
    if not re.search(r"[0-9]", senha):  # número
        return False
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):  # especial
        return False

    return True


# Tamanho máximo de cada campo, igual às colunas das tabelas usuarios e profissionais
# (a biografia é TEXT; o limite dela é só para manter o perfil curto)
TAMANHO_MAXIMO_CAMPOS = {
    "nome": 100,
    "sobrenome": 100,
    "email": 150,
    "rua": 150,
    "numero": 20,
    "bairro": 100,
    "cidade": 100,
    "especialidade": 100,
    "faculdade": 150,
    "pos": 150,
    "biografia": 1000
}

OPCOES_SEXO = {"Masculino", "Feminino", "Prefiro não informar"}

UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}

class ErroCadastro(Exception):
    # Erro de validação de um campo do formulário de cadastro
    def __init__(self, campo, mensagem):
        super().__init__(mensagem)
        self.campo = campo
        self.mensagem = mensagem


def validar_campos_obrigatorios(dados, campos):
    # Campos obrigatórios e tamanho máximo, na ordem do formulário
    for campo, nome_campo in campos:
        if not dados[campo]:
            raise ErroCadastro(campo, f"O campo {nome_campo} é obrigatório.")

        limite = TAMANHO_MAXIMO_CAMPOS.get(campo)
        if limite and len(dados[campo]) > limite:
            raise ErroCadastro(campo, f"O campo {nome_campo} deve ter no máximo {limite} caracteres.")


def validar_dados_pessoais(dados, campos):
    # Valida e padroniza os dados comuns aos cadastros de usuário e de profissional,
    # na ordem do formulário. Levanta ErroCadastro no primeiro erro e
    # devolve a data de nascimento já convertida.

    validar_campos_obrigatorios(dados, campos)

    # Nome e sobrenome (letras, espaços, apóstrofo e hífen)
    for campo, nome_campo in (("nome", "Nome"), ("sobrenome", "Sobrenome")):
        if not re.fullmatch(r"[^\W\d_]+(?:[ '\-][^\W\d_]+)*", dados[campo]):
            raise ErroCadastro(campo, f"O campo {nome_campo} deve conter apenas letras.")

    # CPF, salvo sempre no mesmo formato para o UNIQUE do banco funcionar
    # (a edição do próprio perfil não envia o CPF, que não pode ser alterado lá)
    if any(campo == "cpf" for campo, _ in campos):
        if not validar_cpf(dados["cpf"]):
            raise ErroCadastro("cpf", "CPF inválido.")

        dados["cpf"] = formatar_cpf(dados["cpf"])

    # Data de nascimento
    try:
        data_nascimento = datetime.strptime(dados["data_de_nascimento"], "%d/%m/%Y")
    except ValueError:
        raise ErroCadastro("data_de_nascimento", "Data de nascimento inválida.")

    hoje = datetime.today()
    idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
    if idade < 18 or idade > 100:
        raise ErroCadastro("data_de_nascimento", "Idade deve estar entre 18 e 100 anos.")

    # Sexo (só as opções do formulário)
    if dados["sexo"] not in OPCOES_SEXO:
        raise ErroCadastro("sexo", "Selecione uma opção válida.")

    # Email
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", dados["email"]):
        raise ErroCadastro("email", "Digite um e-mail válido.")

    validar_telefone_e_endereco(dados)

    return data_nascimento


def validar_telefone_e_endereco(dados):
    # Valida e padroniza telefone, CEP e UF (cadastros e edições de perfil).
    # Os campos já devem ter passado por validar_campos_obrigatorios.

    # Telefone: DDD + 8 dígitos (fixo) ou 9 dígitos (celular), salvo sempre no mesmo formato
    telefone_digitos = re.sub(r"\D", "", dados["telefone"])
    if (
        len(telefone_digitos) not in (10, 11)
        or telefone_digitos[0] == "0"
        or (len(telefone_digitos) == 11 and telefone_digitos[2] != "9")
    ):
        raise ErroCadastro("telefone", "Telefone inválido. Use o formato (00) 00000-0000.")

    if len(telefone_digitos) == 11:
        dados["telefone"] = f"({telefone_digitos[:2]}) {telefone_digitos[2:7]}-{telefone_digitos[7:]}"
    else:
        dados["telefone"] = f"({telefone_digitos[:2]}) {telefone_digitos[2:6]}-{telefone_digitos[6:]}"

    # CEP no formato 00000-000
    cep_digitos = re.sub(r"\D", "", dados["cep"])
    if len(cep_digitos) != 8 or not re.fullmatch(r"[\d\-\s]+", dados["cep"]):
        raise ErroCadastro("cep", "CEP inválido. Use o formato 00000-000.")

    dados["cep"] = f"{cep_digitos[:5]}-{cep_digitos[5:]}"

    # UF
    dados["estado"] = dados["estado"].upper()
    if dados["estado"] not in UFS_VALIDAS:
        raise ErroCadastro("estado", "UF inválida.")


def validar_senha_e_termos(senha, confirmar_senha, termos):
    # Validações finais comuns aos dois cadastros
    if not senha:
        raise ErroCadastro("senha", "Informe uma senha.")

    if not senha_valida(senha):
        raise ErroCadastro("senha", "A senha deve ter entre 8 e 64 caracteres, conter letra maiúscula, número e caractere especial.")

    if not confirmar_senha:
        raise ErroCadastro("confirmar_senha", "Confirme sua senha.")

    if senha != confirmar_senha:
        raise ErroCadastro("confirmar_senha", "As senhas não coincidem.")

    if termos != "aceito":
        raise ErroCadastro("termos", "Você deve aceitar os Termos de Uso e a Política de Privacidade.")
