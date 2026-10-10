import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import yt_dlp


def encontrar_ffmpeg():
    """Localiza o FFmpeg no PATH do Windows."""
    return shutil.which("ffmpeg")


def baixar_midia(
    url,
    formato,
    pasta_destino,
    callback_progresso,
    callback_status,
    callback_concluido,
):
    """Executa o download em uma thread separada."""

    def executar():
        try:
            destino = Path(pasta_destino)
            destino.mkdir(parents=True, exist_ok=True)

            if formato == "MP4":
                opcoes = {
                    "format": "best[ext=mp4]/best",
                    "outtmpl": str(destino / "%(title)s.%(ext)s"),
                    "noplaylist": True,
                    "progress_hooks": [
                        lambda dados: atualizar_progresso(
                            dados,
                            callback_progresso,
                            callback_status,
                        )
                    ],
                }
            else:
                opcoes = {
                    "format": "bestaudio/best",
                    "outtmpl": str(destino / "%(title)s.%(ext)s"),
                    "noplaylist": True,
                    "progress_hooks": [
                        lambda dados: atualizar_progresso(
                            dados,
                            callback_progresso,
                            callback_status,
                        )
                    ],
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": formato.lower(),
                            "preferredquality": "0",
                        }
                    ],
                }

            ffmpeg = encontrar_ffmpeg()

            if ffmpeg:
                opcoes["ffmpeg_location"] = str(Path(ffmpeg).parent)

            callback_status("Iniciando download...")

            with yt_dlp.YoutubeDL(opcoes) as ydl:
                ydl.download([url])

            callback_progresso(1.0)
            callback_status("Download concluído!")

        except Exception as erro:
            callback_status(f"Erro: {erro}")

        finally:
            callback_concluido()

    threading.Thread(target=executar, daemon=True).start()


def atualizar_progresso(dados, callback_progresso, callback_status):
    estado = dados.get("status")

    if estado == "downloading":
        total = dados.get("total_bytes") or dados.get("total_bytes_estimate")
        baixado = dados.get("downloaded_bytes", 0)

        if total:
            callback_progresso(min(baixado / total, 1.0))

        velocidade = dados.get("speed")
        if velocidade:
            velocidade_mbps = velocidade / (1024 * 1024)
            callback_status(
                f"Baixando... {velocidade_mbps:.2f} MB/s"
            )

    elif estado == "finished":
        callback_progresso(1.0)
        callback_status("Convertendo arquivo...")