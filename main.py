import os
import sys
import threading
import time
import tempfile
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw

import config_manager
import github_service
import installer_service
import notifier

try:
    from version import __version__, __app_name__, __default_repo__
except ImportError:
    __version__ = "v1.0.0"
    __app_name__ = "Nordestina App Suite"
    __default_repo__ = "evandroomiix/suite-nordestina"

# Carrega configuração inicial
_initial_config = config_manager.load_config()
_initial_appearance = _initial_config.get("appearance_mode", "dark")
ctk.set_appearance_mode(_initial_appearance)
ctk.set_default_color_theme("blue")


class SquareAppCard(ctk.CTkFrame):
    """
    Card em formato quadrado vertical estilo ArtCraft com suporte a modo claro/escuro.
    """
    def __init__(self, master, project_data, is_installed, release_info, on_action, **kwargs):
        super().__init__(
            master,
            corner_radius=14,
            fg_color=("#ffffff", "#1e222b"),
            border_width=1,
            border_color=("#d0d7de", "#2d3340"),
            width=250,
            height=340,
            **kwargs
        )
        self.project_data = project_data
        self.is_installed = is_installed
        self.release_info = release_info or {}
        self.on_action = on_action

        self.pack_propagate(False)
        self._build_ui()

    def _build_ui(self):
        # 1. Topo: Ícone e Categoria
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=14, pady=(14, 4))

        cat_badge = ctk.CTkLabel(
            top_bar,
            text=f" {self.project_data.get('category', 'App')} ",
            fg_color=("#e1f0ff", "#273244"),
            text_color=("#0969da", "#79b8ff"),
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        cat_badge.pack(side="right")

        # Ícone Grande Centralizado
        icon_label = ctk.CTkLabel(
            self,
            text=self.project_data.get("icon_emoji", "📊"),
            font=ctk.CTkFont(size=44)
        )
        icon_label.pack(pady=(4, 6))

        # Nome do Projeto
        name_label = ctk.CTkLabel(
            self,
            text=self.project_data["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1f2328", "#f0f6fc"),
            wraplength=230,
            justify="center"
        )
        name_label.pack(padx=10, pady=(0, 4))

        # Descrição curta
        desc_label = ctk.CTkLabel(
            self,
            text=self.project_data.get("description", ""),
            font=ctk.CTkFont(size=11),
            text_color=("#57606a", "#8b949e"),
            wraplength=230,
            justify="center",
            height=32
        )
        desc_label.pack(padx=10, pady=(0, 6))

        # 2. Status e Versão
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(fill="x", padx=14, pady=2)

        curr_ver = installer_service.read_installed_version(self.project_data["id"]) or self.project_data.get("installed_version", "v1.0.0")
        latest_tag = self.release_info.get("tag_name")
        has_update = self.release_info.get("success") and github_service.is_newer_version(latest_tag, curr_ver)

        if not self.is_installed:
            status_badge = ctk.CTkLabel(
                status_frame,
                text="DISPONÍVEL PARA INSTALAR",
                fg_color=("#fff8c5", "#382d18"),
                text_color=("#9a6700", "#e3b341"),
                corner_radius=6,
                font=ctk.CTkFont(size=10, weight="bold"),
                height=24
            )
            status_badge.pack(fill="x")
        elif has_update:
            status_badge = ctk.CTkLabel(
                status_frame,
                text=f"⚡ ATUALIZAÇÃO: {curr_ver} ➔ {latest_tag}",
                fg_color=("#ffedd5", "#3b2b1a"),
                text_color=("#c2410c", "#ffa657"),
                corner_radius=6,
                font=ctk.CTkFont(size=10, weight="bold"),
                height=24
            )
            status_badge.pack(fill="x")
        else:
            status_badge = ctk.CTkLabel(
                status_frame,
                text=f"✔ Instalado ({curr_ver})",
                fg_color=("#dafbe1", "#183424"),
                text_color=("#1a7f37", "#56d364"),
                corner_radius=6,
                font=ctk.CTkFont(size=10, weight="bold"),
                height=24
            )
            status_badge.pack(fill="x")

        # 3. Caixa de Novidades da Release (se houver atualização)
        if self.is_installed and has_update:
            body_text = self.release_info.get("body", "Novas melhorias disponíveis.")
            body_preview = (body_text[:95] + "...") if len(body_text) > 95 else body_text
            rel_box = ctk.CTkLabel(
                self,
                text=f"Novidades: {body_preview}",
                font=ctk.CTkFont(size=10, slant="italic"),
                text_color=("#57606a", "#c9d1d9"),
                wraplength=230,
                justify="center",
                height=30
            )
            rel_box.pack(padx=10, pady=(4, 4))
        else:
            spacer = ctk.CTkLabel(self, text="", height=16)
            spacer.pack()

        # 4. Botão de Ação Inferior (ABRIR, INSTALAR ou ATUALIZAR)
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(side="bottom", fill="x", padx=14, pady=(6, 14))

        if not self.is_installed:
            self.btn_action = ctk.CTkButton(
                self.btn_frame,
                text="⬇ INSTALAR",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#1f6feb",
                hover_color="#1857ba",
                text_color="#ffffff",
                height=34,
                corner_radius=8,
                command=lambda: self.on_action("install", self.project_data, self.release_info)
            )
            self.btn_action.pack(fill="x")
        elif has_update:
            self.btn_action = ctk.CTkButton(
                self.btn_frame,
                text="⚡ ATUALIZAR",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#238636",
                hover_color="#2ea043",
                text_color="#ffffff",
                height=34,
                corner_radius=8,
                command=lambda: self.on_action("update", self.project_data, self.release_info)
            )
            self.btn_action.pack(fill="x")
        else:
            self.btn_action = ctk.CTkButton(
                self.btn_frame,
                text="▶ ABRIR",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#f3f4f6", "#21262d"),
                hover_color=("#e5e7eb", "#30363d"),
                text_color=("#24292f", "#f0f6fc"),
                border_width=1,
                border_color=("#d0d7de", "#384252"),
                height=34,
                corner_radius=8,
                command=lambda: self.on_action("open", self.project_data, self.release_info)
            )
            self.btn_action.pack(fill="x")

        # Container de progresso (Download / Instalação)
        self.progress_container = ctk.CTkFrame(self.btn_frame, fg_color="transparent")
        self.lbl_progress = ctk.CTkLabel(
            self.progress_container,
            text="Iniciando...",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#0969da", "#58a6ff"),
            anchor="w"
        )
        self.lbl_progress.pack(fill="x", pady=(0, 2))
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_container,
            height=8,
            corner_radius=4,
            progress_color="#2ea043"
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

    def show_progress(self, percent_fraction, text=""):
        try:
            if self.btn_action.winfo_ismapped():
                self.btn_action.pack_forget()
            if not self.progress_container.winfo_ismapped():
                self.progress_container.pack(fill="x")
            self.progress_bar.set(max(0.0, min(1.0, float(percent_fraction))))
            if text:
                self.lbl_progress.configure(text=text)
        except Exception:
            pass

    def hide_progress(self):
        try:
            if self.progress_container.winfo_ismapped():
                self.progress_container.pack_forget()
            if not self.btn_action.winfo_ismapped():
                self.btn_action.pack(fill="x")
        except Exception:
            pass


class ProjectStartupDialog(ctk.CTkToplevel):
    """
    Janela elegante de procedimento de inicialização para aplicativos que levam alguns segundos
    para carregar bancos de dados e interfaces (ex: CIC Reformulado).
    """
    def __init__(self, master, project_name, icon_emoji="🏢", estimated_seconds=8, on_complete=None):
        super().__init__(master)
        self.project_name = project_name
        self.estimated_seconds = estimated_seconds
        self.on_complete = on_complete
        self.elapsed = 0.0
        self.is_closed = False

        self.title(f"Inicializando {project_name}")
        self.geometry("500x260")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=("#ffffff", "#161b22"))

        # Centraliza na janela pai
        try:
            self.transient(master)
            master.update_idletasks()
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            px = max(40, mx + (mw - 500) // 2)
            py = max(40, my + (mh - 260) // 2)
            self.geometry(f"+{px}+{py}")
        except Exception:
            pass

        self._build_ui(icon_emoji)
        self._start_progress_loop()

    def _build_ui(self, icon_emoji):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Cabeçalho
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        lbl_icon = ctk.CTkLabel(header, text=icon_emoji, font=ctk.CTkFont(size=38))
        lbl_icon.pack(side="left", padx=(0, 14))

        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.pack(side="left", fill="x", expand=True)

        lbl_title = ctk.CTkLabel(
            titles,
            text=f"Inicializando {self.project_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1f2328", "#f0f6fc"),
            anchor="w"
        )
        lbl_title.pack(fill="x")

        lbl_sub = ctk.CTkLabel(
            titles,
            text="Lojas Nordestina • Procedimento de Inicialização",
            font=ctk.CTkFont(size=11),
            text_color=("#57606a", "#8b949e"),
            anchor="w"
        )
        lbl_sub.pack(fill="x")

        # Mensagem de etapa dinâmica
        self.lbl_stage = ctk.CTkLabel(
            container,
            text="⏳ Disparando processo seguro e preparando ambiente...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#0969da", "#58a6ff"),
            anchor="w"
        )
        self.lbl_stage.pack(fill="x", pady=(6, 4))

        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(
            container,
            height=10,
            corner_radius=5,
            progress_color="#2ea043"
        )
        self.progress_bar.pack(fill="x", pady=(4, 10))
        self.progress_bar.set(0.12)

        # Aviso sobre tempo de inicialização
        self.lbl_notice = ctk.CTkLabel(
            container,
            text="💡 O sistema processa uma volumosa base de dados locais e a interface moderna.\nA inicialização leva cerca de 5 a 10 segundos. A tela abrirá automaticamente.",
            font=ctk.CTkFont(size=11),
            text_color=("#57606a", "#8b949e"),
            justify="left",
            anchor="w"
        )
        self.lbl_notice.pack(fill="x", pady=(0, 12))

        # Botão para fechar aviso sem interromper processo
        btn_close = ctk.CTkButton(
            container,
            text="Aguardar em Segundo Plano",
            font=ctk.CTkFont(size=11),
            fg_color=("#eaeef2", "#21262d"),
            hover_color=("#d0d7de", "#30363d"),
            text_color=("#24292f", "#f0f6fc"),
            height=28,
            corner_radius=6,
            command=self.close_dialog
        )
        btn_close.pack(anchor="e")

    def _start_progress_loop(self):
        steps = [
            (0.15, "⏳ Disparando processo seguro e verificando executável..."),
            (0.35, "📂 Conectando às bases de dados de clientes, títulos e pedidos..."),
            (0.65, "⚙️ Inicializando servidor interno e rotas de consulta..."),
            (0.85, "🖥️ Renderizando interface gráfica do sistema..."),
            (1.00, "✨ Pronto! O CIC Reformulado está abrindo na tela...")
        ]

        def update():
            if self.is_closed:
                return
            self.elapsed += 0.5
            fraction = min(1.0, self.elapsed / max(1.0, self.estimated_seconds))
            try:
                self.progress_bar.set(fraction)
                for thresh, msg in reversed(steps):
                    if fraction >= thresh or thresh == steps[0][0]:
                        self.lbl_stage.configure(text=msg)
                        break
            except Exception:
                pass

            if fraction >= 1.0:
                self.after(1400, self.close_dialog)
            else:
                self.after(500, update)

        self.after(400, update)

    def close_dialog(self):
        if not self.is_closed:
            self.is_closed = True
            if self.on_complete:
                try:
                    self.on_complete()
                except Exception:
                    pass
            try:
                self.destroy()
            except Exception:
                pass


class SettingsWindow(ctk.CTkToplevel):
    """
    Janela de Configurações com separação de permissão:
    - Preferências do usuário (Geral)
    - Área Restrita para Administradores (Token, Repositórios, Auto-Update)
    """
    def __init__(self, parent, config, on_save_callback):
        super().__init__(parent)
        self.title("Configurações - Nordestina App Suite")
        self.geometry("620x680")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.config = config
        self.on_save_callback = on_save_callback
        self.is_admin_unlocked = False

        self._build_ui()

    def _build_ui(self):
        # Container com rolagem para conforto visual
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=25, pady=20)

        # Cabeçalho
        lbl_title = ctk.CTkLabel(
            self.container,
            text="⚙️ Configurações & Preferências",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f2328", "#f0f6fc")
        )
        lbl_title.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            self.container,
            text="Personalize o comportamento do Launcher ou gerencie as credenciais da empresa.",
            font=ctk.CTkFont(size=12),
            text_color=("#57606a", "#8b949e")
        ).pack(anchor="w", pady=(0, 16))

        # --- SEÇÃO 1: PREFERÊNCIAS GERAIS (Livre para todos os usuários) ---
        sec1 = ctk.CTkFrame(self.container, fg_color=("#ffffff", "#1e222b"), corner_radius=10, border_width=1, border_color=("#d0d7de", "#2d3340"))
        sec1.pack(fill="x", pady=(0, 20))

        sec1_header = ctk.CTkLabel(
            sec1,
            text="🖥️  Preferências do Sistema",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1f2328", "#f0f6fc")
        )
        sec1_header.pack(anchor="w", padx=16, pady=(12, 10))

        # Intervalo de checagem
        int_frame = ctk.CTkFrame(sec1, fg_color="transparent")
        int_frame.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(int_frame, text="Verificação em segundo plano a cada:", font=ctk.CTkFont(size=12)).pack(side="left")
        self.interval_var = ctk.StringVar(value=str(self.config.get("check_interval_minutes", 60)))
        cbo = ctk.CTkComboBox(int_frame, values=["15", "30", "60", "120"], variable=self.interval_var, state="readonly", width=110)
        cbo.pack(side="right")

        # Bandeja
        self.tray_var = ctk.BooleanVar(value=self.config.get("minimize_to_tray", True))
        chk_tray = ctk.CTkCheckBox(sec1, text="Minimizar para a bandeja do sistema (perto do relógio)", variable=self.tray_var, font=ctk.CTkFont(size=12))
        chk_tray.pack(anchor="w", padx=16, pady=(0, 12))

        # Botão Criar Atalho na Área de Trabalho
        btn_desk = ctk.CTkButton(
            sec1,
            text="📌 Criar / Restaurar Atalho na Área de Trabalho",
            fg_color=("#e1e4e8", "#21262d"),
            hover_color=("#d0d7de", "#30363d"),
            text_color=("#1f2328", "#f0f6fc"),
            height=30,
            command=self._create_desktop_shortcut_action
        )
        btn_desk.pack(anchor="w", padx=16, pady=(0, 14))

        # --- SEÇÃO 2: ÁREA RESTRITA AO ADMINISTRADOR ---
        self.admin_card = ctk.CTkFrame(self.container, fg_color=("#ffffff", "#1e222b"), corner_radius=10, border_width=1, border_color=("#d0d7de", "#2d3340"))
        self.admin_card.pack(fill="x", pady=(0, 20))

        self._render_admin_section()

        # Botões de Ação na base
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(0, 15), side="bottom")

        ctk.CTkButton(
            btn_box,
            text="Fechar",
            fg_color=("#e1e4e8", "#3e4451"),
            hover_color=("#d0d7de", "#4b5263"),
            text_color=("#1f2328", "#ffffff"),
            command=self.destroy,
            width=100
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="Salvar Alterações",
            fg_color="#1f6feb",
            hover_color="#1857ba",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._save,
            width=150
        ).pack(side="right")

    def _render_admin_section(self):
        for w in self.admin_card.winfo_children():
            w.destroy()

        if not self.is_admin_unlocked:
            # Estado Bloqueado: Exige Senha de Administrador
            lock_header = ctk.CTkLabel(
                self.admin_card,
                text="🔒  Área Restrita ao Administrador",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("#cf222e", "#f85149")
            )
            lock_header.pack(anchor="w", padx=16, pady=(12, 6))

            ctk.CTkLabel(
                self.admin_card,
                text="As configurações de GitHub Token, Repositórios privados e controle\nde implantação são restritas aos administradores de TI.",
                font=ctk.CTkFont(size=11),
                text_color=("#57606a", "#8b949e"),
                justify="left"
            ).pack(anchor="w", padx=16, pady=(0, 12))

            pass_box = ctk.CTkFrame(self.admin_card, fg_color="transparent")
            pass_box.pack(fill="x", padx=16, pady=(0, 14))

            self.entry_pass = ctk.CTkEntry(pass_box, placeholder_text="Senha de Administrador", show="*", width=240)
            self.entry_pass.pack(side="left", padx=(0, 10))
            self.entry_pass.bind("<Return>", lambda e: self._unlock_admin())

            btn_unlock = ctk.CTkButton(
                pass_box,
                text="🔓 Desbloquear",
                fg_color="#1f6feb",
                hover_color="#1857ba",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self._unlock_admin,
                width=120
            )
            btn_unlock.pack(side="left")
        else:
            # Estado Desbloqueado: Exibe todos os parâmetros técnicos
            unlocked_header = ctk.CTkFrame(self.admin_card, fg_color="transparent")
            unlocked_header.pack(fill="x", padx=16, pady=(12, 8))

            ctk.CTkLabel(
                unlocked_header,
                text="🔓  Controle de Administrador Liberado",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("#1a7f37", "#56d364")
            ).pack(side="left")

            btn_lock_again = ctk.CTkButton(
                unlocked_header,
                text="Bloquear",
                width=75,
                height=24,
                fg_color=("#e1e4e8", "#21262d"),
                hover_color=("#d0d7de", "#30363d"),
                text_color=("#1f2328", "#f0f6fc"),
                font=ctk.CTkFont(size=10),
                command=self._lock_admin
            )
            btn_lock_again.pack(side="right")

            # GitHub Token
            ctk.CTkLabel(self.admin_card, text="GitHub Personal Access Token (Leitura de Repos Privados):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(4, 2))
            self.entry_token = ctk.CTkEntry(self.admin_card, placeholder_text="ghp_... ou github_pat_...", width=530, show="*")
            self.entry_token.insert(0, self.config.get("github_token", ""))
            self.entry_token.pack(anchor="w", padx=16, pady=(0, 4))

            self.show_tok_var = ctk.BooleanVar(value=False)
            chk_tok = ctk.CTkCheckBox(self.admin_card, text="Mostrar token", variable=self.show_tok_var, command=self._toggle_token, font=ctk.CTkFont(size=11))
            chk_tok.pack(anchor="w", padx=16, pady=(0, 12))

            # Repositório do próprio Launcher
            ctk.CTkLabel(self.admin_card, text="Repositório da Suite no GitHub (para auto-update):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(0, 2))
            self.entry_launcher_repo = ctk.CTkEntry(self.admin_card, placeholder_text=__default_repo__, width=530)
            self.entry_launcher_repo.insert(0, self.config.get("launcher_repo", __default_repo__))
            self.entry_launcher_repo.pack(anchor="w", padx=16, pady=(0, 12))

            # Alterar Senha de Administrador
            ctk.CTkLabel(self.admin_card, text="Nova Senha de Administrador (deixe em branco para manter a atual):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(0, 2))
            self.entry_new_pass = ctk.CTkEntry(self.admin_card, placeholder_text="Nova senha...", width=300, show="*")
            self.entry_new_pass.pack(anchor="w", padx=16, pady=(0, 12))

            # Botão Testar Conexão com GitHub
            btn_test = ctk.CTkButton(
                self.admin_card,
                text="🔗 Testar Conexão com GitHub",
                fg_color=("#0969da", "#1f6feb"),
                hover_color=("#0854ad", "#1857ba"),
                text_color="#ffffff",
                height=28,
                command=self._test_github_connection
            )
            btn_test.pack(anchor="w", padx=16, pady=(0, 14))

    def _unlock_admin(self):
        typed_pass = self.entry_pass.get().strip()
        current_admin_pass = self.config.get("admin_password", "admin")
        if typed_pass == current_admin_pass:
            self.is_admin_unlocked = True
            self._render_admin_section()
        else:
            messagebox.showerror("Acesso Negado", "Senha de administrador incorreta!")

    def _lock_admin(self):
        self.is_admin_unlocked = False
        self._render_admin_section()

    def _toggle_token(self):
        if hasattr(self, "entry_token"):
            self.entry_token.configure(show="" if self.show_tok_var.get() else "*")

    def _test_github_connection(self):
        token = self.entry_token.get().strip()
        repo = self.entry_launcher_repo.get().strip()
        if not repo:
            repo = __default_repo__
        res = github_service.get_latest_release(repo, token=token)
        if res.get("success"):
            messagebox.showinfo("Sucesso", f"Conexão com GitHub bem-sucedida!\n\nÚltima versão localizada no repositório: {res.get('tag_name')}")
        else:
            messagebox.showwarning("Aviso de Conexão", f"Não foi possível acessar a release:\n{res.get('error')}\n\nVerifique se o token tem permissão e se o repositório existe.")

    def _create_desktop_shortcut_action(self):
        path = installer_service.install_launcher_desktop_shortcut()
        if path:
            messagebox.showinfo("Atalho Criado", f"O atalho 'NORDESTINA APP SUITE' com o logotipo oficial foi criado com sucesso na sua Área de Trabalho!\n\nLocal: {path}")
        else:
            messagebox.showerror("Erro", "Não foi possível criar o atalho na Área de Trabalho.")

    def _save(self):
        try:
            self.config["check_interval_minutes"] = int(self.interval_var.get())
        except ValueError:
            self.config["check_interval_minutes"] = 60
        self.config["minimize_to_tray"] = self.tray_var.get()

        if self.is_admin_unlocked:
            self.config["github_token"] = self.entry_token.get().strip()
            self.config["launcher_repo"] = self.entry_launcher_repo.get().strip()
            new_p = self.entry_new_pass.get().strip()
            if new_p:
                self.config["admin_password"] = new_p

        config_manager.save_config(self.config)
        self.on_save_callback()
        messagebox.showinfo("Configurações Salvas", "As alterações foram salvas com sucesso!")
        self.destroy()


class LauncherApp(ctk.CTk):
    """
    Aplicativo Principal: LOJAS NORDESTINA - NORDESTINA APP SUITE
    Abre maximizado, suporte a modo claro/escuro, grid responsivo e logotipo oficial.
    """
    def __init__(self):
        super().__init__()

        self.title(f"LOJAS NORDESTINA - NORDESTINA APP SUITE {__version__}")
        self.geometry("1200x800")
        self.minsize(860, 620)

        # Configurações do usuário
        self.config = config_manager.load_config()
        self.appearance_mode = self.config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(self.appearance_mode)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.releases_cache = {}
        self.app_cards = {}
        self.table_rows = {}
        self.launcher_update_info = None
        self.is_checking = False
        self.tray_icon = None
        self.last_notified = {}
        self._current_columns = 4
        self._resize_job = None

        # Ícones da Janela (substitui o ícone azul padrão do Tkinter)
        self._apply_window_icon()

        # Cria ou atualiza o atalho na Área de Trabalho
        try:
            installer_service.install_launcher_desktop_shortcut()
        except Exception as e:
            print(f"Erro ao registrar atalho do launcher: {e}")

        self._build_main_layout()

        # Inicia maximizado na tela
        self.after(50, lambda: self.state("zoomed"))

        # Monitora redimensionamento da janela para organizar os cartões lado a lado
        self.bind("<Configure>", self._on_window_configure)

        # Checagem inicial de atualizações
        self.after(600, self.start_update_check)
        self._schedule_auto_check()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_window_icon(self):
        """Define o ícone oficial da empresa na barra de título e barra de tarefas."""
        ico_path = os.path.join(self.base_dir, "assets", "app_icon.ico")
        png_path = os.path.join(self.base_dir, "assets", "app_icon.png")

        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        if os.path.exists(png_path):
            try:
                self._photo_icon = tk.PhotoImage(file=png_path)
                self.iconphoto(False, self._photo_icon)
            except Exception:
                pass

    def _build_main_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header Principal Estilo ArtCraft
        header_frame = ctk.CTkFrame(self, height=76, corner_radius=0, fg_color=("#ffffff", "#161b22"))
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        header_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_box.pack(fill="both", expand=True, padx=25, pady=12)

        # --- LADO ESQUERDO: LOGOTIPO + LOJAS NORDESTINA | NORDESTINA APP SUITE ---
        brand_box = ctk.CTkFrame(header_box, fg_color="transparent")
        brand_box.pack(side="left")

        # Imagem do Logo Oficial
        logo_path = os.path.join(self.base_dir, "assets", "logo_header.png")
        if os.path.exists(logo_path):
            try:
                pil_logo = Image.open(logo_path)
                self.header_logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(pil_logo.width, pil_logo.height))
                logo_lbl = ctk.CTkLabel(brand_box, image=self.header_logo_img, text="")
                logo_lbl.pack(side="left", padx=(0, 12))
            except Exception as e:
                print(f"Erro ao carregar imagem do logo: {e}")

        # Texto 'LOJAS NORDESTINA'
        title_lbl = ctk.CTkLabel(
            brand_box,
            text="LOJAS NORDESTINA",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
            text_color=("#111827", "#f9fafb")
        )
        title_lbl.pack(side="left")

        # Divisor vertical fino (idêntico ao print de referência ArtCraft)
        divider = ctk.CTkFrame(brand_box, width=1, height=22, fg_color=("#d0d7de", "#30363d"))
        divider.pack(side="left", padx=16)

        # Nome da Suite de Aplicativos
        suite_lbl = ctk.CTkLabel(
            brand_box,
            text="NORDESTINA APP SUITE",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color=("#6b7280", "#9ca3af")
        )
        suite_lbl.pack(side="left")

        # --- LADO DIREITO: CONTROLES (Tema, Cartões/Tabela, Verificar, Configurações) ---
        ctrl_box = ctk.CTkFrame(header_box, fg_color="transparent")
        ctrl_box.pack(side="right")

        # Botão Alternador de Modo Claro / Escuro
        theme_icon_text = "🌙 Escuro" if self.appearance_mode == "dark" else "☀️ Claro"
        self.btn_theme = ctk.CTkButton(
            ctrl_box,
            text=theme_icon_text,
            width=90,
            height=34,
            corner_radius=8,
            fg_color=("#f3f4f6", "#21262d"),
            hover_color=("#e5e7eb", "#30363d"),
            text_color=("#1f2328", "#f0f6fc"),
            border_width=1,
            border_color=("#d0d7de", "#30363d"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_theme
        )
        self.btn_theme.pack(side="left", padx=(0, 12))

        # Alternador Cartões / Tabela
        view_toggle_frame = ctk.CTkFrame(ctrl_box, fg_color=("#eaeef2", "#21262d"), corner_radius=8)
        view_toggle_frame.pack(side="left", padx=(0, 14))

        self.btn_view_cards = ctk.CTkButton(
            view_toggle_frame,
            text="🔲 Cartões",
            width=85,
            height=30,
            corner_radius=6,
            fg_color="#1f6feb" if self.config.get("view_mode") == "cards" else "transparent",
            hover_color="#1857ba",
            text_color="#ffffff" if self.config.get("view_mode") == "cards" else ("#24292f", "#f0f6fc"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._set_view_mode("cards")
        )
        self.btn_view_cards.pack(side="left", padx=2, pady=2)

        self.btn_view_table = ctk.CTkButton(
            view_toggle_frame,
            text="📋 Tabela",
            width=85,
            height=30,
            corner_radius=6,
            fg_color="#1f6feb" if self.config.get("view_mode") == "table" else "transparent",
            hover_color="#1857ba",
            text_color="#ffffff" if self.config.get("view_mode") == "table" else ("#24292f", "#f0f6fc"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._set_view_mode("table")
        )
        self.btn_view_table.pack(side="left", padx=2, pady=2)

        # Botão Verificar
        self.btn_refresh = ctk.CTkButton(
            ctrl_box,
            text="🔄 Verificar",
            width=95,
            height=34,
            corner_radius=8,
            fg_color=("#f3f4f6", "#21262d"),
            hover_color=("#e5e7eb", "#30363d"),
            text_color=("#1f2328", "#f0f6fc"),
            border_width=1,
            border_color=("#d0d7de", "#30363d"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.start_update_check
        )
        self.btn_refresh.pack(side="left", padx=(0, 10))

        # Botão Atualizar Todos
        self.btn_update_all = ctk.CTkButton(
            ctrl_box,
            text="⚡ Atualizar Todos",
            width=135,
            height=34,
            corner_radius=8,
            fg_color="#238636",
            hover_color="#2ea043",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.update_all_apps
        )
        self.btn_update_all.pack(side="left", padx=(0, 10))

        # Botão Configurações
        self.btn_config = ctk.CTkButton(
            ctrl_box,
            text="⚙️ Configurações",
            width=120,
            height=34,
            corner_radius=8,
            fg_color=("#f3f4f6", "#21262d"),
            hover_color=("#e5e7eb", "#30363d"),
            text_color=("#1f2328", "#f0f6fc"),
            border_width=1,
            border_color=("#d0d7de", "#30363d"),
            font=ctk.CTkFont(size=12),
            command=self._open_settings
        )
        self.btn_config.pack(side="left")

        # 2. Banner de Atualização do Launcher
        self.launcher_banner = ctk.CTkFrame(self, fg_color=("#fff8c5", "#3b2b10"), height=42, corner_radius=0)
        self.launcher_banner_label = ctk.CTkLabel(
            self.launcher_banner,
            text="🔔 Nova atualização do Hub Launcher disponível!",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#9a6700", "#ffd166")
        )
        self.launcher_banner_label.pack(side="left", padx=25)

        self.btn_banner_update = ctk.CTkButton(
            self.launcher_banner,
            text="Atualizar Launcher",
            height=26,
            width=130,
            corner_radius=6,
            fg_color="#e3b341",
            text_color="#000000",
            hover_color="#c99c32",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._update_launcher_self
        )
        self.btn_banner_update.pack(side="right", padx=25)

        # 3. Área Central Rolável (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(15, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # 4. Rodapé
        footer_frame = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color=("#f0f2f5", "#0d1117"))
        footer_frame.grid(row=3, column=0, sticky="ew")

        self.lbl_status = ctk.CTkLabel(footer_frame, text="Pronto.", font=ctk.CTkFont(size=11), text_color=("#57606a", "#8b949e"))
        self.lbl_status.pack(side="left", padx=25, pady=6)

        lbl_version_info = ctk.CTkLabel(
            footer_frame,
            text=f"NORDESTINA APP SUITE {self.config.get('launcher_version', 'v1.0.0')} • Criado por {self.config.get('creator', 'Evandro Magno')}",
            font=ctk.CTkFont(size=11),
            text_color=("#57606a", "#8b949e")
        )
        lbl_version_info.pack(side="right", padx=25, pady=6)

    def _toggle_theme(self):
        """Alterna entre modo escuro e claro."""
        new_mode = "light" if self.appearance_mode == "dark" else "dark"
        self.appearance_mode = new_mode
        ctk.set_appearance_mode(new_mode)
        self.config["appearance_mode"] = new_mode
        config_manager.save_config(self.config)

        self.btn_theme.configure(text="🌙 Escuro" if new_mode == "dark" else "☀️ Claro")
        self._render_view()

    def _calculate_columns(self):
        """
        Calcula o número de colunas: de 4 a 5 apps por linha (máximo 5) e os demais abaixo.
        """
        try:
            w = self.winfo_width()
        except Exception:
            w = 0

        if w < 400:
            try:
                w = self.winfo_screenwidth()
            except Exception:
                w = 1200

        # Para telas >= 1440px (como Full HD 1920 e 1536x864): exatamente 5 colunas
        # Para telas entre 1080px e 1440px: 4 colunas
        # Para telas menores: 3 ou 2
        # Máximo absoluto de 5 colunas por linha para não cortar nenhum aplicativo!
        if w >= 1440:
            return 5
        elif w >= 1080:
            return 4
        elif w >= 800:
            return 3
        else:
            return 2

    def _on_window_configure(self, event):
        """Re-organiza os cartões dinamicamente quando a tela é maximizada ou redimensionada."""
        if event.widget == self:
            if self._resize_job:
                self.after_cancel(self._resize_job)
            self._resize_job = self.after(120, self._check_column_reflow)

    def _check_column_reflow(self):
        new_cols = self._calculate_columns()
        if self._current_columns != new_cols:
            self._current_columns = new_cols
            if self.config.get("view_mode", "cards") == "cards":
                self._render_view()

    def _set_view_mode(self, mode):
        self.config["view_mode"] = mode
        config_manager.save_config(self.config)

        if mode == "cards":
            self.btn_view_cards.configure(fg_color="#1f6feb", text_color="#ffffff")
            self.btn_view_table.configure(fg_color="transparent", text_color=("#24292f", "#f0f6fc"))
        else:
            self.btn_view_cards.configure(fg_color="transparent", text_color=("#24292f", "#f0f6fc"))
            self.btn_view_table.configure(fg_color="#1f6feb", text_color="#ffffff")

        self._render_view()

    def _render_view(self):
        """Renderiza a visualização separando em Instalados (topo) e Disponíveis (baixo)."""
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        self.app_cards.clear()
        self.table_rows.clear()

        mode = self.config.get("view_mode", "cards")
        projects = self.config.get("projects", [])

        installed_list = []
        available_list = []

        for p in projects:
            installed = installer_service.is_project_installed(
                p["id"], p["name"], p.get("keywords"), p.get("fallback_exe")
            )
            if installed:
                installed_list.append(p)
            else:
                available_list.append(p)

        if mode == "cards":
            self._render_cards_mode(installed_list, available_list)
        else:
            self._render_table_mode(installed_list, available_list)

    def _render_cards_mode(self, installed_list, available_list):
        """
        Modo Cartões: Organiza os projetos lado a lado aproveitando toda a largura da tela!
        """
        cols = self._calculate_columns()
        self._current_columns = cols

        # Seção 1: INSTALADOS NO COMPUTADOR
        sec1_header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        sec1_header.pack(fill="x", pady=(5, 10))

        lbl_sec1 = ctk.CTkLabel(
            sec1_header,
            text=f"💻  INSTALADOS NO COMPUTADOR ({len(installed_list)})",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#1a7f37", "#56d364")
        )
        lbl_sec1.pack(side="left")

        grid_frame1 = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid_frame1.pack(fill="x", pady=(0, 25))

        if installed_list:
            for idx, p in enumerate(installed_list):
                col = idx % cols
                row = idx // cols
                r_info = self.releases_cache.get(p["id"])
                card = SquareAppCard(
                    grid_frame1,
                    project_data=p,
                    is_installed=True,
                    release_info=r_info,
                    on_action=self._handle_action
                )
                self.app_cards[p["id"]] = card
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nw")
        else:
            empty_lbl = ctk.CTkLabel(
                grid_frame1,
                text="Nenhum programa instalado ainda. Veja as opções disponíveis abaixo para instalar.",
                font=ctk.CTkFont(size=12),
                text_color=("#57606a", "#8b949e")
            )
            empty_lbl.pack(pady=10)

        # Seção 2: DISPONÍVEIS PARA INSTALAR
        sec2_header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        sec2_header.pack(fill="x", pady=(10, 10))

        lbl_sec2 = ctk.CTkLabel(
            sec2_header,
            text=f"🌐  DISPONÍVEIS PARA INSTALAR ({len(available_list)})",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#0969da", "#79b8ff")
        )
        lbl_sec2.pack(side="left")

        grid_frame2 = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid_frame2.pack(fill="x", pady=(0, 20))

        if available_list:
            for idx, p in enumerate(available_list):
                col = idx % cols
                row = idx // cols
                r_info = self.releases_cache.get(p["id"])
                card = SquareAppCard(
                    grid_frame2,
                    project_data=p,
                    is_installed=False,
                    release_info=r_info,
                    on_action=self._handle_action
                )
                self.app_cards[p["id"]] = card
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nw")
        else:
            all_lbl = ctk.CTkLabel(
                grid_frame2,
                text="Todos os projetos corporativos já estão instalados no seu computador!",
                font=ctk.CTkFont(size=12),
                text_color=("#1a7f37", "#56d364")
            )
            all_lbl.pack(pady=10)

    def _render_table_mode(self, installed_list, available_list):
        """Modo Tabela elegante."""
        def _render_group(title, color, items, is_inst):
            header = ctk.CTkLabel(self.scroll_frame, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=color)
            header.pack(anchor="w", pady=(10, 8))

            table_card = ctk.CTkFrame(self.scroll_frame, fg_color=("#ffffff", "#1e222b"), corner_radius=10, border_width=1, border_color=("#d0d7de", "#2d3340"))
            table_card.pack(fill="x", pady=(0, 15))

            thead = ctk.CTkFrame(table_card, fg_color=("#f3f4f6", "#252a36"), corner_radius=0, height=36)
            thead.pack(fill="x")
            thead.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(thead, text="Aplicativo", font=ctk.CTkFont(size=11, weight="bold"), width=240, anchor="w").pack(side="left", padx=(15, 10), pady=6)
            ctk.CTkLabel(thead, text="Status & Versão", font=ctk.CTkFont(size=11, weight="bold"), width=160, anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(thead, text="Descrição / Release", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=6)
            ctk.CTkLabel(thead, text="Ação", font=ctk.CTkFont(size=11, weight="bold"), width=130, anchor="center").pack(side="right", padx=(10, 15), pady=6)

            if not items:
                ctk.CTkLabel(table_card, text="Nenhum item nesta seção.", font=ctk.CTkFont(size=11), text_color=("#57606a", "#8b949e")).pack(pady=12)
                return

            for p in items:
                row = ctk.CTkFrame(table_card, fg_color="transparent", height=48)
                row.pack(fill="x", pady=2)

                name_frame = ctk.CTkFrame(row, fg_color="transparent", width=240)
                name_frame.pack(side="left", padx=(15, 10), fill="y")
                ctk.CTkLabel(name_frame, text=f"{p.get('icon_emoji', '📊')} {p['name']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#1f2328", "#f0f6fc"), anchor="w").pack(anchor="w", pady=(8, 0))

                r_info = self.releases_cache.get(p["id"]) or {}
                curr_ver = installer_service.read_installed_version(p["id"]) or p.get("installed_version", "v1.0.0")
                latest_tag = r_info.get("tag_name", curr_ver)
                has_update = r_info.get("success") and github_service.is_newer_version(latest_tag, curr_ver)

                status_box = ctk.CTkFrame(row, fg_color="transparent", width=160)
                status_box.pack(side="left", padx=10)

                if not is_inst:
                    txt = "DISPONÍVEL"
                    bg, fg = ("#fff8c5", "#382d18"), ("#9a6700", "#e3b341")
                elif has_update:
                    txt = f"Nova: {latest_tag}"
                    bg, fg = ("#ffedd5", "#3b2b1a"), ("#c2410c", "#ffa657")
                else:
                    txt = f"Atualizado ({curr_ver})"
                    bg, fg = ("#dafbe1", "#183424"), ("#1a7f37", "#56d364")

                ctk.CTkLabel(status_box, text=f" {txt} ", fg_color=bg, text_color=fg, corner_radius=6, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(10, 0))

                desc_box = ctk.CTkFrame(row, fg_color="transparent")
                desc_box.pack(side="left", fill="x", expand=True, padx=10)
                body = (r_info.get("body", p.get("description", ""))[:75] + "...") if is_inst and has_update else p.get("description", "")
                ctk.CTkLabel(desc_box, text=body, font=ctk.CTkFont(size=11), text_color=("#57606a", "#8b949e"), anchor="w").pack(anchor="w", pady=(10, 0))

                act_box = ctk.CTkFrame(row, fg_color="transparent", width=130)
                act_box.pack(side="right", padx=(10, 15))

                if not is_inst:
                    b = ctk.CTkButton(act_box, text="⬇ Instalar", width=100, height=28, fg_color="#1f6feb", font=ctk.CTkFont(size=11, weight="bold"), command=lambda pr=p, ri=r_info: self._handle_action("install", pr, ri))
                elif has_update:
                    b = ctk.CTkButton(act_box, text="⚡ Atualizar", width=100, height=28, fg_color="#238636", font=ctk.CTkFont(size=11, weight="bold"), command=lambda pr=p, ri=r_info: self._handle_action("update", pr, ri))
                else:
                    b = ctk.CTkButton(
                        act_box,
                        text="▶ Abrir",
                        width=100,
                        height=28,
                        fg_color=("#f3f4f6", "#21262d"),
                        hover_color=("#e5e7eb", "#30363d"),
                        text_color=("#1f2328", "#f0f6fc"),
                        border_width=1,
                        border_color=("#d0d7de", "#384252"),
                        font=ctk.CTkFont(size=11, weight="bold"),
                        command=lambda pr=p, ri=r_info: self._handle_action("open", pr, ri)
                    )
                b.pack(pady=6)

        _render_group(f"💻  INSTALADOS NO COMPUTADOR ({len(installed_list)})", ("#1a7f37", "#56d364"), installed_list, True)
        _render_group(f"🌐  DISPONÍVEIS PARA INSTALAR ({len(available_list)})", ("#0969da", "#79b8ff"), available_list, False)

    def _handle_action(self, action_type, project_data, release_info):
        """Gerencia os cliques nos botões ABRIR, INSTALAR e ATUALIZAR."""
        if action_type == "open":
            project_id = project_data.get("id", "")
            project_name = project_data.get("name", "")

            # Procedimento especial para aplicativos com inicialização mais pesada (ex: CIC Reformulado)
            if project_id in ["cic", "mysoft"] or "reformulado" in project_name.lower():
                self._update_project_progress(project_id, 0.2, "Inicializando...")
                self.lbl_status.configure(text=f"Inicializando {project_name}... Aguarde alguns instantes.")

                def on_done():
                    self._clear_project_progress(project_id)
                    self.lbl_status.configure(text=f"{project_name} em execução.")

                # Abre janela dedicada do procedimento de inicialização
                startup_dlg = ProjectStartupDialog(
                    self,
                    project_name=project_name,
                    icon_emoji=project_data.get("icon_emoji", "🏢"),
                    estimated_seconds=8,
                    on_complete=on_done
                )

                def run_launch():
                    ok, msg = installer_service.launch_project(
                        project_data["id"],
                        project_data["name"],
                        project_data.get("keywords"),
                        project_data.get("fallback_exe")
                    )
                    if not ok:
                        self.after(0, lambda: messagebox.showerror("Erro ao Abrir", f"{msg}"))
                        self.after(0, lambda: self._clear_project_progress(project_id))
                        try:
                            startup_dlg.close_dialog()
                        except Exception:
                            pass

                threading.Thread(target=run_launch, daemon=True).start()
            else:
                self._update_project_progress(project_id, 0.5, "Iniciando...")
                def run_quick():
                    ok, msg = installer_service.launch_project(
                        project_data["id"],
                        project_data["name"],
                        project_data.get("keywords"),
                        project_data.get("fallback_exe")
                    )
                    if ok:
                        self.after(0, lambda: self.lbl_status.configure(text=f"Iniciado com sucesso: {project_data['name']}"))
                    else:
                        self.after(0, lambda: messagebox.showerror("Erro ao Abrir", f"{msg}\n\nTente instalar ou atualizar o aplicativo."))
                    self.after(2000, lambda: self._clear_project_progress(project_id))

                threading.Thread(target=run_quick, daemon=True).start()

        elif action_type in ["install", "update"]:
            self._do_install_or_update(project_data, release_info)

    def _update_project_progress(self, project_id, fraction, text=""):
        try:
            if project_id in self.app_cards:
                self.app_cards[project_id].show_progress(fraction, text)
            if project_id in self.table_rows:
                lbl = self.table_rows[project_id]
                lbl.configure(text=text)
        except Exception:
            pass

    def _clear_project_progress(self, project_id):
        try:
            if project_id in self.app_cards:
                self.app_cards[project_id].hide_progress()
        except Exception:
            pass

    def _do_install_or_update(self, project_data, release_info, on_complete=None):
        """Baixa o zip/exe da release privada automaticamente com progresso e instala!"""
        if not release_info:
            messagebox.showwarning("Aviso", "Aguarde a checagem com o GitHub ser concluída.")
            return

        assets = release_info.get("assets", [])
        tag_name = release_info.get("tag_name", "v1.0.0")

        if not assets:
            html_url = release_info.get("html_url", "")
            resp = messagebox.askyesno(
                "Nenhum arquivo compilado anexado",
                f"A release {tag_name} no GitHub ainda não possui um arquivo .zip ou .exe anexado aos Assets.\n\nDeseja abrir a página da release para visualizar?"
            )
            if resp and html_url:
                webbrowser.open(html_url)
            return

        token = self.config.get("github_token", "")
        asset = github_service.find_asset_for_download(assets, preferred_name=project_data.get("name")) or assets[0]
        download_url = asset.get("url") if (token and asset.get("url")) else asset.get("browser_download_url")
        asset_name = asset.get("name", "app.zip")
        p_id = project_data["id"]
        self.lbl_status.configure(text=f"Baixando {asset_name} ({tag_name})...")
        self.btn_refresh.configure(state="disabled")
        if hasattr(self, "btn_update_all"):
            self.btn_update_all.configure(state="disabled")

        def _worker():
            temp_dir = tempfile.gettempdir()
            dest_temp_path = os.path.join(temp_dir, asset_name)

            def _progress(fraction, downloaded=0, total_size=0):
                if total_size > 0:
                    mb_down = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    pct = int(fraction * 100)
                    text = f"Baixando: {pct}% ({mb_down:.1f}/{mb_total:.1f} MB)"
                else:
                    text = f"Baixando: {int(fraction * 100)}%"
                self.after(0, lambda f=fraction, t=text: self._update_project_progress(p_id, f, t))

            ok, msg = github_service.download_release_asset(download_url, dest_temp_path, token=token, progress_callback=_progress)
            if not ok:
                def _err():
                    self._clear_project_progress(p_id)
                    messagebox.showerror("Erro no Download", f"Falha ao baixar da release privada:\n{msg}")
                    self.lbl_status.configure(text="Falha no download.")
                    self.btn_refresh.configure(state="normal")
                    if hasattr(self, "btn_update_all"):
                        self.btn_update_all.configure(state="normal")
                self.after(0, _err)
                return

            self.after(0, lambda: self._update_project_progress(p_id, 1.0, "Instalando e criando atalhos..."))
            self.lbl_status.configure(text=f"Instalando {project_data['name']}...")
            ok_inst, exe_path = installer_service.install_or_update_package(
                project_data["id"],
                project_data["name"],
                dest_temp_path,
                tag_name
            )

            try:
                if os.path.exists(dest_temp_path):
                    os.remove(dest_temp_path)
            except Exception:
                pass

            def _success():
                self._clear_project_progress(p_id)
                self.btn_refresh.configure(state="normal")
                if hasattr(self, "btn_update_all"):
                    self.btn_update_all.configure(state="normal")
                self.lbl_status.configure(text=f"✔ {project_data['name']} instalado com sucesso!")
                messagebox.showinfo(
                    "Sucesso!",
                    f"O projeto '{project_data['name']}' foi instalado/atualizado com sucesso na versão {tag_name}!\n\nO atalho foi criado/atualizado na sua Área de Trabalho."
                )
                self._render_view()
                if on_complete:
                    on_complete()
            self.after(0, _success)

        threading.Thread(target=_worker, daemon=True).start()

    def update_all_apps(self):
        """Atualiza todos os aplicativos desatualizados sequencialmente com barra de progresso."""
        if self.is_checking:
            messagebox.showinfo("Aguarde", "Aguarde a verificação de atualizações ser concluída.")
            return

        projects = self.config.get("projects", [])
        to_update = []
        for p in projects:
            p_id = p["id"]
            r_info = self.releases_cache.get(p_id)
            if not r_info or not r_info.get("success"):
                continue
            curr_ver = installer_service.read_installed_version(p_id) or p.get("installed_version", "v1.0.0")
            latest_tag = r_info.get("tag_name")
            if github_service.is_newer_version(latest_tag, curr_ver):
                to_update.append((p, r_info, curr_ver, latest_tag))

        if not to_update:
            messagebox.showinfo(
                "Tudo Atualizado",
                "Todos os aplicativos instalados já estão em sua versão mais recente!"
            )
            return

        msg_list = "\n".join([f"• {p['name']}: {cv} ➔ {lt}" for p, r, cv, lt in to_update])
        resp = messagebox.askyesno(
            "Atualizar Todos os Aplicativos",
            f"As seguintes {len(to_update)} atualizações foram encontradas:\n\n{msg_list}\n\nDeseja atualizar todos agora de forma automática?"
        )
        if not resp:
            return

        self.btn_update_all.configure(state="disabled", text="⏳ Atualizando...")
        self.btn_refresh.configure(state="disabled")

        def _bulk_worker():
            token = self.config.get("github_token", "")
            success_count = 0
            fail_count = 0

            for idx, (p, r_info, curr_ver, tag_name) in enumerate(to_update, 1):
                p_id = p["id"]
                p_name = p["name"]
                self.after(0, lambda i=idx, n=len(to_update), nm=p_name: self.lbl_status.configure(text=f"Atualizando [{i}/{n}]: {nm}..."))

                assets = r_info.get("assets", [])
                if not assets:
                    fail_count += 1
                    continue

                asset = github_service.find_asset_for_download(assets, preferred_name=p_name) or assets[0]
                download_url = asset.get("url") if (token and asset.get("url")) else asset.get("browser_download_url")
                asset_name = asset.get("name", f"{p_id}.zip")
                dest_temp_path = os.path.join(tempfile.gettempdir(), asset_name)

                def _prog(fraction, downloaded=0, total_size=0, cur_pid=p_id):
                    if total_size > 0:
                        mb_d = downloaded / (1024 * 1024)
                        mb_t = total_size / (1024 * 1024)
                        pct = int(fraction * 100)
                        t = f"Baixando: {pct}% ({mb_d:.1f}/{mb_t:.1f} MB)"
                    else:
                        t = f"Baixando: {int(fraction * 100)}%"
                    self.after(0, lambda f=fraction, txt=t, pid=cur_pid: self._update_project_progress(pid, f, txt))

                ok, err = github_service.download_release_asset(download_url, dest_temp_path, token=token, progress_callback=_prog)
                if not ok:
                    fail_count += 1
                    self.after(0, lambda pid=p_id: self._clear_project_progress(pid))
                    continue

                self.after(0, lambda pid=p_id: self._update_project_progress(pid, 1.0, "Instalando..."))
                ok_inst, _ = installer_service.install_or_update_package(p_id, p_name, dest_temp_path, tag_name)
                try:
                    if os.path.exists(dest_temp_path):
                        os.remove(dest_temp_path)
                except Exception:
                    pass

                self.after(0, lambda pid=p_id: self._clear_project_progress(pid))
                if ok_inst:
                    success_count += 1
                else:
                    fail_count += 1

            def _finish_bulk():
                self.btn_update_all.configure(state="normal", text="⚡ Atualizar Todos")
                self.btn_refresh.configure(state="normal")
                self.lbl_status.configure(text=f"Atualização concluída: {success_count} atualizados com sucesso.")
                self._render_view()
                messagebox.showinfo(
                    "Atualização Concluída",
                    f"Processo finalizado!\n\n✔ Atualizados com sucesso: {success_count}\n" + (f"✖ Falhas: {fail_count}" if fail_count else "Todos os aplicativos foram atualizados para suas últimas versões!")
                )

            self.after(0, _finish_bulk)

        threading.Thread(target=_bulk_worker, daemon=True).start()

    def start_update_check(self):
        """Consulta as releases de todos os projetos e do próprio Launcher no GitHub."""
        if self.is_checking:
            return
        self.is_checking = True
        self.btn_refresh.configure(state="disabled", text="⏳ Verificando...")
        self.lbl_status.configure(text="Consultando repositórios no GitHub...")

        threading.Thread(target=self._run_check_worker, daemon=True).start()

    def _run_check_worker(self):
        token = self.config.get("github_token", "")
        projects = self.config.get("projects", [])

        # Checa os Projetos
        for proj in projects:
            repo = proj.get("repo")
            res = github_service.get_latest_release(repo, token=token)
            self.releases_cache[proj["id"]] = res

            if res.get("success"):
                tag = res.get("tag_name")
                curr_ver = installer_service.read_installed_version(proj["id"]) or proj.get("installed_version", "v1.0.0")
                is_inst = installer_service.is_project_installed(proj["id"], proj["name"], proj.get("keywords"), proj.get("fallback_exe"))

                if is_inst and github_service.is_newer_version(tag, curr_ver):
                    if self.last_notified.get(proj["id"]) != tag:
                        self.last_notified[proj["id"]] = tag
                        notifier.show_update_notification(proj["name"], tag)

            time.sleep(0.2)

        # Checa atualização do próprio Launcher
        launcher_repo = self.config.get("launcher_repo", __default_repo__)
        current_launcher_ver = self.config.get("launcher_version", __version__)
        l_res = github_service.get_latest_release(launcher_repo, token=token)

        # Sincroniza catálogo remoto de aplicativos se disponível no repositório
        try:
            remote_catalog = github_service.fetch_remote_catalog(launcher_repo, token=token)
            if remote_catalog:
                merged = config_manager.merge_projects(self.config.get("projects", []), remote_catalog)
                self.config["projects"] = merged
                config_manager.save_config(self.config)
        except Exception as e:
            print(f"Catálogo remoto de aplicativos não sincronizado: {e}")

        def _update_ui():
            self.is_checking = False
            self.btn_refresh.configure(state="normal", text="🔄 Verificar")
            now_str = datetime.now().strftime("%H:%M:%S")
            self.lbl_status.configure(text=f"Última verificação: {now_str}.")

            if l_res.get("success") and github_service.is_newer_version(l_res.get("tag_name"), current_launcher_ver):
                l_tag = l_res.get("tag_name")
                self.launcher_update_info = l_res
                self.launcher_banner_label.configure(
                    text=f"🚀 Nova versão da Nordestina App Suite disponível ({l_tag})! Clique para atualizar."
                )
                self.launcher_banner.grid(row=1, column=0, sticky="ew")

                if self.last_notified.get("launcher") != l_tag:
                    self.last_notified["launcher"] = l_tag
                    notifier.show_update_notification("Nordestina App Suite", l_tag)
            else:
                self.launcher_banner.grid_forget()

            self._render_view()

        self.after(0, _update_ui)

    def _update_launcher_self(self):
        if not self.launcher_update_info:
            return

        tag_name = self.launcher_update_info.get("tag_name", "nova versão")
        assets = self.launcher_update_info.get("assets", [])
        html_url = self.launcher_update_info.get("html_url", "")

        asset = github_service.find_asset_for_download(assets, preferred_name="NordestinaAppSuite")
        if not asset:
            resp = messagebox.askyesno(
                "Nenhum executável anexado",
                f"A release {tag_name} da Nordestina App Suite ainda não possui um executável .exe anexado aos Assets no GitHub.\n\nDeseja abrir a página da release no navegador?"
            )
            if resp and html_url:
                webbrowser.open(html_url)
            return

        confirm = messagebox.askyesno(
            "Atualizar Nordestina App Suite",
            f"Uma nova versão da Nordestina App Suite ({tag_name}) está disponível!\n\n"
            f"Deseja atualizar automaticamente agora?\n\n"
            f"O aplicativo fará o download e reiniciará já atualizado."
        )
        if not confirm:
            return

        self._start_launcher_update_process(asset, tag_name)

    def _start_launcher_update_process(self, asset, tag_name):
        """Abre janela de progresso e executa a auto-atualização da Suite em segundo plano."""
        update_win = ctk.CTkToplevel(self)
        update_win.title("Atualizando Nordestina App Suite")
        update_win.geometry("480x230")
        update_win.resizable(False, False)
        update_win.transient(self)
        update_win.grab_set()

        # Centraliza a janela modal
        update_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 240
        y = self.winfo_y() + (self.winfo_height() // 2) - 115
        update_win.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            update_win,
            text=f"🚀 Atualizando Nordestina App Suite para {tag_name}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(padx=20, pady=(20, 10))

        lbl_status = ctk.CTkLabel(
            update_win,
            text="Iniciando download da nova versão...",
            font=ctk.CTkFont(size=12)
        )
        lbl_status.pack(padx=20, pady=(0, 10))

        progress_bar = ctk.CTkProgressBar(update_win, width=400, height=14)
        progress_bar.pack(padx=20, pady=(0, 8))
        progress_bar.set(0.0)

        lbl_pct = ctk.CTkLabel(
            update_win,
            text="Aguardando conexão...",
            font=ctk.CTkFont(size=11),
            text_color=("#57606a", "#8b949e")
        )
        lbl_pct.pack(padx=20, pady=(0, 15))

        def _worker():
            token = self.config.get("github_token", "")
            download_url = asset.get("url") or asset.get("browser_download_url")
            asset_name = asset.get("name", "NordestinaAppSuite.exe")
            temp_dest = os.path.join(tempfile.gettempdir(), asset_name)

            def _progress(fraction, downloaded=0, total_size=0):
                def _ui_update():
                    try:
                        if update_win.winfo_exists():
                            progress_bar.set(fraction)
                            if total_size > 0:
                                mb_down = downloaded / (1024 * 1024)
                                mb_total = total_size / (1024 * 1024)
                                pct = int(fraction * 100)
                                lbl_pct.configure(text=f"{pct}% ({mb_down:.1f} MB de {mb_total:.1f} MB)")
                            else:
                                lbl_pct.configure(text=f"{int(fraction * 100)}%")
                    except Exception:
                        pass
                self.after(0, _ui_update)

            ok, msg = github_service.download_release_asset(download_url, temp_dest, token=token, progress_callback=_progress)
            if not ok:
                def _on_err():
                    try:
                        update_win.destroy()
                    except Exception:
                        pass
                    messagebox.showerror("Erro na Atualização", f"Falha ao baixar nova versão da Suite:\n{msg}")
                self.after(0, _on_err)
                return

            def _applying():
                try:
                    if update_win.winfo_exists():
                        lbl_status.configure(text="Aplicando nova versão e reiniciando...")
                        progress_bar.set(1.0)
                        lbl_pct.configure(text="Download concluído! Reiniciando aplicativo...")
                except Exception:
                    pass
            self.after(0, _applying)
            time.sleep(1.0)

            # Aplica a substituição do executável
            ok_apply, err_apply = installer_service.apply_launcher_update(temp_dest, tag_name)
            if not ok_apply:
                def _on_apply_err():
                    try:
                        update_win.destroy()
                    except Exception:
                        pass
                    messagebox.showerror("Erro ao Aplicar", f"Não foi possível substituir o executável:\n{err_apply}")
                self.after(0, _on_apply_err)
            else:
                # Se estiver rodando em desenvolvimento (script python), fecha a janela e avisa
                def _on_script_done():
                    try:
                        update_win.destroy()
                    except Exception:
                        pass
                    messagebox.showinfo("Sucesso", err_apply)
                    self.start_update_check()
                self.after(0, _on_script_done)

        threading.Thread(target=_worker, daemon=True).start()

    def _schedule_auto_check(self):
        interval_min = self.config.get("check_interval_minutes", 60)
        delay_ms = max(interval_min * 60 * 1000, 60000)
        self.after(delay_ms, self._on_auto_check)

    def _on_auto_check(self):
        self.start_update_check()
        self._schedule_auto_check()

    def _open_settings(self):
        SettingsWindow(self, self.config, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self):
        self.config = config_manager.load_config()
        self.start_update_check()

    def _on_close(self):
        if self.config.get("minimize_to_tray", True):
            self.withdraw()
            self._setup_tray_icon()
        else:
            self.destroy()

    def _setup_tray_icon(self):
        if self.tray_icon:
            return
        import pystray
        png_path = os.path.join(self.base_dir, "assets", "app_icon.png")
        if os.path.exists(png_path):
            image = Image.open(png_path).convert('RGB')
        else:
            image = Image.new('RGB', (64, 64), color=(31, 111, 235))
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))

        menu = (
            pystray.MenuItem("Abrir Nordestina App Suite", lambda: self.after(0, self._restore_from_tray), default=True),
            pystray.MenuItem("Verificar Atualizações", lambda: self.after(0, self.start_update_check)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._exit_app)
        )
        self.tray_icon = pystray.Icon("NordestinaAppSuite", image, "NORDESTINA APP SUITE", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _restore_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _exit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
