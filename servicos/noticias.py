"""Notícias: busca na API do GNews, filtro de relevância e cache no banco."""

import os
import time
import unicodedata
from datetime import datetime

import requests
from flask import current_app

from db import get_db_connection


_cache_noticias = {
    "dados": [],
    "atualizado_em": 0
}


def testar_api_noticias():
    chave = os.getenv("GNEWS_API_KEY")

    if not chave:
        current_app.logger.error("GNEWS_API_KEY não encontrada na configuração.")
        return []

    try:
        resposta = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": '"apostas online" OR bets',
                "lang": "pt",
                "country": "br",
                "max": 10,
                "apikey": chave
            },
            timeout=15
        )

        if resposta.status_code != 200:
            current_app.logger.warning(
                "A API GNews retornou status HTTP %s.",
                resposta.status_code
            )
            return []

        dados = resposta.json()
        noticias_relevantes = []

        for artigo in dados.get("articles", []):
            if not noticia_relevante(artigo):
                continue
            
            data_publicacao = artigo.get("publishedAt")

            if data_publicacao:
                try:
                    data_publicacao = datetime.fromisoformat(
                        data_publicacao.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                except (ValueError, TypeError):
                    data_publicacao = None

           
            noticia = {
                "titulo": artigo.get("title", ""),
                "resumo": artigo.get("description", ""),
                "introducao": artigo.get("content", ""),
                "fonte": artigo.get("url", ""),
                "imagem": artigo.get("image", ""),
                "data_publicacao": data_publicacao
            }


            noticias_relevantes.append(noticia)
            

            current_app.logger.info(
                    "Busca GNews concluída. Notícias relevantes encontradas: %s",
                    len(noticias_relevantes)
                )

        return noticias_relevantes

    except requests.RequestException:
        current_app.logger.exception("Erro ao consultar a API GNews.")
        return []


def carregar_noticias():
    agora = time.time()

    # Reutiliza o cache durante 30 minutos
    if (
        _cache_noticias["dados"]
        and agora - _cache_noticias["atualizado_em"] < 1800
    ):
        return _cache_noticias["dados"]

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # Busca notícias novas na API
        noticias_api = testar_api_noticias()
        
        if noticias_api:
            for noticia in noticias_api:
                fonte = noticia.get("fonte", "").strip()

                # Não salva notícias sem link original
                if not fonte:
                    continue

                cursor.execute("""
                    INSERT INTO noticias_site (
                        titulo,
                        resumo,
                        introducao,
                        fonte,
                        imagem,
                        data_publicacao
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        titulo = VALUES(titulo),
                        resumo = VALUES(resumo),
                        introducao = VALUES(introducao),
                        imagem = VALUES(imagem)
                """, (
                    noticia.get("titulo", ""),
                    noticia.get("resumo", ""),
                    noticia.get("introducao", ""),
                    fonte,
                    noticia.get("imagem", ""),
                    noticia.get("data_publicacao")
                ))

            conexao.commit()

            # Mantém somente as 9 notícias mais recentes
            cursor.execute("""
                DELETE FROM noticias_site
                WHERE id NOT IN (
                    SELECT id
                    FROM (
                        SELECT id
                        FROM noticias_site
                        ORDER BY
                            data_publicacao DESC,
                            criada_em DESC,
                            id DESC
                        LIMIT 9
                    ) AS recentes
                )
            """)

            conexao.commit()

        # Recupera as notícias salvas, mesmo se a API falhar
        cursor.execute("""
            SELECT
                id,
                titulo,
                resumo,
                introducao,
                fonte,
                imagem,
                data_publicacao
            FROM noticias_site
            ORDER BY
                data_publicacao DESC,
                criada_em DESC,
                id DESC
            LIMIT 9
        """)

        noticias = cursor.fetchall()

        # Atualiza o cache em memória
        _cache_noticias["dados"] = noticias
        _cache_noticias["atualizado_em"] = time.time()

        return noticias

    except Exception:
        if conexao:
            conexao.rollback()

        current_app.logger.exception(
            "Erro ao atualizar as notícias; tentando recuperar as notícias salvas no banco."
        )

        # Se houver erro, tenta recuperar as notícias já salvas no banco
        try:
            if cursor:
                cursor.execute("""
                    SELECT
                        id,
                        titulo,
                        resumo,
                        introducao,
                        fonte,
                        imagem,
                        data_publicacao
                    FROM noticias_site
                    ORDER BY
                        data_publicacao DESC,
                        criada_em DESC,
                        id DESC
                    LIMIT 9
                """)

                noticias = cursor.fetchall()
                _cache_noticias["dados"] = noticias
                _cache_noticias["atualizado_em"] = time.time()

                return noticias

        except Exception:
            current_app.logger.exception(
                "Erro ao recuperar notícias salvas no banco."
            )

        return _cache_noticias["dados"]

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


def noticia_relevante(noticia):
    texto = " ".join([
        noticia.get("title", ""),
        noticia.get("description", ""),
        noticia.get("content", "")
    ]).lower()

    # Remove os acentos para padronizar a comparação
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    termos_relevantes = [
        "vicio em apostas",
        "dependencia em apostas",
        "jogo compulsivo",
        "jogo patologico",
        "transtorno do jogo",
        "saude mental",
        "saude publica",
        "jogos de azar",
        "endividamento",
        "perdas financeiras",
        "superendividamento",
        "apostador compulsivo",
        "compulsao por jogos",
        "jogo do tigrinho",
        "impactos das apostas",
        "tratamento para jogadores",
        "prevencao as apostas",
        "familiares de apostadores",
        "regulamentacao das apostas",
        "proibicao das apostas",
        "proibicao das bets",
        "proibir nao e proteger"
    ]

    return any(termo in texto for termo in termos_relevantes)
