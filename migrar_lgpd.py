"""Adiciona à tabela usuarios as colunas usadas pelos recursos de LGPD.

Uso (uma vez, com o .env configurado):
    .venv\\Scripts\\python migrar_lgpd.py

É seguro rodar mais de uma vez: só cria o que ainda não existe.
"""
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv(override=True)

COLUNAS = {
    # Consentimento específico para dados de saúde (chatbot, atendimento e fórum)
    "consentimento_saude_em": "DATETIME NULL",
    "consentimento_saude_versao": "VARCHAR(30) NULL",
    # Preenchida quando a conta é excluída (os dados pessoais são anonimizados)
    "excluido_em": "DATETIME NULL",
}


def main():
    conexao = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'usuarios'
            """
        )
        existentes = {linha[0] for linha in cursor.fetchall()}

        for nome, definicao in COLUNAS.items():
            if nome in existentes:
                print(f"já existe: {nome}")
                continue

            cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {nome} {definicao}")
            print(f"criada: {nome}")

        conexao.commit()

    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    main()
