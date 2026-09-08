import tkinter as tk
from tkinter import font as tkfont
import sys
import os
import threading

from modelos import get_db, Marcacion
import firebase_admin
from firebase_admin import credentials, firestore


def ruta_relativa(ruta):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ruta)


def _get_firestore():
    if not firebase_admin._apps:
        key_file = "config/firebase-key.json"
        if not os.path.exists(ruta_relativa(key_file)):
            key_file = "config/registro-asistencia-bfe64-firebase-adminsdk-fbsvc-236f010224.json"
        cred = credentials.Certificate(ruta_relativa(key_file))
        firebase_admin.initialize_app(cred)
    return firestore.client()


COLORES = {
    "bg_oscuro":        "#0d1117",
    "panel_izq":        "#161b22",
    "panel_der":        "#0d1117",
    "accento":          "#e94560",
    "accento_hover":    "#ff6b81",
    "accento_oscuro":   "#c81e45",
    "texto_blanco":     "#e6edf3",
    "texto_gris":       "#7d8590",
    "texto_placeholder": "#484f58",
    "entry_bg":         "#161b22",
    "entry_borde":      "#30363d",
    "entry_borde_focus": "#e94560",
    "divider":          "#21262d",
    "sombra":           "#010409",
    "error":            "#f85149",
    "exito":            "#3fb950",
    "titulo_panel":     "#f0f6fc",
    "card_bg":          "#161b22",
}

ANCHO = 820
ALTO = 500


class UsuarioApp:
    def __init__(self, usuario="", datos=None):
        datos = datos or {}
        self.usuario = usuario
        self.nombre = datos.get("nombre") or usuario.capitalize()
        self.rol = datos.get("rol", "")
        self.correo = datos.get("correo", "")
        self.db = None
        self.db_ok = False

        self.ventana = tk.Tk()
        self.ventana.title("Sistema de Asistencia")
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self.ventana.overrideredirect(True)
        self.ventana.attributes("-alpha", 0.0)
        self._centrar_ventana(ANCHO, ALTO)
        self.ventana.minsize(ANCHO, ALTO)
        self.ventana.maxsize(ANCHO, ALTO)

        self._modo_marcacion = "entrada"
        self._jornada = {"entrada": None, "salida": None}

        self._construir_ui()
        self._iniciar_animacion_entrada()

        self._offset_x = 0
        self._offset_y = 0
        self.barra_titulo.bind("<ButtonPress-1>", self._iniciar_arrastre)
        self.barra_titulo.bind("<B1-Motion>", self._arrastrar)

        threading.Thread(target=self._iniciar_firebase, daemon=True).start()
        self.ventana.mainloop()

    def _iniciar_firebase(self):
        try:
            self.db = get_db()
            self.db_ok = True
            self.ventana.after(0, self._cargar_jornada_desde_db)
        except Exception as e:
            print("Error Firebase:", e)

    def _cargar_jornada_desde_db(self):
        try:
            entrada = Marcacion.buscar(self.db, self.usuario, accion=Marcacion.ENTRADA)
            if entrada:
                self._aplicar_entrada_bd(entrada)
        except Exception:
            pass

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

        from PIL import Image, ImageTk
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
            text="Marca tu entrada y salida\nde forma rapida y segura",
            bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9), justify="center",
        )
        lbl_sub.pack()

        self.btn_cerrar_sesion = tk.Button(
            self.panel_izq, text="CERRAR SESI\u00d3N",
            bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            activebackground=COLORES["entry_borde"], activeforeground=COLORES["texto_blanco"],
            font=("Helvetica", 9, "bold"), relief="flat",
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
            cursor="hand2", command=self._cerrar_sesion,
        )
        self.btn_cerrar_sesion.pack(side="bottom", pady=20, padx=40, fill="x")

        if "administrador" in self.rol.lower():
            self.btn_gestion = tk.Button(
                self.panel_izq, text="GESTI\u00d3N DE USUARIOS",
                bg=COLORES["accento"], fg=COLORES["texto_blanco"],
                activebackground=COLORES["accento_oscuro"], activeforeground=COLORES["texto_blanco"],
                font=("Helvetica", 9, "bold"), relief="flat",
                highlightthickness=0, cursor="hand2",
                command=self._abrir_gestion_usuarios,
            )
            self.btn_gestion.pack(side="bottom", pady=(0, 8), padx=40, fill="x")

            self.btn_registros = tk.Button(
                self.panel_izq, text="GESTI\u00d3N DE REGISTROS",
                bg=COLORES["accento_oscuro"], fg=COLORES["texto_blanco"],
                activebackground=COLORES["entry_borde"], activeforeground=COLORES["texto_blanco"],
                font=("Helvetica", 9, "bold"), relief="flat",
                highlightthickness=0, cursor="hand2",
                command=self._abrir_gestion_registros,
            )
            self.btn_registros.pack(side="bottom", pady=(0, 8), padx=40, fill="x")

            self.btn_inasistencias = tk.Button(
                self.panel_izq, text="REPORTE DE INASISTENCIAS",
                bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
                activebackground=COLORES["entry_borde"], activeforeground=COLORES["texto_blanco"],
                font=("Helvetica", 9, "bold"), relief="flat",
                highlightthickness=1, highlightbackground=COLORES["entry_borde"],
                cursor="hand2",
                command=self._abrir_reporte_inasistencias,
            )
            self.btn_inasistencias.pack(side="bottom", pady=(0, 8), padx=40, fill="x")

    def _crear_panel_derecho(self):
        panel_der = tk.Frame(self.ventana, bg=COLORES["panel_der"])
        panel_der.pack(side="right", fill="both", expand=True)

        frame_form = tk.Frame(panel_der, bg=COLORES["panel_der"])
        frame_form.place(relx=0.5, rely=0.48, anchor="center", width=420, height=420)

        nombre = self.nombre
        self.lbl_saludo = tk.Label(
            frame_form, text=f"Hola, {nombre}",
            bg=COLORES["panel_der"], fg=COLORES["texto_blanco"],
            font=("Helvetica", 22, "bold"),
        )
        self.lbl_saludo.pack(pady=(0, 4))

        lbl_sub = tk.Label(
            frame_form, text="Marca tu entrada y salida",
            bg=COLORES["panel_der"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9),
        )
        lbl_sub.pack(pady=(0, 18))

        self.lbl_reloj = tk.Label(
            frame_form, text="00:00:00",
            bg=COLORES["panel_der"], fg=COLORES["titulo_panel"],
            font=("Helvetica", 34, "bold"),
        )
        self.lbl_reloj.pack(pady=(0, 20))
        self._actualizar_reloj()

        # Tarjeta de estado de la jornada
        card = tk.Frame(
            frame_form, bg=COLORES["card_bg"],
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
        )
        card.pack(fill="x", padx=20, pady=(0, 14))

        self.lbl_entrada = self._crear_fila_card(card, "HORA DE ENTRADA", 0)
        tk.Frame(card, bg=COLORES["entry_borde"], height=1).pack(fill="x", padx=14)
        self.lbl_salida = self._crear_fila_card(card, "HORA DE SALIDA", 1)

        frame_hora = tk.Frame(frame_form, bg=COLORES["panel_der"])
        frame_hora.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(
            frame_hora, text="HORA A MARCAR", bg=COLORES["panel_der"],
            fg=COLORES["texto_gris"], font=("Helvetica", 9, "bold"), anchor="w",
        ).pack(side="left", padx=(0, 10))

        self.spn_hh = tk.Spinbox(
            frame_hora, from_=0, to=23, width=3, format="%02.0f",
            justify="center", font=("Helvetica", 11, "bold"),
            bg=COLORES["entry_bg"], fg=COLORES["texto_blanco"],
            insertbackground=COLORES["texto_blanco"], relief="flat",
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
            buttonbackground=COLORES["panel_izq"], buttoncursor="hand2",
        )
        self.spn_hh.pack(side="left")

        tk.Label(
            frame_hora, text=":", bg=COLORES["panel_der"],
            fg=COLORES["texto_blanco"], font=("Helvetica", 12, "bold"),
        ).pack(side="left", padx=2)

        self.spn_mm = tk.Spinbox(
            frame_hora, from_=0, to=59, width=3, format="%02.0f",
            justify="center", font=("Helvetica", 11, "bold"),
            bg=COLORES["entry_bg"], fg=COLORES["texto_blanco"],
            insertbackground=COLORES["texto_blanco"], relief="flat",
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
            buttonbackground=COLORES["panel_izq"], buttoncursor="hand2",
        )
        self.spn_mm.pack(side="left")

        self.btn_ahora = tk.Button(
            frame_hora, text="AHORA", bg=COLORES["panel_izq"],
            fg=COLORES["texto_gris"], activebackground=COLORES["entry_borde"],
            activeforeground=COLORES["texto_blanco"], relief="flat",
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
            font=("Helvetica", 8, "bold"), cursor="hand2", command=self._fijar_hora_ahora,
        )
        self.btn_ahora.pack(side="right")

        self._fijar_hora_ahora()

        self.lbl_estado = tk.Label(
            frame_form, text="", bg=COLORES["panel_der"],
            fg=COLORES["exito"], font=("Helvetica", 9),
        )
        self.lbl_estado.pack(pady=(0, 4))

        # Botón de marcación (canvas, estilo del MVP)
        self.canvas_boton = tk.Canvas(
            frame_form, height=46, bg=COLORES["panel_der"],
            highlightthickness=0, cursor="hand2",
        )
        self.canvas_boton.pack(fill="x", padx=20)
        self._dibujar_boton()
        self.canvas_boton.bind("<Button-1>", lambda e: self._marcar())
        self.canvas_boton.bind("<Enter>", lambda e: self._dibujar_boton(COLORES["accento_hover"]))
        self.canvas_boton.bind("<Leave>", lambda e: self._dibujar_boton())

    def _crear_fila_card(self, parent, texto, fila):
        fila_frame = tk.Frame(parent, bg=COLORES["card_bg"])
        fila_frame.pack(fill="x", padx=16, pady=12)

        tk.Label(
            fila_frame, text=texto, bg=COLORES["card_bg"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9, "bold"), anchor="w",
        ).pack(side="left")

        lbl = tk.Label(
            fila_frame, text="\u2014", bg=COLORES["card_bg"], fg=COLORES["titulo_panel"],
            font=("Helvetica", 10, "bold"), anchor="e",
        )
        lbl.pack(side="right")
        return lbl

    def _actualizar_reloj(self):
        from datetime import datetime
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self.ventana.after(1000, self._actualizar_reloj)

    def _dibujar_boton(self, color=None):
        if color is None:
            color = COLORES["accento_oscuro"] if self._modo_marcacion == "salida" else COLORES["accento"]
        c = self.canvas_boton
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width()
        h = 46
        r = 10
        c.create_arc(0, 0, 2 * r, 2 * r, start=90, extent=90, fill=color, outline="")
        c.create_arc(w - 2 * r, 0, w, 2 * r, start=0, extent=90, fill=color, outline="")
        c.create_arc(0, h - 2 * r, 2 * r, h, start=180, extent=90, fill=color, outline="")
        c.create_arc(w - 2 * r, h - 2 * r, w, h, start=270, extent=90, fill=color, outline="")
        c.create_rectangle(r, 0, w - r, h, fill=color, outline="")
        c.create_rectangle(0, r, w, h - r, fill=color, outline="")
        texto = "MARCAR SALIDA" if self._modo_marcacion == "salida" else "MARCAR ENTRADA"
        c.create_text(w // 2, h // 2, text=texto,
                      fill=COLORES["texto_blanco"], font=("Helvetica", 11, "bold"))

    def _marcar(self):
        if not self.db_ok or self.db is None:
            self._mostrar_estado("Conectando a la base de datos...", exito=False)
            return

        tipo = self._modo_marcacion
        try:
            if tipo == Marcacion.ENTRADA:
                ent = Marcacion.buscar(self.db, self.usuario, accion=Marcacion.ENTRADA)
                if ent:
                    self._aplicar_entrada_bd(ent)
                    self._mostrar_estado("  \u26a0  Ya registraste tu entrada hoy", exito=False)
                    return
            else:
                ent = Marcacion.buscar(self.db, self.usuario, accion=Marcacion.ENTRADA)
                if not ent:
                    self._mostrar_estado("  \u26a0  Primero registra tu entrada", exito=False)
                    return

            marcacion = Marcacion.ahora(self.usuario, correo=self.correo, accion=tipo)
            marcacion.hora = self._hora_seleccionada()

            atrasado = marcacion.es_entrada_atrasada()
            salida_anticipada = marcacion.es_salida_anticipada()
            marcacion.guardar(self.db, atrasado=atrasado, salida_anticipada=salida_anticipada)

            self._marcacion_guardada(marcacion, atrasado, salida_anticipada)
        except Exception as e:
            self._mostrar_estado(f"  \u26a0  Error al guardar: {e}", exito=False)

    def _marcacion_guardada(self, marcacion, atrasado=False, salida_anticipada=False):
        tipo = marcacion.accion
        self._jornada[tipo] = marcacion.hora
        if tipo == Marcacion.ENTRADA:
            self.lbl_entrada.config(text=marcacion.hora)
            if atrasado:
                self.lbl_entrada.config(fg=COLORES["error"])
                self._mostrar_estado(f"  \u26a0  Entrada {marcacion.hora} (ATRASADO)", exito=False)
            else:
                self.lbl_entrada.config(fg=COLORES["titulo_panel"])
                self._mostrar_estado(f"  \u2713  Entrada guardada a las {marcacion.hora}", exito=True)
            self._modo_marcacion = Marcacion.SALIDA
        else:
            self.lbl_salida.config(text=marcacion.hora)
            if salida_anticipada:
                self.lbl_salida.config(fg=COLORES["error"])
                self._mostrar_estado(f"  \u26a0  Salida {marcacion.hora} (SALIDA ANTICIPADA)", exito=False)
            else:
                self.lbl_salida.config(fg=COLORES["titulo_panel"])
                self._mostrar_estado(f"  \u2713  Salida guardada a las {marcacion.hora}", exito=True)
            self._modo_marcacion = Marcacion.ENTRADA
        self._dibujar_boton()

    def _mostrar_estado(self, msg, exito=False):
        self.lbl_estado.config(
            text=msg,
            fg=COLORES["exito"] if exito else COLORES["error"],
        )

    def _fijar_hora_ahora(self):
        from datetime import datetime
        ahora = datetime.now()
        self.spn_hh.delete(0, tk.END)
        self.spn_hh.insert(0, f"{ahora.hour:02d}")
        self.spn_mm.delete(0, tk.END)
        self.spn_mm.insert(0, f"{ahora.minute:02d}")

    def _hora_seleccionada(self):
        from datetime import datetime
        try:
            hh = max(0, min(23, int(self.spn_hh.get())))
            mm = max(0, min(59, int(self.spn_mm.get())))
            return f"{hh:02d}:{mm:02d}:00"
        except ValueError:
            return datetime.now().strftime("%H:%M:%S")

    def _aplicar_entrada_bd(self, ent):
        hora = ent.get("hora") or ""
        self._jornada["entrada"] = hora
        self.lbl_entrada.config(text=hora)
        if ent.get("atrasado"):
            self.lbl_entrada.config(fg=COLORES["error"])
            self._mostrar_estado(f"  \u26a0  Entrada de hoy {hora} (ATRASADO)", exito=False)
        else:
            self.lbl_entrada.config(fg=COLORES["titulo_panel"])
        self._modo_marcacion = Marcacion.SALIDA
        self._dibujar_boton()

    def _abrir_gestion_usuarios(self):
        import gestion_usuarios
        gestion_usuarios.GestionUsuariosApp(self.ventana, self.usuario)

    def _abrir_gestion_registros(self):
        import gestion_registros
        gestion_registros.GestionRegistrosApp(self.ventana, self.usuario)

    def _abrir_reporte_inasistencias(self):
        import gestion_registros
        gestion_registros.ReporteInasistenciasApp(self.ventana)

    def _cerrar_sesion(self):
        self.ventana.destroy()
        subprocess_login()

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


def subprocess_login():
    import subprocess
    base = os.path.dirname(os.path.abspath(__file__))
    subprocess.Popen([sys.executable, os.path.join(base, "primeraventana.py")])


if __name__ == "__main__":
    UsuarioApp()
