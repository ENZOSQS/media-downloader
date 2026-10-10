import importlib.util
import os
import shutil
import subprocess
import sys
import threading


def verificar_dependencias():
    return {
        "Python": sys.version_info >= (3, 10),
        "CustomTkinter": importlib.util.find_spec("customtkinter") is not None,
        "yt-dlp": shutil.which("yt-dlp") is not None,
        "FFmpeg": shutil.which("ffmpeg") is not None,
        "FFprobe": shutil.which("ffprobe") is not None,
    }


def instalar_customtkinter():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "customtkinter"],
        check=True,
    )


def instalar_ytdlp():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
        check=True,
    )


def instalar_ffmpeg():
    winget = shutil.which("winget")

    if not winget:
        raise RuntimeError(
            "O winget não foi encontrado. Instale o FFmpeg manualmente."
        )

    subprocess.run(
        [
            winget,
            "install",
            "--id", "Gyan.FFmpeg.Shared",
            "-e",
            "--accept-source-agreements",
            "--accept-package-agreements",
        ],
        check=True,
    )


def preparar_dependencias(atualizar_status):
    """Instala componentes ausentes sem bloquear a interface."""

    try:
        status = verificar_dependencias()

        if not status["Python"]:
            raise RuntimeError("É necessário Python 3.10 ou superior.")

        if not status["CustomTkinter"]:
            atualizar_status("Instalando CustomTkinter...")
            instalar_customtkinter()

        if not status["yt-dlp"]:
            atualizar_status("Instalando yt-dlp...")
            instalar_ytdlp()

        status = verificar_dependencias()

        if not status["FFmpeg"] or not status["FFprobe"]:
            atualizar_status("Instalando FFmpeg...")
            instalar_ffmpeg()

        atualizar_status("Verificando novamente as dependências...")

        status = verificar_dependencias()

        if not all(status.values()):
            faltantes = [
                nome for nome, instalado in status.items()
                if not instalado
            ]
            raise RuntimeError(
                "Componentes ausentes: " + ", ".join(faltantes)
                + ". Reinicie o programa após a instalação."
            )

        atualizar_status("Todas as dependências estão prontas.")

    except Exception as erro:
        atualizar_status(f"Erro nas dependências: {erro}")