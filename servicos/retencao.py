"""Retenção de dados (LGPD): apaga conversas antigas conforme os prazos do .env."""

import os

from db import get_db_connection


# Prazos em dias sem atividade; ajuste no .env conforme a Política de Privacidade
RETENCAO_CONVERSAS_DIAS = int(os.getenv("RETENCAO_CONVERSAS_DIAS", "365"))


RETENCAO_CONVERSAS_VISITANTES_DIAS = int(os.getenv("RETENCAO_CONVERSAS_VISITANTES_DIAS", "30"))


def apagar_conversas_antigas(cursor, visitantes, dias):
    condicao_usuario = "a.usuario_id IS NULL" if visitantes else "a.usuario_id IS NOT NULL"

    cursor.execute(
        f"""
        SELECT a.id
        FROM atendimentos_chatbot a
        WHERE a.status IN ('ia', 'finalizado')
          AND {condicao_usuario}
          AND COALESCE(
                (SELECT MAX(m.data_envio)
                 FROM mensagens_atendimento m
                 WHERE m.atendimento_id = a.id),
                a.data_inicio
              ) < DATE_SUB(NOW(), INTERVAL %s DAY)
        """,
        (dias,)
    )

    ids = [linha[0] for linha in cursor.fetchall()]

    for inicio in range(0, len(ids), 500):
        lote = ids[inicio:inicio + 500]
        marcadores = ", ".join(["%s"] * len(lote))

        cursor.execute(
            f"DELETE FROM mensagens_atendimento WHERE atendimento_id IN ({marcadores})",
            lote
        )
        cursor.execute(
            f"DELETE FROM atendimentos_chatbot WHERE id IN ({marcadores})",
            lote
        )

    return len(ids)


def aplicar_retencao():
    """Apaga conversas antigas e códigos expirados. Devolve as quantidades apagadas."""

    conexao = get_db_connection()
    cursor = conexao.cursor()

    try:
        resultado = {
            "conversas_usuarios": apagar_conversas_antigas(cursor, False, RETENCAO_CONVERSAS_DIAS),
            "conversas_visitantes": apagar_conversas_antigas(cursor, True, RETENCAO_CONVERSAS_VISITANTES_DIAS),
        }

        cursor.execute("DELETE FROM codigos_2fa WHERE expira_em < NOW()")
        resultado["codigos_2fa"] = cursor.rowcount

        cursor.execute("DELETE FROM tokens_recuperacao_senha WHERE expira_em < NOW()")
        resultado["tokens_senha"] = cursor.rowcount

        conexao.commit()

        return resultado

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()
