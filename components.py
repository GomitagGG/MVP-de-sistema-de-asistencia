import tkinter as tk
from tkinter import ttk

from theme import COLORS, FONTS

C = COLORS
F = FONTS


def _fuente(nombre):
    return F.get(nombre, F["body"])


class SurfaceCard(tk.Frame):
    def __init__(self, master, bg=None, radius=14, padding=20, **kwargs):
        bg = bg or C["surface"]
        super().__init__(master, bg=bg, highlightthickness=1,
                         highlightbackground=C["border"], **kwargs)
        self.bg = bg
        self.radius = radius
        self.padding = padding


class PageHeader(tk.Frame):
    def __init__(self, master, titulo, subtitulo="", estado_conexion=None, **kwargs):
        super().__init__(master, bg=C["bg_app"], **kwargs)
        self.col_titulo(0, titulo, subtitulo)
        if estado_conexion:
            self.col_estado(1, estado_conexion)

    def col_titulo(self, col, titulo, subtitulo):
        tk.Label(self, text=titulo, bg=C["bg_app"], fg=C["text_primary"],
                 font=F["page_title"], anchor="w").grid(row=0, column=col, sticky="w")
        if subtitulo:
            tk.Label(self, text=subtitulo, bg=C["bg_app"], fg=C["text_secondary"],
                     font=F["page_subtitle"], anchor="w").grid(row=1, column=col, sticky="w")

    def col_estado(self, col, estado):
        dot = tk.Label(self, text="●", bg=C["bg_app"], fg=C["success"],
                       font=("Segoe UI", 10))
        dot.grid(row=0, column=col, sticky="ne", padx=(0, 8), pady=(6, 0))
        tk.Label(self, text=estado, bg=C["bg_app"], fg=C["text_secondary"],
                 font=F["small"]).grid(row=0, column=col + 1, sticky="ne", pady=(6, 0))


class MetricCard(SurfaceCard):
    def __init__(self, master, titulo, valor, subtitulo="", color=C["info"],
                 icono="reloj", tamano=(267, 120), **kwargs):
        super().__init__(master, padding=18, **kwargs)
        self.titulo = titulo
        self.valor = valor
        self.subtitulo = subtitulo
        self.color = color
        self.icono = icono
        self.config(height=tamano[1])
        if tamano[0]:
            self.config(width=tamano[0])
        self.pack_propagate(False)
        self._dibujar()

    def _dibujar(self):
        for w in self.winfo_children():
            w.destroy()
        import icons
        icono_canvas = icons.crear_icono(
            self.icono, size=28, color=self.color, bg=self.bg, master=self)
        cir = tk.Canvas(self, width=58, height=58, bg=self.bg,
                        highlightthickness=0, bd=0)
        cir.create_oval(3, 3, 55, 55, outline=self.color, width=2)
        cir.create_oval(10, 10, 48, 48, outline=self.color, width=1)
        icono_canvas.place(x=15, y=15)
        cir.grid(row=0, column=0, rowspan=2, padx=(0, 12), pady=6, sticky="w")
        tk.Label(self, text=self.titulo.upper(), bg=self.bg, fg=C["text_secondary"],
                 font=F["small_bold"], anchor="w").grid(row=0, column=1, sticky="sw")
        tk.Label(self, text=str(self.valor), bg=self.bg, fg=C["text_primary"],
                 font=F["metric_value"], anchor="w").grid(row=1, column=1, sticky="nw")
        if self.subtitulo:
            tk.Label(self, text=self.subtitulo, bg=self.bg, fg=C["text_muted"],
                     font=F["small"], anchor="w").grid(
                row=2, column=0, columnspan=2, sticky="sw", pady=(4, 0))
        self.columnconfigure(1, weight=1)


class StatusBadge(tk.Label):
    def __init__(self, master, texto, tipo="info", **kwargs):
        colores = {
            "exito": (C["success"], C["success_bg"]),
            "warning": (C["warning"], C["warning_bg"]),
            "danger": (C["danger"], C["danger_bg"]),
            "info": (C["info"], C["surface_raised"]),
            "neutral": (C["text_secondary"], C["surface_raised"]),
        }
        fg, bg = colores.get(tipo, colores["neutral"])
        super().__init__(master, text=texto, bg=bg, fg=fg, font=F["small_bold"],
                         padx=10, pady=4, **kwargs)


class PrimaryButton(tk.Button):
    def __init__(self, master, texto, command=None, icono=None, deshabilitado=False,
                 loading=False, **kwargs):
        super().__init__(
            master, text=texto, command=command,
            bg=C["accent"], fg=C["white"], activebackground=C["accent_hover"],
            activeforeground=C["white"], relief="flat", bd=0,
            font=F["body_bold"], padx=16, pady=8,
            cursor="hand2", borderwidth=0, highlightthickness=0,
            **kwargs)
        self.c_original = C["accent"]
        self._texto = texto
        self._command = command
        self._icono = icono
        if icono:
            import icons
            ic = icons.crear_icono(icono, size=18, color=C["white"], bg=C["accent"],
                                   master=self)
            ic.place(relx=0.06, rely=0.5, anchor="w")
        if deshabilitado:
            self.set_deshabilitado(True)
        if loading:
            self.set_loading(True)
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))

    def _hover(self, entrar):
        if self["state"] == "disabled":
            return
        self.config(bg=C["accent_hover"] if entrar else C["accent"],
                    activebackground=C["accent_hover"])

    def set_deshabilitado(self, valor):
        self.config(state="disabled" if valor else "normal",
                    bg=C["accent_dark"] if valor else C["accent"])

    def set_loading(self, valor, texto_loading="CARGANDO..."):
        if valor:
            self.config(text=texto_loading, state="disabled", bg=C["accent_dark"])
        else:
            self.config(text=self._texto, state="normal", bg=C["accent"])


class SecondaryButton(tk.Button):
    def __init__(self, master, texto, command=None, **kwargs):
        super().__init__(
            master, text=texto, command=command,
            bg=C["surface_raised"], fg=C["text_primary"],
            activebackground=C["surface_hover"], activeforeground=C["text_primary"],
            relief="flat", bd=0, font=F["body_bold"], padx=16, pady=8,
            cursor="hand2", borderwidth=0, highlightthickness=0, **kwargs)
        self.bind("<Enter>", lambda e: self.config(bg=C["surface_hover"]))
        self.bind("<Leave>", lambda e: self.config(bg=C["surface_raised"]))


class EmptyState(tk.Frame):
    def __init__(self, master, titulo="Sin datos", detalle="", icono="calendario",
                 color=C["text_muted"], **kwargs):
        super().__init__(master, bg=C["surface"], **kwargs)
        import icons
        icono_canvas = icons.crear_icono(icono, size=32, color=color,
                                         bg=C["surface"], master=self)
        icono_canvas.grid(row=0, column=0, pady=(0, 8))
        tk.Label(self, text=titulo, bg=C["surface"], fg=C["text_secondary"],
                 font=F["body_bold"]).grid(row=1, column=0)
        if detalle:
            tk.Label(self, text=detalle, bg=C["surface"], fg=C["text_muted"],
                     font=F["small"]).grid(row=2, column=0, pady=(2, 0))


class Toast(tk.Toplevel):
    def __init__(self, master, mensaje, tipo="exito", duracion=3500):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        colores = {
            "exito": C["success"],
            "error": C["danger"],
            "info": C["info"],
        }
        borde = colores.get(tipo, C["success"])
        self.configure(bg=borde)
        cuerpo = tk.Frame(self, bg=C["surface_raised"])
        cuerpo.pack(padx=1, pady=1, fill="both", expand=True)
        import icons
        dot = tk.Canvas(cuerpo, width=18, height=18, bg=C["surface_raised"],
                        highlightthickness=0, bd=0)
        dot.create_oval(2, 2, 16, 16, fill=borde, outline="")
        if tipo == "exito":
            dot.create_line(5, 9, 8, 12, 13, 6, fill=C["white"], width=2,
                            capstyle="round")
        elif tipo == "error":
            dot.create_line(6, 6, 12, 12, fill=C["white"], width=2)
            dot.create_line(12, 6, 6, 12, fill=C["white"], width=2)
        dot.grid(row=0, column=0, padx=(14, 10), pady=20)
        tk.Label(cuerpo, text=mensaje, bg=C["surface_raised"], fg=C["text_primary"],
                 font=F["body"], anchor="w", justify="left",
                 wraplength=240).grid(row=0, column=1, pady=20, sticky="w")
        cerrar = tk.Label(cuerpo, text="✕", bg=C["surface_raised"],
                          fg=C["text_secondary"], font=("Segoe UI", 12),
                          cursor="hand2", padx=14)
        cerrar.grid(row=0, column=2, pady=20, sticky="e")
        cerrar.bind("<Button-1>", lambda e: self.ocultar())
        cuerpo.columnconfigure(1, weight=1)
        self.bind("<Button-1>", lambda e: self.ocultar())
        self._timer = self.after(duracion, self.ocultar)

    def mostrar(self):
        self.update_idletasks()
        ancho = 380
        alto = 58
        padre_x = self.master.winfo_rootx()
        padre_y = self.master.winfo_rooty()
        padre_ancho = self.master.winfo_width()
        try:
            self.geometry(f"{ancho}x{alto}+{padre_x + padre_ancho - ancho - 24}+{padre_y + 22}")
        except Exception:
            pass
        self.lift()
        self.attributes("-topmost", True)

    def ocultar(self):
        if self._timer:
            self.after_cancel(self._timer)
            self._timer = None
        try:
            self.destroy()
        except Exception:
            pass


def grid_scrollable(master, bg):
    lienzo = tk.Canvas(master, bg=bg, highlightthickness=0, bd=0)
    scroll = ttk.Scrollbar(master, orient="vertical", command=lienzo.yview,
                           style="Dark.Scrollbar")
    lienzo.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    lienzo.pack(side="left", fill="both", expand=True)
    contenido = tk.Frame(lienzo, bg=bg)
    ventana = lienzo.create_window((0, 0), window=contenido, anchor="nw")
    contenido.bind("<Configure>",
                   lambda e: lienzo.configure(scrollregion=lienzo.bbox("all")))
    lienzo.bind("<Configure>",
                lambda e: lienzo.itemconfigure(ventana, width=e.width))
    return lienzo, contenido