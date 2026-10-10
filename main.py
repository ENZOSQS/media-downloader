import json
import os
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from pathlib import Path
import threading

import customtkinter as ctk

from core.dependencies import preparar_dependencias
from core.downloader import baixar_midia


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def carregar_configuracoes():
    configuracoes = {
        "download_folder": str(Path.home() / "Downloads"),
        "default_format": "MP3",
        "theme": "dark",
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as arquivo:
                configuracoes.update(json.load(arquivo))
        except (OSError, json.JSONDecodeError):
            pass

    pasta = configuracoes.get("download_folder", "")

    if not pasta or not os.path.isdir(pasta):
        configuracoes["download_folder"] = str(
            Path.home() / "Downloads"
        )

    return configuracoes


def salvar_configuracoes(configuracoes):
    with open(CONFIG_FILE, "w", encoding="utf-8") as arquivo:
        json.dump(
            configuracoes,
            arquivo,
            indent=4,
            ensure_ascii=False,
        )


class MediaDownloader(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.configuracoes = carregar_configuracoes()
        self.download_em_andamento = False

        self.title("Media Downloader")
        self.geometry("950x720")
        self.minsize(800, 650)

        self.criar_interface()
        self.iniciar_verificacao()

    def criar_interface(self):
        ctk.CTkLabel(
            self,
            text="MEDIA DOWNLOADER",
            font=("Segoe UI", 30, "bold"),
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self,
            text="Download e conversão de mídia",
            font=("Segoe UI", 14),
        ).pack(pady=(0, 20))

        painel = ctk.CTkFrame(self, corner_radius=18)
        painel.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        ctk.CTkLabel(
            painel,
            text="LINK DO VÍDEO",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", padx=25, pady=(25, 8))

        self.entrada_url = ctk.CTkEntry(
            painel,
            placeholder_text="Cole o link aqui...",
            height=42,
        )
        self.entrada_url.pack(fill="x", padx=25)

        ctk.CTkLabel(
            painel,
            text="FORMATO DE SAÍDA",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", padx=25, pady=(20, 8))

        self.formato = ctk.CTkOptionMenu(
            painel,
            values=["MP3", "WAV", "MP4"],
            height=38,
        )
        self.formato.set(
            self.configuracoes.get("default_format", "MP3")
        )
        self.formato.pack(anchor="w", padx=25)

        ctk.CTkLabel(
            painel,
            text="PASTA DE DESTINO",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", padx=25, pady=(20, 8))

        linha_pasta = ctk.CTkFrame(painel, fg_color="transparent")
        linha_pasta.pack(fill="x", padx=25)

        self.entrada_pasta = ctk.CTkEntry(
            linha_pasta,
            height=40,
        )
        self.entrada_pasta.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10),
        )
        self.entrada_pasta.insert(
            0,
            self.configuracoes["download_folder"],
        )

        ctk.CTkButton(
            linha_pasta,
            text="Escolher pasta",
            width=130,
            command=self.escolher_pasta,
        ).pack(side="right")

        ctk.CTkButton(
            painel,
            text="Abrir pasta de destino",
            height=35,
            fg_color="transparent",
            border_width=1,
            command=self.abrir_pasta,
        ).pack(anchor="w", padx=25, pady=(10, 0))

        self.botao_baixar = ctk.CTkButton(
            painel,
            text="INICIAR DOWNLOAD",
            height=48,
            font=("Segoe UI", 15, "bold"),
            command=self.iniciar_download,
            state="disabled",
        )
        self.botao_baixar.pack(fill="x", padx=25, pady=(25, 15))

        self.progresso = ctk.CTkProgressBar(painel)
        self.progresso.pack(fill="x", padx=25, pady=8)
        self.progresso.set(0)

        self.status = ctk.CTkLabel(
            painel,
            text="Preparando aplicativo...",
            font=("Segoe UI", 12),
            wraplength=800,
        )
        self.status.pack(pady=(8, 10))

        self.status_dependencias = ctk.CTkLabel(
            painel,
            text="Verificando dependências...",
            font=("Segoe UI", 11),
        )
        self.status_dependencias.pack(pady=(0, 20))

    def escolher_pasta(self):
        pasta_atual = self.entrada_pasta.get().strip()

        pasta = filedialog.askdirectory(
            title="Escolha a pasta de destino",
            initialdir=pasta_atual or str(Path.home()),
        )

        if pasta:
            self.entrada_pasta.delete(0, "end")
            self.entrada_pasta.insert(0, pasta)

            self.configuracoes["download_folder"] = pasta
            salvar_configuracoes(self.configuracoes)

            self.status.configure(text="Pasta de destino atualizada.")

    def abrir_pasta(self):
        pasta = self.entrada_pasta.get().strip()

        if not pasta:
            messagebox.showwarning(
                "Pasta",
                "Selecione uma pasta de destino.",
            )
            return

        try:
            Path(pasta).mkdir(parents=True, exist_ok=True)
            os.startfile(pasta)
        except OSError as erro:
            messagebox.showerror("Erro", str(erro))

    def iniciar_verificacao(self):
        self.botao_baixar.configure(state="disabled")

        def atualizar_status(texto):
            self.after(
                0,
                lambda: self.status_dependencias.configure(text=texto),
            )

        def executar():
            preparar_dependencias(atualizar_status)

            self.after(
                0,
                lambda: self.botao_baixar.configure(state="normal"),
            )

        threading.Thread(target=executar, daemon=True).start()

    def iniciar_download(self):
        if self.download_em_andamento:
            return

        url = self.entrada_url.get().strip()
        formato = self.formato.get()
        pasta = self.entrada_pasta.get().strip()

        if not url:
            messagebox.showwarning(
                "Link obrigatório",
                "Cole o link antes de continuar.",
            )
            return

        if not pasta:
            messagebox.showwarning(
                "Pasta obrigatória",
                "Escolha uma pasta de destino.",
            )
            return

        try:
            Path(pasta).mkdir(parents=True, exist_ok=True)

            self.configuracoes["download_folder"] = pasta
            self.configuracoes["default_format"] = formato
            salvar_configuracoes(self.configuracoes)

        except OSError as erro:
            messagebox.showerror("Erro", str(erro))
            return

        self.download_em_andamento = True
        self.botao_baixar.configure(state="disabled")
        self.progresso.set(0)
        self.status.configure(text="Preparando download...")

        def atualizar_progresso(valor):
            self.after(0, lambda: self.progresso.set(valor))

        def atualizar_status(texto):
            self.after(0, lambda: self.status.configure(text=texto))

        def concluir():
            def finalizar_interface():
                self.download_em_andamento = False
                self.botao_baixar.configure(state="normal")

            self.after(0, finalizar_interface)

        baixar_midia(
            url=url,
            formato=formato,
            pasta_destino=pasta,
            callback_progresso=atualizar_progresso,
            callback_status=atualizar_status,
            callback_concluido=concluir,
        )


if __name__ == "__main__":
    app = MediaDownloader()
    app.mainloop()