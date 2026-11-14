"""Fotos de perfil dos profissionais: validação, gravação e limpeza de arquivos."""

import os
import re
import threading
import time
import uuid

from flask import current_app, session
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

from db import get_db_connection


extensoes_validas = {".jpg", ".jpeg", ".png"}


# Tamanho máximo (em pixels) do maior lado da foto de perfil
TAMANHO_MAXIMO_FOTO = 1024


# Limite de pixels da foto enviada. O upload tem no máximo 5 MB, mas uma imagem lisa de
# 12000x12000 cabe nisso e ocupa centenas de MB de memória ao ser aberta.
MAXIMO_PIXELS_FOTO = 50_000_000


class ImagemGrandeDemais(ValueError):
    pass


def salvar_foto_perfil(arquivo, pasta, prefixo=""):
    # Valida a imagem enviada e grava uma cópia nova dela: isso remove os metadados
    # (EXIF, que pode ter a localização GPS de onde a foto foi tirada) e qualquer
    # conteúdo escondido no arquivo. Devolve o nome do arquivo salvo ou levanta ValueError.
    extensao_enviada = os.path.splitext(secure_filename(arquivo.filename or ""))[1].lower()

    if extensao_enviada not in extensoes_validas:
        raise ValueError("Formato de imagem inválido. Use JPG ou PNG.")

    try:
        arquivo.stream.seek(0)
        Image.open(arquivo.stream).verify()

        arquivo.stream.seek(0)
        imagem = Image.open(arquivo.stream)
        formato = imagem.format

        if formato not in {"JPEG", "PNG"}:
            raise ValueError

        # O cabeçalho já informa o tamanho, então isso é checado antes de decodificar a imagem
        if imagem.width * imagem.height > MAXIMO_PIXELS_FOTO:
            raise ImagemGrandeDemais

        # Aplica a rotação indicada no EXIF antes de descartá-lo
        imagem = ImageOps.exif_transpose(imagem)
        imagem.thumbnail((TAMANHO_MAXIMO_FOTO, TAMANHO_MAXIMO_FOTO))

        if formato == "JPEG":
            extensao = ".jpg"
            imagem = imagem.convert("RGB")
        else:
            extensao = ".png"
            if imagem.mode not in ("RGB", "RGBA"):
                imagem = imagem.convert("RGBA")

        nome = f"{prefixo}{uuid.uuid4().hex}{extensao}"
        caminho = os.path.join(pasta, nome)

        # O comentário do JPEG (marcador COM) é regravado pelo Pillow se ficar em info
        imagem.info.pop("comment", None)

        if formato == "JPEG":
            imagem.save(caminho, "JPEG", quality=85, optimize=True)
        else:
            imagem.save(caminho, "PNG", optimize=True)

        return nome

    except ImagemGrandeDemais:
        raise ValueError(
            "A imagem tem resolução alta demais (máximo de 50 megapixels). "
            "Reduza a foto e tente novamente."
        )

    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError):
        raise ValueError("A imagem é inválida ou está em um formato não permitido.")


def remover_foto_perfil(nome):
    # Apaga uma foto de perfil que deixou de ser usada (troca de foto ou falha ao salvar)
    caminho = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(nome))

    try:
        if os.path.isfile(caminho):
            os.remove(caminho)
    except OSError:
        current_app.logger.exception("Erro ao remover foto de perfil: %s", caminho)


def caminho_foto_temporaria(nome):
    # Só aceita nomes gerados pelo próprio app (temp_<uuid>.<ext>)
    if not nome or not re.fullmatch(r"temp_[0-9a-f]{32}\.(jpg|jpeg|png)", nome):
        return None

    caminho = os.path.join(current_app.config["UPLOAD_FOLDER"], nome)
    return caminho if os.path.isfile(caminho) else None


def descartar_foto_temporaria():
    caminho = caminho_foto_temporaria(session.pop("foto_temporaria_profissional", None))

    if caminho:
        try:
            os.remove(caminho)
        except OSError:
            current_app.logger.exception("Erro ao remover foto temporária: %s", caminho)


def limpar_fotos_temporarias():
    pasta = current_app.config["UPLOAD_FOLDER"]

    if not os.path.exists(pasta):
        return

    agora = time.time()

    for arquivo in os.listdir(pasta):

        if not arquivo.startswith("temp_"):
            continue

        caminho = os.path.join(pasta, arquivo)

        if not os.path.isfile(caminho):
            continue

        idade = agora - os.path.getmtime(caminho)

        # Remove temporários com mais de 1 hora
        if idade > 3600:
            try:
                os.remove(caminho)

            except OSError:
                current_app.logger.exception(
                    "Erro ao remover foto temporária: %s",
                    caminho
                )


def limpar_fotos_orfas():
    pasta = current_app.config["UPLOAD_FOLDER"]

    if not os.path.exists(pasta):
        return

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT foto
            FROM profissionais
            WHERE foto IS NOT NULL
              AND foto != ''
        """)

        fotos_banco = {
            registro["foto"]
            for registro in cursor.fetchall()
        }

        for arquivo in os.listdir(pasta):
            caminho = os.path.join(pasta, arquivo)

            if not os.path.isfile(caminho):
                continue

            # Não mexe nas fotos temporárias aqui
            if arquivo.startswith("temp_"):
                continue

            # Fotos recentes podem ser de um cadastro que ainda não fez commit
            if time.time() - os.path.getmtime(caminho) < 3600:
                continue

            # Se não estiver registrado no banco, remove
            if arquivo not in fotos_banco:
                try:
                    os.remove(caminho)
                    current_app.logger.info(
                        "Foto órfã removida: %s",
                        arquivo
                    )

                except OSError:
                    current_app.logger.exception(
                        "Erro ao remover foto órfã: %s",
                        arquivo
                    )

    except Exception:
        current_app.logger.exception("Erro ao limpar fotos órfãs.")

    finally:
        if cursor:
            cursor.close()

        if conexao:
            conexao.close()


# A limpeza varre a pasta e consulta o banco; nas páginas abertas a visitantes
# ela roda no máximo a cada 10 minutos
INTERVALO_LIMPEZA_FOTOS = 600


ultima_limpeza_fotos = 0


limpeza_fotos_lock = threading.Lock()


def limpar_fotos_periodicamente():
    global ultima_limpeza_fotos

    with limpeza_fotos_lock:
        if time.time() - ultima_limpeza_fotos < INTERVALO_LIMPEZA_FOTOS:
            return

        ultima_limpeza_fotos = time.time()

    limpar_fotos_temporarias()
    limpar_fotos_orfas()
