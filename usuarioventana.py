import tkinter as tk
import sys
import os
import threading

from modelos import get_db, Marcacion, Alerta
import icons


def ruta_relativa(ruta):
    """Devuelve la ruta completa de un archivo relativo al directorio de la app.

    @param ruta: Ruta del recurso dentro del proyecto, por ejemplo "img/logo.png".
    @return str: Ruta absoluta del archivo, adaptada para ejecución empaquetada o normal.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ruta)


def configurar_icono(ventana):
    """Configura el icono de la ventana principal según la plataforma actual.

    @param ventana: Instancia de la ventana Tkinter donde se aplicará el icono.
    @return None: No devuelve valor; solo ajusta la configuración visual de la ventana.
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
    """Representa la ventana principal del sistema para que un usuario marque entrada y salida.

    @param usuario: Nombre de usuario autenticado activo en la sesión.
    @param datos: Diccionario opcional con datos adicionales del usuario como nombre, rol y correo.
    """

    def __init__(self, usuario="", datos=None):
        """Inicializa la interfaz, carga el estado del usuario y arranca la ventana principal.

        @param usuario: Identificador del usuario actual.
        @param datos: Datos del perfil del usuario, si existen.
        @return None: No devuelve valor y crea la UI en el hilo principal de Tkinter.
        """
        datos = datos or {}
        self.usuario = usuario
        self.nombre = datos.get("nombre") or usuario.capitalize()
        self.rol = datos.get("rol", "")
        self.correo = datos.get("correo", "")
        self.db = None
        self.db_ok = False
        self.volver_login = False
        self._reloj_after_id = None

        self.ventana = tk.Tk()
        self.ventana.title("Sistema de Asistencia")
        configurar_icono(self.ventana)
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self.ventana.overrideredirect(True)
        self.ventana.attributes("-alpha", 0.0)
        self._centrar_ventana(ANCHO, ALTO)
        self.ventana.minsize(ANCHO, ALTO)
        self.ventana.maxsize(ANCHO, ALTO)

        self._modo_marcacion = "entrada"
        self._jornada = {"entrada": None, "salida": None}
        self.COMPLETADA = "completada"

        self._construir_ui()
        self._iniciar_animacion_entrada()
        icons.forzar_taskbar(self.ventana)

        self._offset_x = 0
        self._offset_y = 0
        self.barra_titulo.bind("<ButtonPress-1>", self._iniciar_arrastre)
        self.barra_titulo.bind("<B1-Motion>", self._arrastrar)

        threading.Thread(target=self._iniciar_firebase, daemon=True).start()
        self.ventana.mainloop()

    def _iniciar_firebase(self):
        """Inicializa la conexión a la base de datos en un hilo en segundo plano.

        @return None: No devuelve valor; actualiza la referencia a la base de datos y el estado de conexión.
        """
        try:
            self.db = get_db()
            self.db_ok = True
            self.ventana.after(0, self._cargar_jornada_desde_db)
        except Exception as e:
            print("Error Firebase:", e)

    def _cargar_jornada_desde_db(self):
        """Carga la jornada del usuario desde la base de datos y refleja entrada y salida.

        @return None: No devuelve valor; actualiza la interfaz si ya existen marcas de hoy.
        """
        try:
            entrada = Marcacion.buscar(self.db, self.usuario, accion=Marcacion.ENTRADA)
            if entrada:
                self._aplicar_entrada_bd(entrada)
            salida = Marcacion.buscar(self.db, self.usuario, accion=Marcacion.SALIDA)
            if salida:
                self._aplicar_salida_bd(salida)
        except Exception:
            pass

    def _centrar_ventana(self, w, h):
        """Centra la ventana en la pantalla según el ancho y alto indicados.

        @param w: Ancho de la ventana.
        @param h: Alto de la ventana.
        @return None: Ajusta la geometría de la ventana en pantalla.
        """
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.ventana.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_ui(self):
        """Construye los elementos visuales de la ventana principal.

        @return None: Crea la barra, panel izquierdo y panel derecho de la interfaz.
        """
        self._crear_barra_titulo()
        self._crear_panel_izquierdo()
        self._crear_panel_derecho()

    def _crear_barra_titulo(self):
        """Genera la barra superior con título y controles de cierre/minimizar.

        @return None: Crea la barra de título interactiva para la ventana.
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
        btn_cerrar.bind("<Button-1>", lambda e: self._cerrar_ventana_pura())

        btn_minimizar = tk.Label(
            self.barra_titulo, text=" \u2013 ", bg=COLORES["panel_izq"],
            fg=COLORES["texto_gris"], font=("Helvetica", 10), cursor="hand2",
        )
        btn_minimizar.pack(side="right")
        btn_minimizar.bind("<Enter>", lambda e: btn_minimizar.config(fg=COLORES["texto_blanco"]))
        btn_minimizar.bind("<Leave>", lambda e: btn_minimizar.config(fg=COLORES["texto_gris"]))
        btn_minimizar.bind("<Button-1>", lambda e: self.ventana.overrideredirect(False))

    def _crear_panel_izquierdo(self):
        """Crea el panel lateral izquierdo con branding, información y accesos rápidos.

        @return None: Genera la navegación lateral y los botones de sesión y administración.
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
        """Genera el panel principal de marcación con reloj, estados y botón de acción.

        @return None: Construye la interfaz central del usuario para registrar asistencia.
        """
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
        """Crea una fila dentro de una tarjeta con etiqueta y valor de hora.

        @param parent: Contenedor padre donde se insertará la fila.
        @param texto: Etiqueta que describe el tipo de hora a mostrar.
        @param fila: Índice de la fila, aunque no se usa para lógica funcional.
        @return tk.Label: Etiqueta del valor asociado a la fila.
        """
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
        """Actualiza la hora mostrada en la interfaz cada segundo.

        @return None: Reprograma la actualización del reloj en el hilo de Tkinter.
        """
        from datetime import datetime
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self._reloj_after_id = self.ventana.after(1000, self._actualizar_reloj)

    def _detener_reloj(self):
        pid = getattr(self, "_reloj_after_id", None)
        if pid is not None:
            try:
                self.ventana.after_cancel(pid)
            except Exception:
                pass
            self._reloj_after_id = None

    def _dibujar_boton(self, color=None):
        """Dibuja el botón principal de marcación con el color según el tipo de acción.

        @param color: Color opcional para sobreescribir el color base del botón.
        @return None: Actualiza el widget canvas con la apariencia visual del botón.
        """
        if color is None:
            if self._modo_marcacion == "salida":
                color = COLORES["accento_oscuro"]
            elif self._modo_marcacion == self.COMPLETADA:
                color = COLORES["entry_borde"]
            else:
                color = COLORES["accento"]
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
        if self._modo_marcacion == "salida":
            texto = "MARCAR SALIDA"
        elif self._modo_marcacion == self.COMPLETADA:
            texto = "JORNADA COMPLETADA"
        else:
            texto = "MARCAR ENTRADA"
        c.create_text(w // 2, h // 2, text=texto,
                      fill=COLORES["texto_blanco"], font=("Helvetica", 11, "bold"))

    def _marcar(self):
        """Inicia el proceso de marcación de asistencia en segundo plano.

        @return None: Ejecuta la operación de guardar la marca sin bloquear la interfaz.
        """
        if self._modo_marcacion == self.COMPLETADA:
            self._mostrar_estado("  \u2713  Jornada completada hoy", exito=True)
            return
        if not self.db_ok or self.db is None:
            self._mostrar_estado("Conectando a la base de datos...", exito=False)
            return

        threading.Thread(target=self._guardar_marcacion, daemon=True).start()

    def _guardar_marcacion(self):
        """Guarda la marca de entrada o salida en la base de datos con validaciones de negocio.

        @return None: Actualiza la jornada y los estados de la UI según el resultado.
        """
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
                sal = Marcacion.buscar(self.db, self.usuario, accion=Marcacion.SALIDA)
                if sal:
                    self._aplicar_salida_bd(sal)
                    self._mostrar_estado("  \u26a0  Ya registraste tu salida hoy", exito=False)
                    return

            marcacion = Marcacion.ahora(self.usuario, correo=self.correo, accion=tipo)
            marcacion.hora = self._hora_seleccionada()

            atrasado = marcacion.es_entrada_atrasada()
            salida_anticipada = marcacion.es_salida_anticipada()
            marcacion.guardar(self.db, atrasado=atrasado, salida_anticipada=salida_anticipada)

            try:
                if atrasado:
                    Alerta.crear(self.db, Alerta.TIPO_ATRASO, self.usuario,
                                 marcacion.fecha, marcacion.hora)
                if salida_anticipada:
                    Alerta.crear(self.db, Alerta.TIPO_SALIDA_ANTICIPADA, self.usuario,
                                 marcacion.fecha, marcacion.hora)
            except Exception:
                pass

            self._marcacion_guardada(marcacion, atrasado, salida_anticipada)
        except Exception as e:
            self._mostrar_estado(f"  \u26a0  Error al guardar: {e}", exito=False)

    def _marcacion_guardada(self, marcacion, atrasado=False, salida_anticipada=False):
        """Actualiza la interfaz tras guardar una marca de asistencia correctamente.

        @param marcacion: Objeto de marcación recién guardado.
        @param atrasado: Indica si la entrada fue tarde.
        @param salida_anticipada: Indica si la salida se registró antes de tiempo.
        @return None: Cambia el estado visual y de jornada según la nueva marca.
        """
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
            self._modo_marcacion = self.COMPLETADA
        self._dibujar_boton()

    def _mostrar_estado(self, msg, exito=False):
        """Muestra un mensaje de estado con color según sea correcto o advertencia.

        @param msg: Texto a mostrar al usuario.
        @param exito: Indica si el estado es positivo o de error/alerta.
        @return None: Actualiza la etiqueta de estado de la UI.
        """
        self.lbl_estado.config(
            text=msg,
            fg=COLORES["exito"] if exito else COLORES["error"],
        )

    def _fijar_hora_ahora(self):
        """Rellena el selector de horario con la hora actual del sistema.

        @return None: Sincroniza los campos del tiempo con la hora local actual.
        """
        from datetime import datetime
        ahora = datetime.now()
        self.spn_hh.delete(0, tk.END)
        self.spn_hh.insert(0, f"{ahora.hour:02d}")
        self.spn_mm.delete(0, tk.END)
        self.spn_mm.insert(0, f"{ahora.minute:02d}")

    def _hora_seleccionada(self):
        """Obtiene la hora elegida por el usuario en formato HH:MM:SS.

        @return str: Hora seleccionada o la hora actual si la entrada es inválida.
        """
        from datetime import datetime
        try:
            hh = max(0, min(23, int(self.spn_hh.get())))
            mm = max(0, min(59, int(self.spn_mm.get())))
            return f"{hh:02d}:{mm:02d}:00"
        except ValueError:
            return datetime.now().strftime("%H:%M:%S")

    def _aplicar_entrada_bd(self, ent):
        """Carga la hora de entrada de la base de datos y muestra el estado asociado.

        @param ent: Diccionario con los datos de la marcación de entrada.
        @return None: Actualiza la interfaz para reflejar la jornada ya registrada.
        """
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

    def _aplicar_salida_bd(self, sal):
        """Carga la hora de salida de la base de datos y muestra el estado asociado.

        @param sal: Diccionario con los datos de la marcación de salida.
        @return None: Actualiza la interfaz para reflejar la jornada completada.
        """
        hora = sal.get("hora") or ""
        self._jornada["salida"] = hora
        self.lbl_salida.config(text=hora)
        if sal.get("salida_anticipada"):
            self.lbl_salida.config(fg=COLORES["error"])
        else:
            self.lbl_salida.config(fg=COLORES["titulo_panel"])
        self._modo_marcacion = self.COMPLETADA
        self._dibujar_boton()

    def _abrir_gestion_usuarios(self):
        """Abre la pantalla de gestión de usuarios desde la ventana actual.

        @return None: Carga la vista de administración de usuarios.
        """
        import gestion_usuarios
        gestion_usuarios.GestionUsuariosApp(self.ventana, self.usuario)

    def _abrir_gestion_registros(self):
        """Abre la pantalla de gestión de registros del sistema.

        @return None: Inicia la vista de administración de registros.
        """
        import gestion_registros
        gestion_registros.GestionRegistrosApp(self.ventana, self.usuario)

    def _abrir_reporte_inasistencias(self):
        """Abre el módulo de reportes de inasistencias para el usuario administrador.

        @return None: Carga la interfaz del reporte de inasistencias.
        """
        import gestion_registros
        gestion_registros.ReporteInasistenciasApp(self.ventana)

    def _cerrar_sesion(self):
        """Cierra la sesión actual y vuelve a la pantalla de login.

        @return None: Cierra la ventana principal; el controlador reabre el login.
        """
        self._detener_reloj()
        self.volver_login = True
        self.ventana.destroy()

    def _cerrar_ventana_pura(self):
        self._detener_reloj()
        self.ventana.destroy()

    def _iniciar_animacion_entrada(self):
        """Inicia la animación de aparición de la ventana principal.

        @return None: Programa la transición visual de entrada de la UI.
        """
        self.ventana.after(30, self._fade_in, 0.0)

    def _fade_in(self, alpha):
        """Desvanece la ventana hasta dejarla visible a nivel del usuario.

        @param alpha: Valor actual de transparencia de la ventana.
        @return None: Actualiza la transparencia y reprograma la siguiente etapa de la animación.
        """
        if alpha < 1.0:
            alpha += 0.05
            self.ventana.attributes("-alpha", min(alpha, 1.0))
            self.ventana.after(15, self._fade_in, alpha)

    def _iniciar_arrastre(self, e):
        """Guarda la posición inicial del cursor para permitir arrastrar la ventana.

        @param e: Evento del mouse capturado al presionar el botón izquierdo.
        @return None: Registra el desplazamiento inicial del arrastre.
        """
        self._offset_x = e.x
        self._offset_y = e.y

    def _arrastrar(self, e):
        """Mueve la ventana según el desplazamiento actual del mouse.

        @param e: Evento del mouse durante el arrastre de la ventana.
        @return None: Reposiciona la ventana en la pantalla.
        """
        x = self.ventana.winfo_x() + e.x - self._offset_x
        y = self.ventana.winfo_y() + e.y - self._offset_y
        self.ventana.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    UsuarioApp()
