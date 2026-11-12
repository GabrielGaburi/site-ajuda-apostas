"""Envio de e-mails (cadastro, confirmação, recuperação de senha, aprovação...)."""

import hashlib
import os
import secrets

from flask import current_app, url_for
from flask_mail import Message
from markupsafe import escape

from config import BASE_URL
from db import get_db_connection
from extensoes import mail
from servicos.tokens import serializer


def url_externa(endpoint, **valores):
    if not BASE_URL:
        current_app.logger.warning("BASE_URL não definida; usando o Host da requisição no link.")
        return url_for(endpoint, _external=True, **valores)

    return BASE_URL + url_for(endpoint, **valores)


def _envolver_email_html(conteudo_interno):
    # Skeleton HTML compartilhado por todos os emails do site (DOCTYPE, head,
    # estilo do body e o cartão branco externo). Cada email só monta o que
    # vai dentro do cartão (cabeçalho, conteúdo, rodapé) e passa aqui.
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
</head>
<body style="
    margin:0;
    padding:0;
    background-color:#f4f6f9;
    font-family:Arial, Helvetica, sans-serif;
">

    <div style="
        max-width:600px;
        margin:40px auto;
        background:#ffffff;
        border-radius:16px;
        overflow:hidden;
        box-shadow:0 8px 25px rgba(0,0,0,0.08);
    ">

{conteudo_interno}

    </div>

</body>
</html>
    """


def _montar_e_enviar_email(destinatario, assunto, texto_simples, conteudo_interno_html):
    # Monta a Message do Flask-Mail e envia. Fica fora do try/except de cada
    # enviar_email_* para cada função manter sua própria mensagem de log e
    # seu próprio tratamento (ex.: rollback de uma transação em andamento).
    msg = Message(
        subject=assunto,
        recipients=[destinatario],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )

    msg.body = texto_simples
    msg.html = _envolver_email_html(conteudo_interno_html)

    mail.send(msg)


def enviar_email_cadastro_profissional(email):
    try:

        # O profissional também confirma o email: o admin só consegue
        # aprovar o cadastro depois disso (ver aprovar_profissional)
        token = serializer.dumps(email, salt='confirmacao-email')
        link = url_externa('confirmar_email', token=token)

        texto = f"""
Olá!

Seu cadastro profissional no Apoio & Consciência foi recebido com sucesso.

Antes da análise, confirme seu e-mail acessando o link abaixo (válido por 1 hora):

{link}

Depois da confirmação, seu perfil será analisado por um administrador.
Você receberá uma nova mensagem por e-mail quando houver uma decisão sobre o seu cadastro.

Se você não fez este cadastro, ignore esta mensagem.

Atenciosamente,
Equipe Apoio & Consciência
        """

        conteudo = f"""
        <div style="
            background:linear-gradient(135deg, #1d3557, #457b9d);
            padding:30px;
            text-align:center;
            color:white;
        ">

            <h1 style="margin:0; font-size:28px;">
                Apoio &amp; Consciência
            </h1>

            <p style="
                margin-top:8px;
                font-size:15px;
                opacity:0.9;
            ">
                Cadastro profissional
            </p>

        </div>

        <div style="
            padding:40px 30px;
            color:#333;
        ">

            <h2 style="
                color:#1d3557;
                margin-top:0;
                text-align:center;
            ">
                Cadastro recebido
            </h2>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Seu cadastro profissional no
                <strong>Apoio &amp; Consciência</strong>
                foi recebido com sucesso.
            </p>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Antes da análise, confirme seu e-mail clicando no botão abaixo
                (o link vale por 1 hora):
            </p>

            <div style="text-align:center; margin:30px 0;">
                <a href="{link}" style="
                    background:linear-gradient(135deg, #198754, #20c997);
                    color:white;
                    padding:14px 30px;
                    text-decoration:none;
                    border-radius:10px;
                    display:inline-block;
                    font-size:16px;
                    font-weight:bold;
                ">
                    Confirmar e-mail
                </a>
            </div>

            <p style="
                font-size:14px;
                color:#666;
                text-align:center;
                word-break:break-all;
            ">
                Se o botão não funcionar, copie e cole este link no navegador:<br>
                {link}
            </p>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Depois da confirmação, seu perfil será analisado por um administrador.
                Você receberá uma nova mensagem por e-mail quando
                houver uma decisão sobre o seu cadastro.
            </p>

        </div>

        <div style="
            background:#f8f9fa;
            padding:20px;
            text-align:center;
            font-size:13px;
            color:#6c757d;
            border-top:1px solid #e9ecef;
        ">
            Se você não fez este cadastro, ignore esta mensagem.<br>
            Equipe Apoio &amp; Consciência
        </div>
        """

        _montar_e_enviar_email(
            email,
            'Cadastro recebido - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar email do profissional.")
        return False


def enviar_email_confirmacao_usuario(email):
    try:
        token = serializer.dumps(email, salt='confirmacao-email')
        link = url_externa('confirmar_email', token=token)

        texto = f"""
Confirme seu cadastro acessando o link abaixo:

{link}

Se você não criou essa conta, ignore esta mensagem.
        """

        conteudo = f"""
        <!-- TOPO -->
        <div style="
            background:linear-gradient(135deg, #1d3557, #457b9d);
            padding:30px;
            text-align:center;
            color:white;
        ">
            <h1 style="margin:0; font-size:28px;">
                Apoio & Consciência
            </h1>
            <p style="margin-top:8px; font-size:15px; opacity:0.9;">
                Segurança e cuidado no seu cadastro
            </p>
        </div>

        <!-- CONTEÚDO -->
        <div style="padding:40px 30px; color:#333;">

            <h2 style="
                color:#1d3557;
                margin-top:0;
                text-align:center;
            ">
                Confirme seu cadastro
            </h2>

            <p style="
                font-size:16px;
                line-height:1.6;
                text-align:center;
                color:#555;
            ">
                Obrigado por se cadastrar em nossa plataforma.<br>
                Para ativar sua conta com segurança, confirme seu e-mail clicando no botão abaixo:
            </p>

            <!-- BOTÃO -->
            <div style="text-align:center; margin:35px 0;">
                <a href="{link}" style="
                    background:linear-gradient(135deg, #198754, #20c997);
                    color:white;
                    padding:14px 30px;
                    text-decoration:none;
                    border-radius:10px;
                    display:inline-block;
                    font-size:16px;
                    font-weight:bold;
                    box-shadow:0 4px 12px rgba(25,135,84,0.3);
                ">
                    Confirmar Cadastro
                </a>
            </div>

            <!-- LINK -->
            <p style="
                font-size:14px;
                color:#666;
                text-align:center;
                margin-bottom:8px;
            ">
                Se o botão não funcionar, copie e cole este link no navegador:
            </p>

            <div style="
                background:#f8f9fa;
                border:1px solid #dee2e6;
                padding:12px;
                border-radius:8px;
                word-break:break-all;
                font-size:13px;
                color:#0d6efd;
                text-align:center;
            ">
                {link}
            </div>

        </div>

        <!-- RODAPÉ -->
        <div style="
            background:#f8f9fa;
            padding:20px;
            text-align:center;
            font-size:13px;
            color:#6c757d;
            border-top:1px solid #e9ecef;
        ">
            Se você não criou essa conta, ignore esta mensagem com segurança.<br>
            © Apoio & Consciência
        </div>
        """

        current_app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

        _montar_e_enviar_email(
            email,
            'Confirme seu cadastro - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar email.")
        return False


def enviar_email_conta_existente(email):
    # Enviado quando alguém tenta se cadastrar com o email ou CPF de uma conta que já existe.
    # Assim a tela de cadastro não precisa revelar que a conta existe.
    try:
        link_login = url_externa("login")
        link_senha = url_externa("esqueci_senha")

        texto = f"""
Recebemos uma tentativa de cadastro usando dados que já pertencem à sua conta.

Se foi você, não é preciso criar outra conta. Faça login em:
{link_login}

Esqueceu a senha? Redefina em:
{link_senha}

Se não foi você, ignore esta mensagem. Nenhuma conta nova foi criada.
        """

        conteudo = f"""
        <div style="background:linear-gradient(135deg, #1d3557, #457b9d); padding:30px;
            text-align:center; color:white;">
            <h1 style="margin:0; font-size:28px;">Apoio & Consciência</h1>
        </div>

        <div style="padding:40px 30px; color:#333; text-align:center;">

            <h2 style="color:#1d3557; margin-top:0;">Você já tem uma conta</h2>

            <p style="font-size:16px; line-height:1.6; color:#555;">
                Recebemos uma tentativa de cadastro usando dados que já pertencem à sua conta.<br>
                Se foi você, não é preciso criar outra conta.
            </p>

            <div style="margin:30px 0;">
                <a href="{link_login}" style="background:#0d6efd; color:white; padding:14px 30px;
                    text-decoration:none; border-radius:10px; display:inline-block; font-weight:bold;">
                    Fazer login
                </a>
            </div>

            <p style="font-size:14px; color:#666;">
                Esqueceu a senha? <a href="{link_senha}">Redefina aqui</a>.
            </p>

        </div>

        <div style="background:#f8f9fa; padding:20px; text-align:center; font-size:13px;
            color:#6c757d; border-top:1px solid #e9ecef;">
            Se não foi você, ignore esta mensagem. Nenhuma conta nova foi criada.<br>
            © Apoio & Consciência
        </div>
        """

        _montar_e_enviar_email(
            email,
            'Tentativa de cadastro - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar email de conta existente.")
        return False


def enviar_email_troca_email(usuario_id, email_atual, novo_email):
    # Envia ao novo email o link que confirma a troca (confirmar_novo_email).
    # O token guarda o email atual: depois que a troca acontece, o mesmo link deixa de valer.
    try:
        token = serializer.dumps(
            {"id": usuario_id, "atual": email_atual, "novo": novo_email},
            salt="troca-email"
        )

        link = url_externa("confirmar_novo_email", token=token)

        texto = f"""
Recebemos um pedido para usar este e-mail na sua conta do Apoio & Consciência.

Para confirmar a troca, acesse o link abaixo (válido por 1 hora):

{link}

Se você não pediu essa troca, ignore esta mensagem. Nada será alterado.
        """

        conteudo = f"""
        <div style="background:linear-gradient(135deg, #1d3557, #457b9d); padding:30px;
            text-align:center; color:white;">
            <h1 style="margin:0; font-size:28px;">Apoio & Consciência</h1>
        </div>

        <div style="padding:40px 30px; color:#333; text-align:center;">

            <h2 style="color:#1d3557; margin-top:0;">Confirme seu novo e-mail</h2>

            <p style="font-size:16px; line-height:1.6; color:#555;">
                Recebemos um pedido para usar este e-mail na sua conta.<br>
                Para confirmar a troca, clique no botão abaixo. O link vale por 1 hora.
            </p>

            <div style="margin:30px 0;">
                <a href="{link}" style="background:linear-gradient(135deg, #198754, #20c997); color:white;
                    padding:14px 30px; text-decoration:none; border-radius:10px; display:inline-block;
                    font-weight:bold;">
                    Confirmar novo e-mail
                </a>
            </div>

            <p style="font-size:14px; color:#666; margin-bottom:8px;">
                Se o botão não funcionar, copie e cole este link no navegador:
            </p>

            <div style="background:#f8f9fa; border:1px solid #dee2e6; padding:12px; border-radius:8px;
                word-break:break-all; font-size:13px; color:#0d6efd;">
                {link}
            </div>

        </div>

        <div style="background:#f8f9fa; padding:20px; text-align:center; font-size:13px;
            color:#6c757d; border-top:1px solid #e9ecef;">
            Se você não pediu essa troca, ignore esta mensagem. Nada será alterado.<br>
            © Apoio & Consciência
        </div>
        """

        _montar_e_enviar_email(
            novo_email,
            'Confirme seu novo e-mail - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar email de troca de email.")
        return False


def enviar_email_email_alterado(email_antigo, novo_email):
    # Avisa o email antigo depois da troca, para o dono perceber se não foi ele
    try:
        texto = f"""
O e-mail da sua conta no Apoio & Consciência foi alterado para {novo_email}.

Se foi você, nada precisa ser feito.

Se não foi você, entre em contato com a equipe do site o quanto antes.
        """

        conteudo = f"""
        <div style="background:linear-gradient(135deg, #1d3557, #457b9d); padding:30px;
            text-align:center; color:white;">
            <h1 style="margin:0; font-size:28px;">Apoio & Consciência</h1>
        </div>

        <div style="padding:40px 30px; color:#333; text-align:center;">

            <h2 style="color:#1d3557; margin-top:0;">Seu e-mail foi alterado</h2>

            <p style="font-size:16px; line-height:1.6; color:#555;">
                O e-mail da sua conta foi alterado para <strong>{escape(novo_email)}</strong>.<br>
                Se foi você, nada precisa ser feito.
            </p>

            <p style="font-size:14px; color:#666;">
                Se não foi você, entre em contato com a equipe do site o quanto antes.
            </p>

        </div>

        <div style="background:#f8f9fa; padding:20px; text-align:center; font-size:13px;
            color:#6c757d; border-top:1px solid #e9ecef;">
            © Apoio & Consciência
        </div>
        """

        _montar_e_enviar_email(
            email_antigo,
            'Seu e-mail foi alterado - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar aviso de email alterado.")
        return False


def enviar_email_recuperacao(email):
    
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, email, status
            FROM usuarios
            WHERE LOWER(email) = %s
            """,
            (email.lower(),)
        )

        usuario = cursor.fetchone()

        if not usuario or usuario["status"] != "ativo":
            return False
        
        # Invalida os tokens anteriores ainda não utilizados
        cursor.execute(
            """
            DELETE FROM tokens_recuperacao_senha
            WHERE usuario_id = %s
            """,
            (usuario["id"],)
        )

        # Gera um token aleatório e calcula seu hash
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        cursor.execute(
            """
            INSERT INTO tokens_recuperacao_senha
                (usuario_id, token_hash, expira_em)
            VALUES (
                %s,
                %s,
                DATE_ADD(NOW(), INTERVAL 1 HOUR)
            )
            """,
            (usuario["id"], token_hash)
        )
        
        conexao.commit()


        link = url_externa(
            "redefinir_senha",
            token=token
        )

        texto = f"""
Redefina sua senha acessando o link abaixo:

{link}

Se você não solicitou essa alteração, ignore este email com segurança.
        """

        conteudo = f"""
        <!-- TOPO -->
        <div style="
            background:linear-gradient(135deg, #0d6efd, #3a86ff);
            padding:30px;
            text-align:center;
            color:white;
        ">
            <h1 style="margin:0; font-size:28px;">
                Apoio & Consciência
            </h1>
            <p style="margin-top:8px; font-size:15px; opacity:0.9;">
                Segurança para redefinição da sua conta
            </p>
        </div>

        <!-- CONTEÚDO -->
        <div style="padding:40px 30px; color:#333;">

            <h2 style="
                color:#0d6efd;
                margin-top:0;
                text-align:center;
            ">
                Redefinição de Senha
            </h2>

            <p style="
                font-size:16px;
                line-height:1.6;
                text-align:center;
                color:#555;
            ">
                Recebemos uma solicitação para redefinir sua senha.<br>
                Clique no botão abaixo para criar uma nova senha com segurança:
            </p>

            <!-- BOTÃO -->
            <div style="text-align:center; margin:35px 0;">
                <a href="{link}" style="
                    background:linear-gradient(135deg, #0d6efd, #3a86ff);
                    color:white;
                    padding:14px 30px;
                    text-decoration:none;
                    border-radius:10px;
                    display:inline-block;
                    font-size:16px;
                    font-weight:bold;
                    box-shadow:0 4px 12px rgba(13,110,253,0.3);
                ">
                    Redefinir Senha
                </a>
            </div>

            <!-- LINK -->
            <p style="
                font-size:14px;
                color:#666;
                text-align:center;
                margin-bottom:8px;
            ">
                Se o botão não funcionar, copie e cole este link no navegador:
            </p>

            <div style="
                background:#f8f9fa;
                border:1px solid #dee2e6;
                padding:12px;
                border-radius:8px;
                word-break:break-all;
                font-size:13px;
                color:#0d6efd;
                text-align:center;
            ">
                {link}
            </div>

        </div>

        <!-- ALERTA -->
        <div style="
            margin:0 30px 25px;
            padding:14px;
            background:#fff3cd;
            border:1px solid #ffe69c;
            border-radius:8px;
            color:#856404;
            font-size:14px;
            text-align:center;
        ">
            Se você não solicitou esta redefinição, ignore este email. Sua conta continuará segura.
        </div>

        <!-- RODAPÉ -->
        <div style="
            background:#f8f9fa;
            padding:20px;
            text-align:center;
            font-size:13px;
            color:#6c757d;
            border-top:1px solid #e9ecef;
        ">
            Protegendo seu acesso com responsabilidade.<br>
            © Apoio & Consciência
        </div>
        """

        _montar_e_enviar_email(
            email,
            'Redefinição de senha - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    
    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception("Erro ao enviar email de recuperação.")
        return False

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


def enviar_email_aprovacao(email, nome):
    try:
        texto = f"""
Olá, {nome}.

Temos uma boa notícia!

Seu cadastro profissional na plataforma Apoio & Consciência foi analisado e aprovado pela nossa equipe administrativa.

Sua conta profissional está pronta para ser utilizada.

Agora você pode acessar a plataforma utilizando o e-mail e a senha cadastrados.

Atenciosamente,

Equipe Apoio & Consciência
"""

        conteudo = f"""
        <!-- TOPO -->

        <div style="
            background:linear-gradient(135deg, #1d3557, #457b9d);
            padding:30px;
            text-align:center;
            color:white;
        ">

            <h1 style="
                margin:0;
                font-size:28px;
            ">
                Apoio & Consciência
            </h1>

            <p style="
                margin-top:8px;
                font-size:15px;
                opacity:0.9;
            ">
                Cadastro profissional
            </p>

        </div>


        <!-- CONTEÚDO -->

        <div style="
            padding:40px 30px;
            color:#333;
        ">

            <h2 style="
                color:#198754;
                margin-top:0;
                text-align:center;
            ">
                Cadastro aprovado!
            </h2>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Olá, <strong>{nome}</strong>.
            </p>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Temos uma boa notícia!
            </p>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Seu cadastro profissional na plataforma
                <strong>Apoio & Consciência</strong> foi analisado
                e <strong>aprovado</strong> pela nossa equipe administrativa.
            </p>


            <!-- AVISO -->

            <div style="
                margin:25px 0;
                padding:20px;
                background:#d1e7dd;
                border:1px solid #a3cfbb;
                border-radius:10px;
                text-align:center;
            ">

                <p style="
                    margin:0;
                    font-size:16px;
                    line-height:1.6;
                    color:#0f5132;
                ">
                    Sua conta profissional está pronta para ser utilizada.
                </p>

            </div>


            <p style="
                font-size:15px;
                line-height:1.6;
                color:#555;
                text-align:center;
            ">
                Agora você pode acessar a plataforma utilizando
                o e-mail e a senha cadastrados.
            </p>

        </div>


        <!-- RODAPÉ -->

        <div style="
            background:#f8f9fa;
            padding:20px;
            text-align:center;
            font-size:13px;
            color:#6c757d;
            border-top:1px solid #e9ecef;
        ">

            Equipe Apoio & Consciência<br>

            © Apoio & Consciência

        </div>
        """

        _montar_e_enviar_email(
            email,
            'Seu cadastro profissional foi aprovado - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar email de aprovação.")
        return False


def enviar_email_recusa(email, nome, motivo):
    try:
        texto = f"""
Olá, {nome}.

Agradecemos pelo seu interesse em fazer parte da plataforma Apoio & Consciência.

Após a análise realizada pela nossa equipe administrativa, informamos que seu cadastro profissional não foi aprovado neste momento.

Motivo informado pela administração:

{motivo}

Caso você entenda que houve algum equívoco ou queira realizar um novo cadastro futuramente, poderá entrar em contato pelo email gabrielgaburi@hotmail.com.

Atenciosamente,

Equipe Apoio & Consciência
"""

        conteudo = f"""
        <!-- TOPO -->

        <div style="
            background:linear-gradient(135deg, #1d3557, #457b9d);
            padding:30px;
            text-align:center;
            color:white;
        ">

            <h1 style="
                margin:0;
                font-size:28px;
            ">
                Apoio & Consciência
            </h1>

            <p style="
                margin-top:8px;
                font-size:15px;
                opacity:0.9;
            ">
                Atualização do seu cadastro
            </p>

        </div>


        <!-- CONTEÚDO -->

        <div style="
            padding:40px 30px;
            color:#333;
        ">

            <h2 style="
                color:#1d3557;
                margin-top:0;
                text-align:center;
            ">
                Cadastro profissional
            </h2>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Olá, <strong>{nome}</strong>.
            </p>

            <p style="
                font-size:16px;
                line-height:1.6;
                color:#555;
            ">
                Após a análise realizada pela nossa equipe administrativa,
                informamos que seu cadastro profissional
                <strong>não foi aprovado neste momento.</strong>
            </p>


            <!-- MOTIVO -->

            <div style="
                margin:25px 0;
                padding:20px;
                background:#fff3cd;
                border:1px solid #ffe69c;
                border-radius:10px;
            ">

                <p style="
                    margin-top:0;
                    font-size:15px;
                    font-weight:bold;
                    color:#856404;
                ">
                    Motivo informado pela administração:
                </p>

                <p style="
                    margin-bottom:0;
                    font-size:15px;
                    line-height:1.6;
                    color:#664d03;
                    white-space:pre-line;
                ">
                    {motivo}
                </p>

            </div>


            <p style="
                font-size:15px;
                line-height:1.6;
                color:#555;
            ">
                Caso você entenda que houve algum equívoco ou queira
                realizar um novo cadastro futuramente, poderá entrar
                em contato com a plataforma.
            </p>

        </div>


        <!-- RODAPÉ -->

        <div style="
            background:#f8f9fa;
            padding:20px;
            text-align:center;
            font-size:13px;
            color:#6c757d;
            border-top:1px solid #e9ecef;
        ">

            Equipe Apoio & Consciência<br>

            © Apoio & Consciência

        </div>
        """

        _montar_e_enviar_email(
            email,
            'Atualização do seu cadastro profissional - Apoio & Consciência',
            texto,
            conteudo
        )

        return True

    except Exception:
        current_app.logger.exception("Erro ao enviar email de recusa.")
        return False


# Rodam em threads fora da requisição original: por isso recebem o app real (current_app
# não vale numa thread nova) e abrem um test_request_context para url_for e mail.send.
def enviar_confirmacao_em_background(app, email, tipo, base_url):
    # Mesmo esquema de enviar_recuperacao_em_background: a thread precisa do contexto do app
    with app.test_request_context(base_url=base_url):
        if tipo == "profissional":
            enviado = enviar_email_cadastro_profissional(email)
        else:
            enviado = enviar_email_confirmacao_usuario(email)

        if not enviado:
            app.logger.error("Falha ao reenviar email de confirmação (segundo plano).")


def enviar_recuperacao_em_background(app, email, base_url):
    # test_request_context fornece o contexto de app e de requisição que
    # url_for/mail.send precisam, já que esta função roda numa thread fora
    # do request original (ver comentário em esqueci_senha). base_url vem
    # do request original para que o link no email use o host correto
    # quando BASE_URL não estiver configurada (fallback de url_externa).
    with app.test_request_context(base_url=base_url):
        if not enviar_email_recuperacao(email):
            app.logger.error(
                "Falha ao enviar email de recuperação (segundo plano) para %s",
                email
            )
