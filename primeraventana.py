import tkinter as tk
import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore
import threading
import json
import time

import ctypes

from modelos import Usuario


def ruta_relativa(ruta):
    """Resuelve una ruta dentro del proyecto según el entorno de ejecución.

    @param ruta: Ruta relativa del archivo o recurso requerido.
    @return str: Ruta absoluta final para acceder al recurso.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ruta)


def configurar_icono(ventana):
    """Configura el icono de la aplicación para la ventana principal.

    @param ventana: Objeto de ventana de Tkinter que recibirá el icono.
    @return None: No devuelve valor; solo aplica el icono a la ventana.
    """
    try:
        if sys.platform == "win32":
            ventana.iconbitmap(ruta_relativa("icon/Fixmol_icon.ico"))
        else:
            from PIL import Image, ImageTk
            icono = Image.open(ruta_relativa("img/Fixmol3.png"))
            icono = icono.resize((64, 64), Image.LANCZOS)
            foto = ImageTk.PhotoImage(icono)
            ventana.iconphoto(True, foto)
            ventana._icono_app = foto
    except Exception:
        pass


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

MIN_SPLASH_MS = 2000
MAX_SPLASH_MS = 12000


class PantallaCarga(tk.Toplevel):
    """Muestra la pantalla de carga con animación del logo de la app.

    @param master: Ventana padre sobre la que se monta la pantalla.
    @param tamano_logo: Tamaño del logo mostrado durante la carga.
    """

    def __init__(self, master, tamano_logo=340):
        """Inicializa la ventana splash y la animación de carga.

        @param master: Control padre de la ventana.
        @param tamano_logo: Tamaño del logo a mostrar.
        """
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        fondo = COLORES["bg_oscuro"]
        self.configure(bg=fondo)

        from PIL import Image, ImageTk
        logo = Image.open(ruta_relativa("img/Fixmol3.png"))
        logo = logo.resize((tamano_logo, tamano_logo), Image.LANCZOS)
        self._logo_tk = ImageTk.PhotoImage(logo)

        contenedor = tk.Frame(self, bg=fondo)
        contenedor.pack(fill="both", expand=True)

        tk.Label(contenedor, image=self._logo_tk, bg=fondo).pack(pady=(0, 14))

        self.canvas = tk.Canvas(contenedor, width=100, height=100,
                                bg=fondo, highlightthickness=0, bd=0)
        self.canvas.pack()
        self._angulo = 0
        self._animar()

        tk.Label(contenedor, text="CONECTANDO...", bg=fondo,
                 fg="#94a3b8", font=("Helvetica", 9, "bold")).pack(pady=(14, 0))

        self._centrar(tamano_logo + 60, tamano_logo + 190)
        self.lift()

    def _centrar(self, w, h):
        """Centra la ventana splash en la pantalla.

        @param w: Ancho de la ventana.
        @param h: Alto de la ventana.
        @return None: Ajusta la geometría de la pantalla.
        """
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self._x = max(0, (sw - w) // 2)
        self._y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{self._x}+{self._y}")
        self.deiconify()
        self.after(30, self._reaplicar_centrado)

    def _reaplicar_centrado(self):
        """Reaplica la posición centrada de la splash si la ventana sigue activa.

        @return None: Actualiza la geometría de la ventana.
        """
        try:
            self.geometry(f"+{self._x}+{self._y}")
            self.lift()
        except tk.TclError:
            pass

    def _animar(self):
        """Dibuja y actualiza la animación circular de carga.

        @return None: Repite la animación del arco giratorio.
        """
        try:
            self.winfo_exists()
        except tk.TclError:
            return
        self.canvas.delete("rueda")
        self.canvas.create_arc(
            12, 12, 88, 88, start=self._angulo, extent=60, style="arc",
            outline=COLORES["accento"], width=8, tags="rueda",
        )
        self._angulo = (self._angulo + 12) % 360
        self.after(18, self._animar)


class LoginApp:
    """Gestiona la pantalla de login y la autenticación del sistema.

    @return None: Inicializa la interfaz principal y la lógica de acceso.
    """

    def __init__(self, volver_de_sesion=False):
        """Inicializa la aplicación de login y la carga de la base de datos.

        @param volver_de_sesion: Si es True, se reabre el login tras cerrar sesión
            saltando la pantalla de carga. Si es False, se muestra el flujo normal.
        @return None: Crea la ventana principal y prepara la UI.
        """
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SistemaAsistencia")
        except Exception:
            pass
        self.firebase_listo = False
        self._firebase_done = False
        self._splash_inicio = None
        self._fade_iniciado = False
        self._ui_lista = False
        self.db = None
        self._cargar_cache_local()
        threading.Thread(target=self._init_firebase, daemon=True).start()
        self.ventana = tk.Tk()
        self.ventana.withdraw()
        configurar_icono(self.ventana)
        self.ventana.title("Sistema de Asistencia")
        self.ventana.config(bg=COLORES["bg_oscuro"])

        self._volver_de_sesion = volver_de_sesion or os.environ.pop("SA_VOLVER_LOGIN", "") == "1"

        self.destino = None

        self._usuario_visible = False
        self._animacion_idx = 0
        self._widgets_animar = []

        self._splash_inicio = time.monotonic()
        self._fade_iniciado = False

        if self._volver_de_sesion:
            self.ventana.after(0, self._preparar_y_mostrar_login)
        else:
            self._splash = PantallaCarga(self.ventana)
            self.ventana.after(100, self._polear_inicio)

        self.ventana.mainloop()

    def _preparar_y_mostrar_login(self):
        """Prepara la interfaz de login y la muestra con efecto de entrada.

        @return None: Configura y visualiza la pantalla principal de acceso.
        """
        if self._ui_lista:
            return
        self._ui_lista = True
        self.ventana.attributes("-alpha", 0.0)
        self.ventana.overrideredirect(True)
        self._centrar_ventana(ANCHO, ALTO)
        self.ventana.minsize(ANCHO, ALTO)
        self.ventana.maxsize(ANCHO, ALTO)
        self._construir_ui()

        self._offset_x = 0
        self._offset_y = 0
        self.barra_titulo.bind("<ButtonPress-1>", self._iniciar_arrastre)
        self.barra_titulo.bind("<B1-Motion>", self._arrastrar)

        self.ventana.deiconify()
        self._iniciar_animacion_entrada()

    def _init_firebase(self):
        """Inicializa la conexión con Firebase y valida la disponibilidad de Firestore.

        @return None: Carga la instancia de base de datos y marca el estado de conexión.
        """
        self._firebase_error = ""
        try:
            if not firebase_admin._apps:
                key_file = "config/firebase-key.json"
                if not os.path.exists(ruta_relativa(key_file)):
                    key_file = "config/registro-asistencia-bfe64-firebase-adminsdk-fbsvc-1d738c49d5.json"
                if not os.path.exists(ruta_relativa(key_file)):
                    raise FileNotFoundError(
                        f"No se encontro la credencial de Firebase. Archivos revisados en "
                        f"'{ruta_relativa('config')}': firebase-key.json y "
                        f"registro-asistencia-bfe64-firebase-adminsdk-fbsvc-1d738c49d5.json"
                    )
                cred = credentials.Certificate(ruta_relativa(key_file))
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            try:
                list(self.db.collection("usuarios").limit(1).get())
                self.firebase_listo = True
            except Exception as e:
                self._firebase_error = f"Credencial verificada, pero no se pudo leer Firestore: {e}"
                print(f"Error Firestore lectura: {e}")
        except Exception as e:
            self._firebase_error = str(e)
            print(f"Error Firebase: {e}")
        finally:
            self._firebase_done = True

    def _ruta_cache(self):
        """Devuelve la ruta del caché local de usuarios.

        @return str: Ubicación del archivo JSON del caché.
        """
        if getattr(sys, "frozen", False):
            carpeta = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SistemaAsistencia")
        else:
            carpeta = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(carpeta, exist_ok=True)
        return os.path.join(carpeta, "cache_usuarios.json")

    def _cargar_cache_local(self):
        """Carga usuarios desde el caché local si existe.

        @return None: Carga los datos del caché en self.cache_usuarios.
        """
        try:
            with open(self._ruta_cache()) as f:
                self.cache_usuarios = json.load(f)
        except:
            self.cache_usuarios = {}

    def _guardar_cache_local(self, usuario, datos):
        """Guarda la información del usuario en el caché local.

        @param usuario: Nombre del usuario a guardar.
        @param datos: Diccionario con la información del usuario.
        @return None: Escribe el registro en el archivo JSON.
        """
        self.cache_usuarios[usuario] = datos
        with open(self._ruta_cache(), "w") as f:
            json.dump(self.cache_usuarios, f)

    def _buscar_en_cache(self, identificador):
        """Busca un usuario dentro del caché por nombre o correo.

        @param identificador: Nombre o correo del usuario a consultar.
        @return tuple: Tupla (nombre, documento) si existe; si no, (None, None).
        """
        identificador = identificador.strip().lower()
        for nombre, doc in self.cache_usuarios.items():
            if nombre.strip().lower() == identificador:
                return nombre, doc
            if str(doc.get("correo") or "").strip().lower() == identificador:
                return nombre, doc
        return None, None

    def _centrar_ventana(self, w, h):
        """Centra la ventana principal en la pantalla.

        @param w: Ancho deseado.
        @param h: Alto deseado.
        @return None: Ajusta la posición de la ventana.
        """
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.ventana.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_ui(self):
        """Construye la interfaz principal del formulario de login.

        @return None: Crea los paneles y controles visuales.
        """
        self._crear_barra_titulo()
        self._crear_panel_izquierdo()
        self._crear_panel_derecho()

    def _crear_barra_titulo(self):
        """Crea la barra superior con controles de ventana.

        @return None: Genera la barra de título draggable y botones de control.
        """
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
        """Crea el panel visual izquierdo con el logo y nombre de la app.

        @return None: Genera la parte gráfica principal del login.
        """
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
            text="Gestiona tu asistencia de\nforma rapida y segura",
            bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            font=("Helvetica", 9), justify="center",
        )
        lbl_sub.pack()

    def _crear_panel_derecho(self):
        """Crea el panel derecho con el formulario de acceso del usuario.

        @return None: Dibuja los campos de usuario, clave y botón de inicio.
        """
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
        """Genera un campo de texto con etiqueta para el formulario.

        @param parent: Contenedor del campo.
        @param label_text: Texto visible de la etiqueta.
        @return tuple: Par (contenedor, entrada) del campo creado.
        """
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
        """Resalta el marco de un campo al recibir el foco.

        @param frame: Marco del campo a destacar.
        @return None: Cambia el color del borde del campo.
        """
        frame.config(highlightbackground=COLORES["entry_borde_focus"])

    def _focus_out(self, frame):
        """Restablece el estilo normal del campo cuando pierde el foco.

        @param frame: Marco del campo a restaurar.
        @return None: Vuelve al color de borde habitual.
        """
        frame.config(highlightbackground=COLORES["entry_borde"])

    def _toggle_password(self):
        """Alterna la visibilidad de la contraseña ingresada.

        @return None: Muestra u oculta la clave del usuario.
        """
        self._usuario_visible = not self._usuario_visible
        if self._usuario_visible:
            self.entry_clave.config(show="")
            self.btn_toggle.config(text="\U0001f441\u200d\U0001f5e8")
        else:
            self.entry_clave.config(show="\u2022")
            self.btn_toggle.config(text="\U0001f441")

    def _dibujar_boton(self, color):
        """Dibuja el botón principal del login en un canvas.

        @param color: Color de relleno del botón.
        @return None: Redibuja el botón con el color indicado.
        """
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
        """Intenta iniciar sesión con las credenciales ingresadas.

        @return None: Valida usuario y contraseña o muestra errores de validación.
        """
        usuario = self.entry_usuario.get().strip()
        clave = self.entry_clave.get().strip()

        if not usuario or not clave:
            self._mostrar_error("Todos los campos son obligatorios.")
            self._shake()
            return

        nombre_cache, doc_cache = self._buscar_en_cache(usuario)
        if doc_cache is not None and doc_cache.get("clave") == clave:
            self._login_exitoso(usuario, doc_cache)
            return

        if not self.firebase_listo:
            self._intentos_espera = getattr(self, "_intentos_espera", 0) + 1
            if self._intentos_espera > 10:
                self._intentos_espera = 0
                detalle = getattr(self, "_firebase_error", "") or ""
                self._mostrar_error("No hay conexion a la base de datos" + (f": {detalle[:120]}" if detalle else ""))
                return
            self._mostrar_error("Conectando... espera un momento")
            self.ventana.after(500, self._intentar_login)
            return

        self._mostrar_cargando("Verificando credenciales...")
        threading.Thread(target=self._verificar_en_firebase, args=(usuario, clave), daemon=True).start()

    def _verificar_en_firebase(self, usuario, clave):
        """Valida las credenciales en Firebase.

        @param usuario: Nombre de usuario ingresado.
        @param clave: Contraseña ingresada.
        @return None: Ejecuta la lógica de acceso y errores en el hilo principal.
        """
        try:
            doc = Usuario.buscar_por_identificador(self.db, usuario)
            if doc is None:
                self.ventana.after(0, self._error_login, "Usuario o contrasena incorrectos.")
                return
            if Usuario.clave_valida(doc, clave):
                self._guardar_cache_local(doc.get("usuario") or usuario, doc)
                self.ventana.after(0, self._login_exitoso, usuario, doc)
            else:
                self.ventana.after(0, self._error_login, "Usuario o contrasena incorrectos.")
        except Exception as e:
            self.ventana.after(0, self._error_login, f"Error de conexion: {e}")

    def _login_exitoso(self, usuario, doc=None):
        """Procesa un inicio de sesión correcto y prepara la redirección según el rol.

        @param usuario: Usuario que inició sesión.
        @param doc: Documento del usuario con datos adicionales.
        @return None: Guarda el destino y cierra la ventana para que el controlador
            abra la pantalla correspondiente según el rol.
        """
        doc = doc or {}
        self._registrar_log(usuario, doc.get("correo", ""), "exitoso")
        rol = str(doc.get("rol", "")).lower()
        self.destino = (rol, usuario, doc)
        self.ventana.destroy()

    def _error_login(self, msg):
        """Muestra un error de autenticación y activa la animación de alerta.

        @param msg: Mensaje de error a mostrar.
        @return None: Presenta el fallo en la interfaz.
        """
        self._registrar_log(
            self.entry_usuario.get().strip(),
            "",
            "fallido" if "incorrectos" in msg else "",
        )
        self._mostrar_error(msg)
        self._shake()

    def _registrar_log(self, usuario, correo, resultado):
        """Guarda un registro de acceso en Firestore.

        @param usuario: Nombre del usuario.
        @param correo: Correo del usuario.
        @param resultado: Estado del inicio de sesión.
        @return None: Registra el evento en la colección de login_log.
        """
        if not usuario:
            return

        def _registrar():
            """Ejecuta la escritura del log de autenticación.

            @return None: Agrega el evento al historial del sistema.
            """
            try:
                from datetime import datetime
                if not self.firebase_listo:
                    return
                self.db.collection("login_log").add({
                    "usuario": usuario,
                    "correo": correo,
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "hora": datetime.now().strftime("%H:%M:%S"),
                    "resultado": resultado,
                })
            except Exception as e:
                print(f"Error log: {e}")

        threading.Thread(target=_registrar, daemon=True).start()

    def _mostrar_cargando(self, msg):
        """Muestra un estado de carga en el formulario.

        @param msg: Texto de carga a mostrar.
        @return None: Actualiza el texto de error/carga del formulario.
        """
        self.lbl_error.config(text=f"  \u23f3  {msg}", fg=COLORES["texto_gris"])

    def _mostrar_error(self, msg):
        """Muestra un mensaje de error en la interfaz.

        @param msg: Mensaje a mostrar.
        @return None: Actualiza el estado visual del formulario.
        """
        self.lbl_error.config(text=f"  \u26a0  {msg}", fg=COLORES["error"])

    def _mostrar_exito(self, msg):
        """Muestra un mensaje de éxito en la interfaz.

        @param msg: Mensaje de confirmación.
        @return None: Actualiza el estado visual del formulario.
        """
        self.lbl_error.config(text=f"  \u2713  {msg}", fg=COLORES["exito"])

    def _shake(self, paso=0, desplazamientos=(6, -6, 4, -4, 2, -2, 0)):
        """Genera una pequeña animación de vibración en la ventana.

        @param paso: Paso actual de la animación.
        @param desplazamientos: Lista de offsets a aplicar.
        @return None: Repite la animación de sacudida.
        """
        if paso < len(desplazamientos):
            self.ventana.geometry(
                f"{ANCHO}x{ALTO}+{(self.ventana.winfo_screenwidth() - ANCHO) // 2 + desplazamientos[paso]}"
                f"+{(self.ventana.winfo_screenheight() - ALTO) // 2}"
            )
            self.ventana.after(40, self._shake, paso + 1, desplazamientos)

    def _polear_inicio(self):
        """Controla la duración del splash y cierra la pantalla de carga cuando corresponde.

        @return None: Decide si se termina la pantalla splash o sigue esperando.
        """
        if self._fade_iniciado:
            return
        transcurrido = (time.monotonic() - self._splash_inicio) * 1000
        listo = getattr(self, "_firebase_done", False)
        if (listo and transcurrido >= MIN_SPLASH_MS) or transcurrido >= MAX_SPLASH_MS:
            self._cerrar_splash()
            return
        self.ventana.after(100, self._polear_inicio)

    def _cerrar_splash(self):
        """Cierra la pantalla de carga y muestra el login.

        @return None: Elimina el splash y llama a la animación de entrada.
        """
        self._fade_iniciado = True
        try:
            self._splash.destroy()
        except Exception:
            pass
        self._splash = None
        self._preparar_y_mostrar_login()

    def _iniciar_animacion_entrada(self):
        """Inicia la animación de fundido de entrada del login.

        @return None: Programa la transición gradual de opacidad.
        """
        self.ventana.after(30, self._fade_in, 0.0)

    def _fade_in(self, alpha):
        """Aplica un efecto de fundido gradual para mostrar la ventana.

        @param alpha: Nivel actual de opacidad.
        @return None: Actualiza la opacidad de la ventana.
        """
        if alpha < 1.0:
            alpha += 0.05
            self.ventana.attributes("-alpha", min(alpha, 1.0))
            self.ventana.after(15, self._fade_in, alpha)

    def _iniciar_arrastre(self, e):
        """Guarda la posición inicial del cursor para mover la ventana.

        @param e: Evento del mouse con coordenadas.
        @return None: Inicializa el offset de arrastre.
        """
        self._offset_x = e.x
        self._offset_y = e.y

    def _arrastrar(self, e):
        """Mueve la ventana según el desplazamiento del mouse.

        @param e: Evento del mouse en movimiento.
        @return None: Actualiza la geometría de la ventana.
        """
        x = self.ventana.winfo_x() + e.x - self._offset_x
        y = self.ventana.winfo_y() + e.y - self._offset_y
        self.ventana.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    primera_vez = True
    while True:
        login = LoginApp(volver_de_sesion=not primera_vez)
        primera_vez = False

        destino = getattr(login, "destino", None)
        if not destino:
            break

        rol, usuario, doc = destino
        if rol in ("admin", "administrador", "due\u00f1o", "dueno"):
            import dashboard_admin
            app = dashboard_admin.DashboardAdminApp(usuario=usuario, datos=doc)
        else:
            import usuarioventana
            app = usuarioventana.UsuarioApp(
                usuario=doc.get("usuario") or usuario,
                datos=doc,
            )

        if not getattr(app, "volver_login", False):
            break
