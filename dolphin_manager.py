import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import requests

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dolphin_config.json")
LOCAL_API = "http://localhost:3001/v1.0"
CLOUD_API = "https://dolphin-anty-api.com"

DEFAULT_CONFIG = {
    "accounts": [
        {"name": "Conta 1", "api_token": "", "profiles": []},
        {"name": "Conta 2", "api_token": "", "profiles": []},
        {"name": "Conta 3", "api_token": "", "profiles": []},
    ],
    "active_profile_id": None,
}

BG_DARK    = "#0d1117"
BG_CARD    = "#161b22"
BG_HEADER  = "#21262d"
BG_ACTIVE  = "#0d2818"
ACCENT     = "#58a6ff"
GREEN      = "#3fb950"
RED        = "#f85149"
TEXT       = "#c9d1d9"
TEXT_DIM   = "#6e7681"
BORDER     = "#30363d"


class DolphinManager:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Dolphin Anty Manager")
        self.root.geometry("860x540")
        self.root.minsize(700, 420)
        self.root.configure(bg=BG_DARK)

        self.config = self._load_config()
        self.active_profile_id: str | None = self.config.get("active_profile_id")
        self._lock = threading.Lock()

        self._apply_styles()
        self._build_ui()

    # ------------------------------------------------------------------ config

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # backfill missing accounts
                while len(data.get("accounts", [])) < 3:
                    data.setdefault("accounts", []).append(
                        {"name": f"Conta {len(data['accounts'])+1}", "api_token": "", "profiles": []}
                    )
                return data
            except (json.JSONDecodeError, KeyError):
                pass
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    # ----------------------------------------------------------------- styling

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure("TNotebook",        background=BG_DARK,   borderwidth=0)
        s.configure("TNotebook.Tab",    background=BG_HEADER, foreground=TEXT_DIM,
                                        padding=[14, 7],      font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", BG_CARD),  ("active", BG_HEADER)],
              foreground=[("selected", ACCENT),   ("active", TEXT)])

        s.configure("TFrame",      background=BG_DARK)
        s.configure("TScrollbar",  background=BG_CARD,   troughcolor=BG_DARK,
                                   borderwidth=0,         arrowcolor=TEXT_DIM)

        s.configure("Action.TButton",  background=ACCENT,   foreground=BG_DARK,
                                       font=("Segoe UI", 9, "bold"), padding=[10, 4], relief="flat")
        s.map("Action.TButton",
              background=[("active", "#79b8ff"), ("disabled", BG_HEADER)],
              foreground=[("disabled", TEXT_DIM)])

        s.configure("Close.TButton",   background="#2d333b",  foreground=RED,
                                       font=("Segoe UI", 9),  padding=[10, 4], relief="flat")
        s.map("Close.TButton",
              background=[("active", "#3d444b")])

        s.configure("Icon.TButton",    background=BG_HEADER,  foreground=TEXT,
                                       font=("Segoe UI", 9),  padding=[8, 4], relief="flat")
        s.map("Icon.TButton",
              background=[("active", BG_CARD)])

    # ----------------------------------------------------------------- layout

    def _build_ui(self):
        self._build_topbar()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        self._build_tabs()
        self._build_statusbar()

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=BG_HEADER, padx=14, pady=10)
        bar.pack(fill=tk.X)

        tk.Label(bar, text="Dolphin Anty Manager", bg=BG_HEADER, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)

        ttk.Button(bar, text="⚙  Configurações", style="Icon.TButton",
                   command=self._open_settings).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(bar, text="↺  Atualizar Todos", style="Icon.TButton",
                   command=self._refresh_all).pack(side=tk.RIGHT, padx=4)

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="Pronto.")
        bar = tk.Label(self.root, textvariable=self._status_var, bg=BG_HEADER,
                       fg=TEXT_DIM, font=("Segoe UI", 8), anchor=tk.W, padx=12, pady=4)
        bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_tabs(self):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        for idx, account in enumerate(self.config["accounts"]):
            frame = tk.Frame(self.notebook, bg=BG_DARK)
            self.notebook.add(frame, text=f"  {account['name']}  ")
            self._build_account_tab(frame, idx)

    def _build_account_tab(self, parent: tk.Frame, acc_idx: int):
        account = self.config["accounts"][acc_idx]
        has_token = bool(account.get("api_token"))

        # ── tab header ──────────────────────────────────────────────────────
        hdr = tk.Frame(parent, bg=BG_CARD, padx=12, pady=8)
        hdr.pack(fill=tk.X)

        dot_color = GREEN if has_token else RED
        dot_text  = "● Token configurado" if has_token else "● Token não configurado"
        tk.Label(hdr, text=dot_text, bg=BG_CARD, fg=dot_color,
                 font=("Segoe UI", 9)).pack(side=tk.LEFT)

        profile_count = len(account.get("profiles", []))
        tk.Label(hdr, text=f"{profile_count} perfil(s)", bg=BG_CARD, fg=TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=12)

        ttk.Button(hdr, text="↺  Buscar Perfis", style="Icon.TButton",
                   command=lambda i=acc_idx: self._fetch_profiles(i)).pack(side=tk.RIGHT)

        # ── column labels ────────────────────────────────────────────────────
        cols = tk.Frame(parent, bg=BG_HEADER)
        cols.pack(fill=tk.X, padx=2, pady=(2, 0))
        for text, width in [("Nome do Perfil", 34), ("Status", 14), ("Ação", 10)]:
            tk.Label(cols, text=text, bg=BG_HEADER, fg=TEXT_DIM,
                     font=("Segoe UI", 8, "bold"), width=width, anchor=tk.W,
                     padx=8, pady=5).pack(side=tk.LEFT)

        # ── scrollable list ──────────────────────────────────────────────────
        container = tk.Frame(parent, bg=BG_DARK)
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # mouse-wheel support
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        profiles = account.get("profiles", [])
        if not profiles:
            msg = ("Nenhum perfil encontrado.\n"
                   "Configure o token API e clique em '↺ Buscar Perfis'."
                   if not has_token else
                   "Clique em '↺ Buscar Perfis' para carregar os perfis.")
            tk.Label(inner, text=msg, bg=BG_DARK, fg=TEXT_DIM,
                     font=("Segoe UI", 10), pady=30).pack()
        else:
            for profile in profiles:
                self._add_profile_row(inner, profile, acc_idx)

    def _add_profile_row(self, parent: tk.Frame, profile: dict, acc_idx: int):
        pid = str(profile["id"])
        is_active = pid == str(self.active_profile_id)

        row_bg = BG_ACTIVE if is_active else BG_CARD
        row = tk.Frame(parent, bg=row_bg)
        row.pack(fill=tk.X, padx=4, pady=1)

        # separator line
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=4)

        # hover
        def _enter(_e, r=row, bg=row_bg):
            r.configure(bg="#1c2128" if bg == BG_CARD else "#0f3820")
            for w in r.winfo_children():
                try:
                    w.configure(bg=r.cget("bg"))
                except tk.TclError:
                    pass

        def _leave(_e, r=row, bg=row_bg):
            r.configure(bg=bg)
            for w in r.winfo_children():
                try:
                    w.configure(bg=bg)
                except tk.TclError:
                    pass

        row.bind("<Enter>", _enter)
        row.bind("<Leave>", _leave)

        # profile name
        tk.Label(row, text=profile["name"], bg=row_bg, fg=TEXT,
                 font=("Segoe UI", 10), width=34, anchor=tk.W,
                 padx=8, pady=8).pack(side=tk.LEFT)

        # status
        status_text  = "● Ativo"   if is_active else "○ Inativo"
        status_color = GREEN       if is_active else TEXT_DIM
        tk.Label(row, text=status_text, bg=row_bg, fg=status_color,
                 font=("Segoe UI", 9), width=14, anchor=tk.W).pack(side=tk.LEFT)

        # action button
        if is_active:
            ttk.Button(row, text="Fechar", style="Close.TButton",
                       command=lambda p=pid: self._close_profile(p)).pack(side=tk.LEFT, padx=8)
        else:
            ttk.Button(row, text="Abrir", style="Action.TButton",
                       command=lambda p=pid, a=acc_idx: self._open_profile(p, a)).pack(side=tk.LEFT, padx=8)

    # ---------------------------------------------------------- API operations

    def _open_profile(self, profile_id: str, acc_idx: int):
        def _task():
            with self._lock:
                # close existing active profile first
                if self.active_profile_id and self.active_profile_id != profile_id:
                    self._set_status(f"Fechando perfil anterior…")
                    self._api_stop(self.active_profile_id)

                self._set_status(f"Abrindo perfil {profile_id}…")
                ok, msg = self._api_start(profile_id)

                if ok:
                    self.active_profile_id = profile_id
                    self.config["active_profile_id"] = profile_id
                    self._save_config()
                    self._set_status(f"Perfil {profile_id} aberto.")
                    self.root.after(0, self._build_tabs)
                else:
                    self._set_status("Erro ao abrir perfil.")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Erro ao abrir perfil", msg))

        threading.Thread(target=_task, daemon=True).start()

    def _close_profile(self, profile_id: str):
        def _task():
            with self._lock:
                self._set_status(f"Fechando perfil {profile_id}…")
                ok, msg = self._api_stop(profile_id)

                if ok:
                    self.active_profile_id = None
                    self.config["active_profile_id"] = None
                    self._save_config()
                    self._set_status("Perfil fechado.")
                    self.root.after(0, self._build_tabs)
                else:
                    self._set_status("Erro ao fechar perfil.")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Erro ao fechar perfil", msg))

        threading.Thread(target=_task, daemon=True).start()

    def _api_start(self, profile_id: str) -> tuple[bool, str]:
        try:
            resp = requests.get(
                f"{LOCAL_API}/browser_profiles/{profile_id}/start",
                params={"automation": 1, "headless": 0},
                timeout=20,
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("success"):
                return True, ""
            return False, data.get("details") or data.get("message") or str(data)
        except requests.exceptions.ConnectionError:
            return False, (
                "Não foi possível conectar ao Dolphin Anty (localhost:3001).\n"
                "Verifique se o aplicativo está aberto."
            )
        except Exception as exc:
            return False, str(exc)

    def _api_stop(self, profile_id: str) -> tuple[bool, str]:
        try:
            resp = requests.get(
                f"{LOCAL_API}/browser_profiles/{profile_id}/stop",
                timeout=10,
            )
            return resp.status_code == 200, ""
        except Exception as exc:
            return False, str(exc)

    def _fetch_profiles(self, acc_idx: int):
        account = self.config["accounts"][acc_idx]
        if not account.get("api_token"):
            messagebox.showwarning(
                "Token ausente",
                "Configure o token API desta conta em ⚙ Configurações.",
            )
            return

        def _task():
            self._set_status(f"Buscando perfis de '{account['name']}'…")
            try:
                headers = {"Authorization": f"Bearer {account['api_token']}"}
                resp = requests.get(
                    f"{CLOUD_API}/browser_profiles",
                    headers=headers,
                    params={"limit": 50, "page": 1},
                    timeout=15,
                )
                data = resp.json()
                if resp.status_code == 200:
                    raw = data.get("data", [])
                    profiles = [
                        {"id": str(p["id"]), "name": p.get("name", f"Perfil {p['id']}")}
                        for p in raw
                    ]
                    self.config["accounts"][acc_idx]["profiles"] = profiles
                    self._save_config()
                    self._set_status(f"{len(profiles)} perfil(s) carregado(s) para '{account['name']}'.")
                    self.root.after(0, self._build_tabs)
                else:
                    err = data.get("message", "Resposta inesperada da API.")
                    self._set_status("Erro ao buscar perfis.")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Erro API Dolphin", f"Falha ao buscar perfis:\n{err}"))
            except requests.exceptions.ConnectionError:
                self._set_status("Erro de conexão com a API Dolphin.")
                self.root.after(0, lambda: messagebox.showerror(
                    "Erro de Conexão",
                    "Não foi possível conectar à API Dolphin Anty.\n"
                    "Verifique sua conexão com a internet."))
            except Exception as exc:
                self._set_status("Erro inesperado.")
                self.root.after(0, lambda: messagebox.showerror("Erro", str(exc)))

        threading.Thread(target=_task, daemon=True).start()

    def _refresh_all(self):
        for i, acc in enumerate(self.config["accounts"]):
            if acc.get("api_token"):
                self._fetch_profiles(i)

    def _set_status(self, msg: str):
        self.root.after(0, lambda: self._status_var.set(msg))

    # ----------------------------------------------------------- settings modal

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Configurações das Contas")
        win.geometry("520x440")
        win.resizable(False, False)
        win.configure(bg=BG_DARK)
        win.grab_set()
        win.transient(self.root)

        tk.Label(win, text="Configurações das Contas", bg=BG_DARK, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(pady=(16, 4), padx=20, anchor=tk.W)
        tk.Label(win, text="Obtenha seu token em: Dolphin Anty → Automação → API Token",
                 bg=BG_DARK, fg=TEXT_DIM, font=("Segoe UI", 8)).pack(padx=20, anchor=tk.W)

        entries: list[tuple[tk.StringVar, tk.StringVar]] = []

        for i, account in enumerate(self.config["accounts"]):
            card = tk.Frame(win, bg=BG_CARD, padx=12, pady=10)
            card.pack(fill=tk.X, padx=16, pady=6)
            tk.Frame(card, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 8))

            tk.Label(card, text=f"Conta {i + 1}", bg=BG_CARD, fg=ACCENT,
                     font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)

            # name row
            row1 = tk.Frame(card, bg=BG_CARD)
            row1.pack(fill=tk.X, pady=(4, 2))
            tk.Label(row1, text="Nome:", bg=BG_CARD, fg=TEXT_DIM,
                     font=("Segoe UI", 9), width=10, anchor=tk.W).pack(side=tk.LEFT)
            name_var = tk.StringVar(value=account["name"])
            tk.Entry(row1, textvariable=name_var, bg=BG_HEADER, fg=TEXT,
                     insertbackground=TEXT, relief="flat",
                     font=("Segoe UI", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

            # token row
            row2 = tk.Frame(card, bg=BG_CARD)
            row2.pack(fill=tk.X, pady=2)
            tk.Label(row2, text="API Token:", bg=BG_CARD, fg=TEXT_DIM,
                     font=("Segoe UI", 9), width=10, anchor=tk.W).pack(side=tk.LEFT)
            token_var = tk.StringVar(value=account["api_token"])
            token_entry = tk.Entry(row2, textvariable=token_var, bg=BG_HEADER, fg=TEXT,
                                   insertbackground=TEXT, relief="flat", show="●",
                                   font=("Segoe UI", 10))
            token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))

            visible = tk.BooleanVar(value=False)

            def _toggle(e=token_entry, v=visible):
                v.set(not v.get())
                e.config(show="" if v.get() else "●")

            ttk.Button(row2, text="👁", style="Icon.TButton",
                       command=_toggle).pack(side=tk.LEFT)

            entries.append((name_var, token_var))

        def _save():
            for i, (nv, tv) in enumerate(entries):
                self.config["accounts"][i]["name"] = nv.get().strip() or f"Conta {i+1}"
                self.config["accounts"][i]["api_token"] = tv.get().strip()
            self._save_config()
            win.destroy()
            self._build_tabs()

        ttk.Button(win, text="  Salvar  ", style="Action.TButton",
                   command=_save).pack(pady=14)


# --------------------------------------------------------------------------- #

def main():
    root = tk.Tk()
    root.configure(bg=BG_DARK)
    try:
        root.iconbitmap(default="")
    except tk.TclError:
        pass

    app = DolphinManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
