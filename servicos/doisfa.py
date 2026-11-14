"""Código de verificação em duas etapas (2FA) por e-mail."""

import hashlib
import secrets

from flask import current_app
from flask_mail import Message

from db import get_db_connection
from extensoes import mail


def gerar_codigo_2fa():
    return f"{secrets.randbelow(1000000):06d}"


def enviar_codigo_2fa(email, codigo):
    try:
        msg = Message(
            subject="Código de verificação - Apoio & Consciência",
            recipients=[email]
        )

        msg.body = f"""
Olá!

Recebemos uma tentativa de login na sua conta do Apoio & Consciência.

Seu código de verificação é: {codigo}

Esse código é temporário e deve ser utilizado somente por você.
Se não foi você quem tentou entrar, ignore este e-mail.

Atenciosamente,
Equipe Apoio & Consciência
"""

        mail.send(msg)
        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar código de verificação 2FA.")
        return False


def salvar_codigo_2fa(usuario_id, codigo):
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        codigo_hash = hashlib.sha256(codigo.encode("utf-8")).hexdigest()

        cursor.execute("""
            INSERT INTO codigos_2fa
                (usuario_id, codigo_hash, expira_em, tentativas)
            VALUES
                (%s, %s, DATE_ADD(NOW(), INTERVAL 5 MINUTE), 0)
            ON DUPLICATE KEY UPDATE
                codigo_hash = VALUES(codigo_hash),
                expira_em = DATE_ADD(NOW(), INTERVAL 5 MINUTE),
                tentativas = 0,
                criado_em = NOW()
        """, (usuario_id, codigo_hash))

        conexao.commit()
        return True

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao salvar código 2FA.")
        return False

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


def preparar_codigo_2fa(usuario_id, email):
    codigo = gerar_codigo_2fa()

    if not salvar_codigo_2fa(usuario_id, codigo):
        return False

    if not enviar_codigo_2fa(email, codigo):
        return False

    return True


def validar_codigo_2fa(usuario_id, codigo):
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # A tentativa é reservada ANTES de comparar, em uma só instrução. Ler as tentativas,
        # comparar e só depois incrementar deixava requisições simultâneas passarem todas
        # do limite de 5 (40 tentativas ao mesmo tempo eram todas avaliadas)
        cursor.execute("""
            UPDATE codigos_2fa
            SET tentativas = tentativas + 1
            WHERE usuario_id = %s
              AND tentativas < 5
              AND expira_em > NOW()
        """, (usuario_id,))

        reservou = cursor.rowcount == 1

        conexao.commit()

        if not reservou:
            return False

        cursor.execute("""
            SELECT codigo_hash
            FROM codigos_2fa
            WHERE usuario_id = %s
        """, (usuario_id,))

        registro = cursor.fetchone()

        if not registro:
            return False

        codigo_hash = hashlib.sha256(
            codigo.strip().encode("utf-8")
        ).hexdigest()

        if not secrets.compare_digest(
            codigo_hash, registro["codigo_hash"]
        ):
            return False

        cursor.execute("""
            DELETE FROM codigos_2fa
            WHERE usuario_id = %s
        """, (usuario_id,))

        conexao.commit()
        return True

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao validar código 2FA.")
        return False

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
