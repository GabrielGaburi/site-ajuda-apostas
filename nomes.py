"""Como o nome de cada pessoa aparece para os outros no fórum.

Não depende do Flask nem do banco, para poder ser testado sozinho (testes/test_nomes.py).
"""


def nome_publico(nome, sobrenome, tipo="usuario"):
    """Usuário comum aparece só com o primeiro nome e a inicial do sobrenome ("Maria S.").

    O fórum é de apoio a pessoas afetadas por apostas: o nome completo de quem participa
    permitiria identificar quem tem o problema. Profissionais e administradores aparecem
    com o nome completo, porque a identidade deles é pública."""

    nome = (nome or "").strip()
    sobrenome = (sobrenome or "").strip()

    if tipo in ("profissional", "admin"):
        return f"{nome} {sobrenome}".strip() or "Participante"

    # Conta excluída pelo próprio usuário (ver excluir_minha_conta)
    if nome == "Usuário" and sobrenome == "removido":
        return "Usuário removido"

    primeiro_nome = nome.split()[0] if nome else "Participante"

    if not sobrenome:
        return primeiro_nome

    return f"{primeiro_nome} {sobrenome[0].upper()}."
