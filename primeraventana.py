import tkinter as tk
from tkinter import font as tkfont
import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore


def ruta_relativa(ruta):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ruta)


COLORES = {
    
    "bg_oscuro":        "#0d1117",
    "panel_izq":        "#161b22",
    "panel_der":        "#0d1117",
    "accento":          "#e94560",
    "accento_hover":    "#ff6b81",
    "accento_oscuro":   "#c81e45",
    "texto_blanco":     "#e6edf3",
    "texto_gris":       "#7d8590",
    "texto_placeholder":"#484f58",
    "entry_bg":         "#161b22",
    "entry_borde":      "#30363d",
    "entry_borde_focus":"#e94560",
    "divider":          "#21262d",
    "sombra":           "#010409",
    "error":            "#f85149",
    "exito":            "#3fb950",
    "titulo_panel":     "#f0f6fc",
    "card_bg":          "#161b22",
}


ANCHO = 820
ALTO = 500


class LoginApp:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(ruta_relativa("config/firebase-key.json"))
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.ventana = tk.Tk()
        self.ventana.title("Sistema de Asistencia")
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self.ventana.overrideredirect(True)
        self.ventana.attributes("-alpha", 0.0)
        self._centrar_ventana(ANCHO, ALTO)
        self.ventana.minsize(ANCHO, ALTO)
        self.ventana.maxsize(ANCHO, ALTO)

        self._usuario_visible = False
        self._animacion_idx = 0
        self._widgets_animar = []

        self._construir_ui()
        self._iniciar_animacion_entrada()

        self._offset_x = 0
        self._offset_y = 0
        self.barra_titulo.bind("<ButtonPress-1>", self._iniciar_arrastre)
        self.barra_titulo.bind("<B1-Motion>", self._arrastrar)

        self.ventana.mainloop()

    def _centrar_ventana(self, w, h):
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.ventana.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_ui(self):
        self._crear_barra_titulo()
        self._crear_panel_izquierdo()
        self._crear_panel_derecho()

    def _crear_barra_titulo(self):
        self.barra_titulo = tk.Frame(self.ventana, bg=COLORES["panel_izq"], height=32)
        self.barra_titulo.pack(fill="x", side="top")
        self.barra_titulo.pack_propagate(False)

        lbl_titulo_bar = tk.Label(
            self.barra_titulo, text="  Sistema de Asistencia",
            bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9), anchor="w",
        )
        lbl_titulo_bar.pack(side="left", padx=(8, 0))

        btn_cerrar = tk.Label(
            self.barra_titulo, text=" \u2715 ", bg=COLORES["panel_izq"],
            fg=COLORES["texto_gris"], font=("Helvetica", 10), cursor="hand2",
        )
        btn_cerrar.pack(side="right", padx=(0, 4))
        btn_cerrar.bind("<Enter>", lambda e: btn_cerrar.config(fg=COLORES["error"]))
        btn_cerrar.bind("<Leave>", lambda e: btn_cerrar.config(fg=COLORES["texto_gris"]))
        btn_cerrar.bind("<Button-1>", lambda e: self.ventana.destroy())

        btn_minimizar = tk.Label(
            self.barra_titulo, text=" \u2013 ", bg=COLORES["panel_izq"],
            fg=COLORES["texto_gris"], font=("Helvetica", 10), cursor="hand2",
        )
        btn_minimizar.pack(side="right")
        btn_minimizar.bind("<Enter>", lambda e: btn_minimizar.config(fg=COLORES["texto_blanco"]))
        btn_minimizar.bind("<Leave>", lambda e: btn_minimizar.config(fg=COLORES["texto_gris"]))
        btn_minimizar.bind("<Button-1>", lambda e: self.ventana.overrideredirect(False))

    def _crear_panel_izquierdo(self):
        self.panel_izq = tk.Frame(self.ventana, bg=COLORES["panel_izq"], width=300)
        self.panel_izq.pack(side="left", fill="y")
        self.panel_izq.pack_propagate(False)

        from PIL import Image, ImageTk, ImageOps
        logo = Image.open(ruta_relativa("img/Fixmol3.png"))
        logo = logo.resize((130, 130))
        logo_tk = ImageTk.PhotoImage(logo)
        lbl_logo = tk.Label(self.panel_izq, image=logo_tk, bg=COLORES["panel_izq"])
        lbl_logo.image = logo_tk
        lbl_logo.pack(pady=(50, 20))

        lbl_titulo = tk.Label(
            self.panel_izq, text="SISTEMA DE\nASISTENCIA",
            bg=COLORES["panel_izq"], fg=COLORES["titulo_panel"],
            font=("Helvetica", 18, "bold"), justify="center",
        )
        lbl_titulo.pack(pady=(0, 10))

        linea = tk.Frame(self.panel_izq, bg=COLORES["accento"], height=2, width=60)
        linea.pack(pady=(0, 16))

        lbl_sub = tk.Label(
            self.panel_izq,
            text="Gestiona tu asistencia de\nforma rapida y segura",
            bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9), justify="center",
        )
        lbl_sub.pack()

    def _crear_panel_derecho(self):
        panel_der = tk.Frame(self.ventana, bg=COLORES["panel_der"])
        panel_der.pack(side="right", fill="both", expand=True)

        frame_form = tk.Frame(panel_der, bg=COLORES["panel_der"])
        frame_form.place(relx=0.5, rely=0.5, anchor="center", width=320, height=400)

        lbl_bienvenido = tk.Label(
            frame_form, text="Bienvenido",
            bg=COLORES["panel_der"], fg=COLORES["texto_blanco"],
            font=("Helvetica", 24, "bold"),
        )
        lbl_bienvenido.pack(pady=(0, 6))

        lbl_sub_bien = tk.Label(
            frame_form, text="Ingresa tus credenciales para continuar",
            bg=COLORES["panel_der"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9),
        )
        lbl_sub_bien.pack(pady=(0, 28))

        self.frame_entry_usuario = self._crear_campo_entry(frame_form, "USUARIO")
        self.entry_usuario = self.frame_entry_usuario[1]
        self.frame_entry_usuario = self.frame_entry_usuario[0]

        frame_clave_container = tk.Frame(frame_form, bg=COLORES["panel_der"])
        frame_clave_container.pack(fill="x", padx=36, pady=(0, 6))

        lbl_clave = tk.Label(
            frame_clave_container, text="CONTRASE\u00d1A",
            bg=COLORES["panel_der"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9, "bold"), anchor="w",
        )
        lbl_clave.pack(anchor="w", pady=(0, 5))

        self.frame_entry_clave = tk.Frame(
            frame_clave_container, bg=COLORES["entry_borde"],
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
            highlightcolor=COLORES["entry_borde_focus"],
        )
        self.frame_entry_clave.pack(fill="x")

        self.entry_clave = tk.Entry(
            self.frame_entry_clave, font=("Helvetica", 11),
            bg=COLORES["entry_bg"], fg=COLORES["texto_blanco"],
            insertbackground=COLORES["texto_blanco"],
            relief="flat", bd=0, show="\u2022",
        )
        self.entry_clave.pack(side="left", fill="x", expand=True, padx=(12, 0), ipady=9)

        self.btn_toggle = tk.Label(
            self.frame_entry_clave, text="\U0001f441",
            bg=COLORES["entry_bg"], fg=COLORES["texto_gris"],
            font=("Helvetica", 12), cursor="hand2", padx=6,
        )
        self.btn_toggle.pack(side="right", ipady=4)
        self.btn_toggle.bind("<Button-1>", lambda e: self._toggle_password())
        self.btn_toggle.bind("<Enter>", lambda e: self.btn_toggle.config(fg=COLORES["texto_blanco"]))
        self.btn_toggle.bind("<Leave>", lambda e: self.btn_toggle.config(fg=COLORES["texto_gris"]))

        self.entry_clave.bind("<FocusIn>", lambda e: self._focus_in(self.frame_entry_clave))
        self.entry_clave.bind("<FocusOut>", lambda e: self._focus_out(self.frame_entry_clave))

        self.lbl_error = tk.Label(
            frame_form, text="", bg=COLORES["panel_der"],
            fg=COLORES["error"], font=("Helvetica", 8),
        )
        self.lbl_error.pack(pady=(4, 0))

        lbl_olvido = tk.Label(
            frame_form, text="\u00bfOlvidaste tu contrase\u00f1a?",
            bg=COLORES["panel_der"], fg=COLORES["accento"],
            font=("Helvetica", 9), cursor="hand2",
        )
        lbl_olvido.pack(anchor="e", padx=36, pady=(6, 18))
        lbl_olvido.bind("<Enter>", lambda e: lbl_olvido.config(fg=COLORES["accento_hover"]))
        lbl_olvido.bind("<Leave>", lambda e: lbl_olvido.config(fg=COLORES["accento"]))

        self.canvas_boton = tk.Canvas(
            frame_form, height=44, bg=COLORES["panel_der"],
            highlightthickness=0, cursor="hand2",
        )
        self.canvas_boton.pack(fill="x", padx=36, pady=(0, 16))
        self._dibujar_boton(COLORES["accento"])
        self.canvas_boton.bind("<Button-1>", lambda e: self._intentar_login())
        self.canvas_boton.bind("<Enter>", lambda e: self._dibujar_boton(COLORES["accento_hover"]))
        self.canvas_boton.bind("<Leave>", lambda e: self._dibujar_boton(COLORES["accento"]))

        self.entry_usuario.focus_set()

    def _crear_campo_entry(self, parent, label_text):
        frame_container = tk.Frame(parent, bg=COLORES["panel_der"])
        frame_container.pack(fill="x", padx=36, pady=(0, 16))

        lbl = tk.Label(
            frame_container, text=label_text,
            bg=COLORES["panel_der"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9, "bold"), anchor="w",
        )
        lbl.pack(anchor="w", pady=(0, 5))

        frame_entry = tk.Frame(
            frame_container, bg=COLORES["entry_borde"],
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
            highlightcolor=COLORES["entry_borde_focus"],
        )
        frame_entry.pack(fill="x")

        entry = tk.Entry(
            frame_entry, font=("Helvetica", 11),
            bg=COLORES["entry_bg"], fg=COLORES["texto_blanco"],
            insertbackground=COLORES["texto_blanco"],
            relief="flat", bd=0,
        )
        entry.pack(fill="x", padx=12, ipady=9)

        entry.bind("<FocusIn>", lambda e: self._focus_in(frame_entry))
        entry.bind("<FocusOut>", lambda e: self._focus_out(frame_entry))

        return frame_entry, entry

    def _focus_in(self, frame):
        frame.config(highlightbackground=COLORES["entry_borde_focus"])

    def _focus_out(self, frame):
        frame.config(highlightbackground=COLORES["entry_borde"])

    def _toggle_password(self):
        self._usuario_visible = not self._usuario_visible
        if self._usuario_visible:
            self.entry_clave.config(show="")
            self.btn_toggle.config(text="\U0001f441\u200d\U0001f5e8")
        else:
            self.entry_clave.config(show="\u2022")
            self.btn_toggle.config(text="\U0001f441")

    def _dibujar_boton(self, color):
        c = self.canvas_boton
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width()
        h = 44
        r = 10
        c.create_arc(0, 0, 2 * r, 2 * r, start=90, extent=90, fill=color, outline="")
        c.create_arc(w - 2 * r, 0, w, 2 * r, start=0, extent=90, fill=color, outline="")
        c.create_arc(0, h - 2 * r, 2 * r, h, start=180, extent=90, fill=color, outline="")
        c.create_arc(w - 2 * r, h - 2 * r, w, h, start=270, extent=90, fill=color, outline="")
        c.create_rectangle(r, 0, w - r, h, fill=color, outline="")
        c.create_rectangle(0, r, w, h - r, fill=color, outline="")
        c.create_text(w // 2, h // 2, text="INICIAR SESI\u00d3N",
                      fill=COLORES["texto_blanco"], font=("Helvetica", 11, "bold"))



    def _intentar_login(self):
        usuario = self.entry_usuario.get().strip()
        clave = self.entry_clave.get().strip()

        if not usuario or not clave:
            self._mostrar_error("Todos los campos son obligatorios.")
            self._shake()
            return

        try:
            usuarios_ref = self.db.collection("usuarios")
            docs = usuarios_ref.where("usuario", "==", usuario).limit(1).get()
            if len(docs) == 0:
                self._mostrar_error("Usuario o contrasena incorrectos.")
                self._shake()
                return

            doc = docs[0].to_dict()
            if doc.get("clave") == clave:
                self.ventana.destroy()
                import usuarioventana
                usuarioventana.UsuarioApp()
            else:
                self._mostrar_error("Usuario o contrasena incorrectos.")
                self._shake()
        except Exception as e:
            self._mostrar_error(f"Error de conexion: {e}")
            self._shake()



    def _mostrar_error(self, msg):
        self.lbl_error.config(text=f"  \u26a0  {msg}", fg=COLORES["error"])

    def _mostrar_exito(self, msg):
        self.lbl_error.config(text=f"  \u2713  {msg}", fg=COLORES["exito"])

    def _shake(self, paso=0, desplazamientos=(6, -6, 4, -4, 2, -2, 0)):
        if paso < len(desplazamientos):
            self.ventana.geometry(
                f"{ANCHO}x{ALTO}+{(self.ventana.winfo_screenwidth() - ANCHO) // 2 + desplazamientos[paso]}"
                f"+{(self.ventana.winfo_screenheight() - ALTO) // 2}"
            )
            self.ventana.after(40, self._shake, paso + 1, desplazamientos)

    def _iniciar_animacion_entrada(self):
        self.ventana.after(30, self._fade_in, 0.0)

    def _fade_in(self, alpha):
        if alpha < 1.0:
            alpha += 0.05
            self.ventana.attributes("-alpha", min(alpha, 1.0))
            self.ventana.after(15, self._fade_in, alpha)

    def _iniciar_arrastre(self, e):
        self._offset_x = e.x
        self._offset_y = e.y

    def _arrastrar(self, e):
        x = self.ventana.winfo_x() + e.x - self._offset_x
        y = self.ventana.winfo_y() + e.y - self._offset_y
        self.ventana.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    LoginApp()
