"""LGPD: dados do controlador, exportação dos dados da conta e apagamento de conversas."""

import os
from datetime import date, datetime


# Dados do controlador, preenchidos no .env (LEGAL_*).
# Enquanto algum estiver como "[PREENCHER ...]", as páginas mostram o aviso de rascunho.
def carregar_dados_legais():
    campos = {
        "controlador": ("LEGAL_CONTROLADOR", "[PREENCHER: nome ou razão social]"),
        "documento": ("LEGAL_DOCUMENTO", "[PREENCHER: CPF ou CNPJ]"),
        "endereco": ("LEGAL_ENDERECO", "[PREENCHER: endereço]"),
        "encarregado": ("LEGAL_ENCARREGADO", "[PREENCHER: nome do encarregado (DPO)]"),
        "email_privacidade": ("LEGAL_EMAIL_PRIVACIDADE", "[PREENCHER: e-mail de privacidade]"),
        "email_contato": ("LEGAL_EMAIL_CONTATO", "[PREENCHER: e-mail de contato]"),
        "atualizacao": ("LEGAL_ATUALIZACAO", "[PREENCHER: data da última atualização]"),
    }

    dados = {
        chave: (os.getenv(variavel) or padrao).strip()
        for chave, (variavel, padrao) in campos.items()
    }

    dados["pendente"] = any(valor.startswith("[PREENCHER") for valor in dados.values())

    return dados


LEGAL = carregar_dados_legais()


MENSAGEM_REMOVIDA = "[mensagem removida pelo autor]"


ROTULOS_DADOS_CONTA = {
    "nome": "Nome", "sobrenome": "Sobrenome", "email": "E-mail", "telefone": "Telefone",
    "cpf": "CPF", "data_nascimento": "Data de nascimento", "cep": "CEP", "estado": "Estado",
    "cidade": "Cidade", "bairro": "Bairro", "rua": "Rua", "numero": "Número",
    "complemento": "Complemento", "tipo": "Tipo de conta", "status": "Situação da conta",
    "data_cadastro": "Cadastro feito em", "crp": "CRP", "uf_crp": "UF do CRP",
    "especialidade": "Especialidade", "status_aprovacao": "Situação da aprovação",
}


# Campos do cadastro que entram no arquivo "Baixar meus dados"
CAMPOS_EXPORTAVEIS = set(ROTULOS_DADOS_CONTA) | {
    "sexo", "email_confirmado", "termos_aceitos", "termos_aceitos_em", "termos_versao",
    "experiencia", "faculdade", "pos", "biografia", "data_aprovacao", "motivo_recusa",
}


NOMES_REMETENTE = {"usuario": "Você", "bot": "Apoio Virtual", "profissional": "Profissional"}


def montar_texto_meus_dados(conta, profissional, atendimentos, mensagens_chat, topicos, mensagens_forum):
    """Monta o arquivo de texto com os dados do usuário, legível por qualquer pessoa."""

    def valor_legivel(valor):
        if valor is None or valor == "":
            return "(não informado)"
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M")
        if isinstance(valor, date):
            return valor.strftime("%d/%m/%Y")
        return str(valor)

    def campos_visiveis(registro):
        # Só sai o que está em CAMPOS_EXPORTAVEIS. Uma lista de campos proibidos deixaria
        # passar qualquer coluna nova ou interna (como o segredo do autenticador)
        linhas = []
        for chave, valor in (registro or {}).items():
            if chave not in CAMPOS_EXPORTAVEIS:
                continue
            rotulo = ROTULOS_DADOS_CONTA.get(chave, chave.replace("_", " ").capitalize())
            linhas.append(f"{rotulo}: {valor_legivel(valor)}")
        return linhas

    linhas = [
        "MEUS DADOS - APOIO & CONSCIÊNCIA",
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        "",
        "=" * 50,
        "DADOS DO CADASTRO",
        "=" * 50,
        *campos_visiveis(conta),
        "",
    ]

    if profissional:
        linhas += ["=" * 50, "DADOS PROFISSIONAIS", "=" * 50, *campos_visiveis(profissional), ""]

    linhas += ["=" * 50, "CONVERSAS COM O APOIO VIRTUAL", "=" * 50]

    if not atendimentos:
        linhas.append("Nenhuma conversa registrada.")

    for atendimento in atendimentos:
        linhas += ["", f"Conversa iniciada em {valor_legivel(atendimento['data_inicio'])}"]

        for msg in mensagens_chat:
            if msg["atendimento_id"] == atendimento["id"]:
                autor = NOMES_REMETENTE.get(msg["remetente"], msg["remetente"])
                linhas.append(f"  [{valor_legivel(msg['data_envio'])}] {autor}: {msg['mensagem']}")

    linhas += ["", "=" * 50, "FÓRUM", "=" * 50]

    if not topicos and not mensagens_forum:
        linhas.append("Nenhuma participação registrada.")

    if topicos:
        linhas += ["", "Tópicos que você criou:"]
        for topico in topicos:
            linhas.append(f"  - {topico['titulo']} ({valor_legivel(topico['data_criacao'])})")

    if mensagens_forum:
        linhas += ["", "Mensagens que você escreveu:"]
        for msg in mensagens_forum:
            linhas.append(f"  [{valor_legivel(msg['data_criacao'])}] {msg['mensagem']}")

    return "\r\n".join(linhas) + "\r\n"


def apagar_conversas_do_usuario(cursor, usuario_id):
    cursor.execute(
        """
        DELETE m
        FROM mensagens_atendimento m
        INNER JOIN atendimentos_chatbot a
            ON a.id = m.atendimento_id
        WHERE a.usuario_id = %s
        """,
        (usuario_id,)
    )

    cursor.execute(
        "DELETE FROM atendimentos_chatbot WHERE usuario_id = %s",
        (usuario_id,)
    )
