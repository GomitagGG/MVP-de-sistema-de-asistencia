import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import sys

from modelos import get_db


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


def _ruta_cache():
    if getattr(sys, "frozen", False):
        carpeta = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SistemaAsistencia")
    else:
        carpeta = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "cache_registros.json")


def _cargar_cache():
    try:
        with open(_ruta_cache()) as f:
            return json.load(f)
    except Exception:
        return {}


def _guardar_cache(id_registro, datos):
    cache = _cargar_cache()
    if datos is None:
        cache.pop(id_registro, None)
    else:
        cache[id_registro] = datos
    try:
        with open(_ruta_cache(), "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


def crear_id_registro(usuario, fecha, tipo):
    return f"{usuario}_{fecha}_{tipo}"


def _dias_habiles(fecha_inicio, fecha_fin):
    from datetime import date, timedelta
    inicio = date.fromisoformat(fecha_inicio)
    fin = date.fromisoformat(fecha_fin)
    dias = []
    d = inicio
    while d <= fin:
        if d.weekday() < 5:
            dias.append(d.isoformat())
        d += timedelta(days=1)
    return dias


def detectar_inasistencias(marcaciones, usuarios, fecha_inicio, fecha_fin):
    presentes = set()
    for m in marcaciones:
        if m.get("usuario") and m.get("fecha"):
            presentes.add((m["usuario"], m["fecha"]))
    dias = _dias_habiles(fecha_inicio, fecha_fin)
    inasistencias = []
    for u in usuarios:
        usr = u.get("usuario")
        if not usr:
            continue
        for d in dias:
            if (usr, d) not in presentes:
                inasistencias.append({"usuario": usr, "fecha": d})
    inasistencias.sort(key=lambda x: (x["fecha"], x["usuario"]))
    return inasistencias


def ultimo_dia_mes(fecha_inicio):
    from datetime import date, timedelta
    ano, mes = fecha_inicio.split("-")[:2]
    if mes == "12":
        fin = date(int(ano) + 1, 1, 1)
    else:
        fin = date(int(ano), int(mes) + 1, 1)
    fin -= timedelta(days=1)
    return fin.isoformat()


class GestionRegistrosApp:
    def __init__(self, padre, usuario_actual=""):
        self.padre = padre
        self.usuario_actual = usuario_actual
        self.db = None
        self.registros = []
        self.seleccion_id = None
        self.firebase_ok = False

        self.ventana = tk.Toplevel(padre)
        self.ventana.title("Gesti\u00f3n de Registros")
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self._centrar_ventana(760, 540)
        self.ventana.transient(padre)
        self.ventana.grab_set()

        self._construir_ui()
        threading.Thread(target=self._inicializar_db, daemon=True).start()

    def _centrar_ventana(self, w, h):
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.ventana.geometry(f"{w}x{h}+{x}+{y}")

    def _inicializar_db(self):
        try:
            self.db = get_db()
            self.firebase_ok = True
            self._cargar_registros()
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo conectar a la base de datos:\n{msg}"))

    def _construir_ui(self):
        header = tk.Frame(self.ventana, bg=COLORES["panel_izq"])
        header.pack(fill="x")
        tk.Label(
            header, text="GESTI\u00d3N DE REGISTROS",
            bg=COLORES["panel_izq"], fg=COLORES["titulo_panel"],
            font=("Helvetica", 14, "bold"),
        ).pack(side="left", padx=16, pady=12)
        tk.Button(
            header, text="CERRAR", bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            activebackground=COLORES["entry_borde"], activeforeground=COLORES["texto_blanco"],
            relief="flat", cursor="hand2", command=self.ventana.destroy,
        ).pack(side="right", padx=12, pady=8)

        cuerpo = tk.Frame(self.ventana, bg=COLORES["bg_oscuro"])
        cuerpo.pack(fill="both", expand=True, padx=14, pady=10)

        self.lbl_estado = tk.Label(
            cuerpo, text="Cargando registros...", bg=COLORES["bg_oscuro"],
            fg=COLORES["texto_gris"], font=("Helvetica", 9),
        )
        self.lbl_estado.pack(anchor="w", pady=(0, 6))

        cont_tabla = tk.Frame(cuerpo, bg=COLORES["card_bg"])
        cont_tabla.pack(fill="both", expand=True)

        cols = ("usuario", "fecha", "hora", "tipo")
        self.tabla = ttk.Treeview(
            cont_tabla, columns=cols, show="headings",
            selectmode="browse",
        )
        self.tabla.heading("usuario", text="Usuario")
        self.tabla.heading("fecha", text="Fecha")
        self.tabla.heading("hora", text="Hora")
        self.tabla.heading("tipo", text="Tipo")
        self.tabla.column("usuario", width=130)
        self.tabla.column("fecha", width=110)
        self.tabla.column("hora", width=90)
        self.tabla.column("tipo", width=110)
        self.tabla.pack(side="left", fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)

        scroll = ttk.Scrollbar(cont_tabla, orient="vertical", command=self.tabla.yview)
        scroll.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=scroll.set)

        barra = tk.Frame(cuerpo, bg=COLORES["bg_oscuro"])
        barra.pack(fill="x", pady=(10, 0))

        def _btn(texto, comando, color):
            return tk.Button(
                barra, text=texto, bg=color, fg=COLORES["texto_blanco"],
                activebackground=COLORES["accento_oscuro"],
                activeforeground=COLORES["texto_blanco"],
                font=("Helvetica", 10, "bold"), relief="flat",
                highlightthickness=0, cursor="hand2", command=comando,
            )

        _btn("CREAR REGISTRO", self._abrir_crear, COLORES["accento"]).pack(side="left", padx=(0, 8))
        _btn("MODIFICAR REGISTRO", self._abrir_modificar, COLORES["accento_oscuro"]).pack(side="left", padx=(0, 8))
        _btn("ELIMINAR REGISTRO", self._eliminar_seleccionado, COLORES["panel_izq"]).pack(side="left")

        cont_buscar = tk.Frame(cuerpo, bg=COLORES["bg_oscuro"])
        cont_buscar.pack(fill="x", pady=(10, 0))
        tk.Label(
            cont_buscar, text="Buscar:", bg=COLORES["bg_oscuro"],
            fg=COLORES["texto_gris"], font=("Helvetica", 9),
        ).pack(side="left")
        self.entry_buscar = tk.Entry(
            cont_buscar, bg=COLORES["entry_bg"], fg=COLORES["texto_blanco"],
            insertbackground=COLORES["texto_blanco"], relief="flat", bd=0,
            highlightthickness=1, highlightbackground=COLORES["entry_borde"],
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=8, ipady=5)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._filtrar())

    def _al_seleccionar(self, _evento=None):
        sel = self.tabla.selection()
        if sel:
            self.seleccion_id = sel[0]

    def _filtrar(self):
        texto = self.entry_buscar.get().strip().lower()
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for r in self.registros:
            vals = " ".join(str(v or "").lower() for v in [r.get("usuario"), r.get("fecha"),
                           r.get("hora"), r.get("tipo")])
            if texto and texto not in vals:
                continue
            self._insertar_fila(r)

    def _insertar_fila(self, r):
        self.tabla.insert("", "end", iid=r.get("__id"),
                          values=(r.get("usuario", ""), r.get("fecha", ""),
                                  r.get("hora", ""), r.get("tipo", "")))

    def _cargar_registros(self):
        try:
            docs = self.db.collection("marcaciones").get()
            self.registros = []
            for d in docs:
                data = d.to_dict()
                data["__id"] = d.id
                self.registros.append(data)
            self.registros.sort(key=lambda x: (str(x.get("fecha")), str(x.get("hora"))))
            self.ventana.after(0, self._refrescar_tabla)
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo cargar los registros:\n{msg}"))

    def _refrescar_tabla(self):
        self.lbl_estado.config(text=f"{len(self.registros)} registro(s) cargado(s).")
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for r in self.registros:
            self._insertar_fila(r)

    def _obtener_seleccionado(self):
        if not self.seleccion_id:
            messagebox.showwarning("Advertencia", "Selecciona un registro de la lista.")
            return None
        for r in self.registros:
            if r.get("__id") == self.seleccion_id:
                return r
        return None

    def _abrir_crear(self):
        self._abrir_formulario(None)

    def _abrir_modificar(self):
        r = self._obtener_seleccionado()
        if r:
            self._abrir_formulario(r)

    def _abrir_formulario(self, registro_existente):
        GestionRegistroForm(self, registro_existente)

    def _eliminar_seleccionado(self):
        r = self._obtener_seleccionado()
        if not r:
            return
        resp = messagebox.askyesno(
            "Confirmar eliminaci\u00f3n",
            f"\u00bfSeguro que deseas eliminar el registro\n"
            f"'{r.get('usuario')}' del {r.get('fecha')} ({r.get('tipo')})?\n\n"
            f"Esta acci\u00f3n no se puede deshacer.",
        )
        if not resp:
            return
        threading.Thread(target=self._eliminar_en_db, args=(r,), daemon=True).start()

    def _eliminar_en_db(self, r):
        try:
            self.db.collection("marcaciones").document(r["__id"]).delete()
            _guardar_cache(r["__id"], None)
            self.ventana.after(0, lambda: (self._cargar_registros(),
                                           messagebox.showinfo("Eliminado",
                                           "Registro eliminado correctamente.")))
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo eliminar el registro:\n{msg}"))

    def _guardar_creado(self, datos, id_documento):
        try:
            self.db.collection("marcaciones").document(id_documento).set(datos)
            _guardar_cache(id_documento, dict(datos))
            self.ventana.after(0, lambda: (self._cargar_registros(),
                                           messagebox.showinfo("Guardado",
                                           "Registro creado correctamente.")))
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo guardar el registro:\n{msg}"))

    def _guardar_modificado(self, id_documento, datos):
        try:
            self.db.collection("marcaciones").document(id_documento).set(datos)
            _guardar_cache(id_documento, dict(datos))
            self.ventana.after(0, lambda: (self._cargar_registros(),
                                           messagebox.showinfo("Guardado",
                                           "Cambios guardados correctamente.")))
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo guardar los cambios:\n{msg}"))


class GestionRegistroForm:
    def __init__(self, gestor, registro_existente):
        self.gestor = gestor
        self.registro_existente = registro_existente

        self.ventana = tk.Toplevel(gestor.ventana)
        self.ventana.title("Modificar Registro" if registro_existente else "Crear Registro")
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self._centrar_ventana(420, 400)
        self.ventana.transient(gestor.ventana)
        self.ventana.grab_set()

        self._construir_formulario()

    def _centrar_ventana(self, w, h):
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.ventana.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_formulario(self):
        cont = tk.Frame(self.ventana, bg=COLORES["bg_oscuro"])
        cont.pack(fill="both", expand=True, padx=20, pady=16)

        titulo = "MODIFICAR REGISTRO" if self.registro_existente else "CREAR REGISTRO"
        tk.Label(
            cont, text=titulo, bg=COLORES["bg_oscuro"], fg=COLORES["titulo_panel"],
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(0, 14))

        entradas = {}
        campos = [
            ("usuario", "USUARIO", True),
            ("tipo", "TIPO", True),
            ("fecha", "FECHA (AAAA-MM-DD)", True),
            ("hora", "HORA (HH:MM:SS)", True),
        ]

        def _campo(clave, etiqueta):
            cont_campo = tk.Frame(cont, bg=COLORES["bg_oscuro"])
            cont_campo.pack(fill="x", pady=5)
            tk.Label(
                cont_campo, text=etiqueta, bg=COLORES["bg_oscuro"],
                fg=COLORES["texto_gris"], font=("Helvetica", 8, "bold"), anchor="w",
            ).pack(anchor="w")
            entry = tk.Entry(
                cont_campo, bg=COLORES["entry_bg"], fg=COLORES["texto_blanco"],
                insertbackground=COLORES["texto_blanco"], relief="flat", bd=0,
                highlightthickness=1, highlightbackground=COLORES["entry_borde"],
                highlightcolor=COLORES["entry_borde_focus"],
            )
            entry.pack(fill="x", ipady=7)
            return entry

        cont_campo = tk.Frame(cont, bg=COLORES["bg_oscuro"])
        cont_campo.pack(fill="x", pady=5)
        tk.Label(
            cont_campo, text="USUARIO", bg=COLORES["bg_oscuro"],
            fg=COLORES["texto_gris"], font=("Helvetica", 8, "bold"), anchor="w",
        ).pack(anchor="w")
        var_usuario = tk.StringVar()
        combo_usuario = ttk.Combobox(cont_campo, textvariable=var_usuario, state="readonly")
        combo_usuario.pack(fill="x", ipady=3)
        entradas["usuario"] = (var_usuario, combo_usuario)

        cont_campo = tk.Frame(cont, bg=COLORES["bg_oscuro"])
        cont_campo.pack(fill="x", pady=5)
        tk.Label(
            cont_campo, text="TIPO", bg=COLORES["bg_oscuro"],
            fg=COLORES["texto_gris"], font=("Helvetica", 8, "bold"), anchor="w",
        ).pack(anchor="w")
        var_tipo = tk.StringVar()
        combo_tipo = ttk.Combobox(
            cont_campo, textvariable=var_tipo, state="readonly",
            values=["entrada", "salida"],
        )
        combo_tipo.pack(fill="x", ipady=3)
        entradas["tipo"] = (var_tipo, combo_tipo)

        entradas["fecha"] = _campo("fecha", "FECHA (AAAA-MM-DD)")
        entradas["hora"] = _campo("hora", "HORA (HH:MM:SS)")

        try:
            docs = self.gestor.db.collection("usuarios").get()
            usuarios = ["", "trabajador"] + [d.to_dict().get("usuario", "") for d in docs]
            combo_usuario["values"] = [u for u in usuarios if u]
        except Exception:
            combo_usuario["values"] = ["trabajador"]

        datos = self.registro_existente or {}
        combo_usuario["values"] = list(dict.fromkeys(combo_usuario["values"]))
        if datos.get("usuario") and datos["usuario"] not in combo_usuario["values"]:
            combo_usuario["values"] = combo_usuario["values"] + [datos["usuario"]]
        var_usuario.set(datos.get("usuario", ""))
        var_tipo.set(datos.get("tipo", "entrada"))
        entradas["fecha"].insert(0, datos.get("fecha", ""))
        entradas["hora"].insert(0, datos.get("hora", ""))

        if self.registro_existente:
            combo_usuario.config(state="disabled")
            combo_tipo.config(state="disabled")

        self.lbl_error = tk.Label(
            cont, text="", bg=COLORES["bg_oscuro"], fg=COLORES["error"],
            font=("Helvetica", 8),
        )
        self.lbl_error.pack(pady=(6, 0))

        barra = tk.Frame(cont, bg=COLORES["bg_oscuro"])
        barra.pack(fill="x", pady=(10, 0))

        tk.Button(
            barra, text="GUARDAR", bg=COLORES["accento"], fg=COLORES["texto_blanco"],
            activebackground=COLORES["accento_oscuro"], activeforeground=COLORES["texto_blanco"],
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            command=lambda: self._guardar(entradas),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            barra, text="CANCELAR", bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            activebackground=COLORES["entry_borde"], activeforeground=COLORES["texto_blanco"],
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            command=self.ventana.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _validar(self, entradas):
        import datetime
        import re
        usuario = entradas["usuario"][0].get().strip()
        tipo = entradas["tipo"][0].get().strip()
        fecha = entradas["fecha"].get().strip()
        hora = entradas["hora"].get().strip()

        if not usuario or not tipo or not fecha or not hora:
            self.lbl_error.config(text="Todos los campos son obligatorios.")
            return False

        if tipo not in ("entrada", "salida"):
            self.lbl_error.config(text="El tipo debe ser entrada o salida.")
            return False

        patron_fecha = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(patron_fecha, fecha):
            self.lbl_error.config(text="La fecha debe tener el formato AAAA-MM-DD.")
            return False
        try:
            datetime.date.fromisoformat(fecha)
        except ValueError:
            self.lbl_error.config(text="La fecha ingresada no es v\u00e1lida.")
            return False

        patron_hora = r"^\d{2}:\d{2}:\d{2}$"
        if not re.match(patron_hora, hora):
            self.lbl_error.config(text="La hora debe tener el formato HH:MM:SS.")
            return False

        if not self.registro_existente:
            id_doc = crear_id_registro(usuario, fecha, tipo)
            existing = self.gestor.db.collection("marcaciones").document(id_doc).get()
            if existing.exists:
                self.lbl_error.config(text="Ya existe un registro con esos datos.")
                return False
        return True

    def _guardar(self, entradas):
        if not self._validar(entradas):
            return

        usuario = entradas["usuario"][0].get().strip()
        tipo = entradas["tipo"][0].get().strip()
        datos = {
            "usuario": usuario,
            "tipo": tipo,
            "fecha": entradas["fecha"].get().strip(),
            "hora": entradas["hora"].get().strip(),
        }

        if self.registro_existente:
            id_doc = self.registro_existente["__id"]
            self.ventana.destroy()
            threading.Thread(target=self.gestor._guardar_modificado,
                             args=(id_doc, datos), daemon=True).start()
        else:
            id_doc = crear_id_registro(usuario, datos['fecha'], tipo)
            self.ventana.destroy()
            threading.Thread(target=self.gestor._guardar_creado,
                             args=(datos, id_doc), daemon=True).start()


class ReporteInasistenciasApp:
    def __init__(self, padre):
        self.padre = padre
        self.db = None
        self.usuarios = []
        self.inasistencias = []

        self.ventana = tk.Toplevel(padre)
        self.ventana.title("Reporte de Inasistencias")
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self._centrar_ventana(720, 500)
        self.ventana.transient(padre)
        self.ventana.grab_set()

        self._construir_ui()
        threading.Thread(target=self._inicializar_db, daemon=True).start()

    def _centrar_ventana(self, w, h):
        sw = self.ventana.winfo_screenwidth()
        sh = self.ventana.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.ventana.geometry(f"{w}x{h}+{x}+{y}")

    def _inicializar_db(self):
        try:
            self.db = get_db()
            self._cargar_datos()
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo conectar a la base de datos:\n{msg}"))

    def _construir_ui(self):
        from datetime import datetime
        self.mes_actual = datetime.now().strftime("%Y-%m")

        header = tk.Frame(self.ventana, bg=COLORES["panel_izq"])
        header.pack(fill="x")
        tk.Label(
            header, text="REPORTE DE INASISTENCIAS",
            bg=COLORES["panel_izq"], fg=COLORES["titulo_panel"],
            font=("Helvetica", 14, "bold"),
        ).pack(side="left", padx=16, pady=12)
        tk.Button(
            header, text="CERRAR", bg=COLORES["panel_izq"], fg=COLORES["texto_gris"],
            activebackground=COLORES["entry_borde"], activeforeground=COLORES["texto_blanco"],
            relief="flat", cursor="hand2", command=self.ventana.destroy,
        ).pack(side="right", padx=12, pady=8)

        cuerpo = tk.Frame(self.ventana, bg=COLORES["bg_oscuro"])
        cuerpo.pack(fill="both", expand=True, padx=14, pady=10)

        cont_mes = tk.Frame(cuerpo, bg=COLORES["bg_oscuro"])
        cont_mes.pack(fill="x", pady=(0, 8))
        tk.Label(
            cont_mes, text="Mes:", bg=COLORES["bg_oscuro"],
            fg=COLORES["texto_gris"], font=("Helvetica", 9),
        ).pack(side="left")
        self.var_mes = tk.StringVar(value=self.mes_actual)
        self.combo_mes = ttk.Combobox(
            cont_mes, textvariable=self.var_mes, state="readonly",
            values=self._generar_meses(),
        )
        self.combo_mes.pack(side="left", padx=8)
        self.combo_mes.bind("<<ComboboxSelected>>", lambda e: self._aplicar_reporte())

        self.lbl_estado = tk.Label(
            cuerpo, text="Calculando inasistencias...", bg=COLORES["bg_oscuro"],
            fg=COLORES["texto_gris"], font=("Helvetica", 9),
        )
        self.lbl_estado.pack(anchor="w", pady=(0, 2))

        tk.Label(
            cuerpo, text="Solo se consideran usuarios con al menos una marcaci\u00f3n registrada.",
            bg=COLORES["bg_oscuro"], fg=COLORES["texto_placeholder"],
            font=("Helvetica", 8),
        ).pack(anchor="w", pady=(0, 6))

        cont_tabla = tk.Frame(cuerpo, bg=COLORES["card_bg"])
        cont_tabla.pack(fill="both", expand=True)

        cols = ("fecha", "usuario", "nombre")
        self.tabla = ttk.Treeview(
            cont_tabla, columns=cols, show="headings",
            selectmode="browse",
        )
        self.tabla.heading("fecha", text="Fecha")
        self.tabla.heading("usuario", text="Identificador")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.column("fecha", width=120)
        self.tabla.column("usuario", width=140)
        self.tabla.column("nombre", width=260)
        self.tabla.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(cont_tabla, orient="vertical", command=self.tabla.yview)
        scroll.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=scroll.set)

    def _generar_meses(self):
        from datetime import datetime
        meses = []
        now = datetime.now()
        for i in range(6):
            ano = now.year
            mes = now.month - i
            while mes <= 0:
                mes += 12
                ano -= 1
            meses.append(f"{ano:04d}-{mes:02d}")
        return meses

    def _cargar_datos(self):
        try:
            self.usuarios = []
            for d in self.db.collection("usuarios").get():
                self.usuarios.append(d.to_dict())
            self.ventana.after(0, self._aplicar_reporte)
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo cargar los datos:\n{msg}"))

    def _aplicar_reporte(self):
        self.lbl_estado.config(text="Cargando...", fg=COLORES["texto_gris"])
        threading.Thread(target=self._calcular, daemon=True).start()

    def _calcular(self):
        try:
            mes = self.var_mes.get().strip()
            fecha_inicio = f"{mes}-01"
            fecha_fin = ultimo_dia_mes(fecha_inicio)
            registros = []
            for d in self.db.collection("marcaciones").get():
                registros.append(d.to_dict())
            usuarios_activos = self._usuarios_con_marcaciones(registros)
            self.inasistencias = detectar_inasistencias(
                registros, usuarios_activos, fecha_inicio, fecha_fin)
            self.ventana.after(0, self._refrescar_tabla)
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: self.lbl_estado.config(
                text=f"Error: {msg}", fg=COLORES["error"]))

    def _usuarios_con_marcaciones(self, registros):
        con_marcas = {m.get("usuario") for m in registros if m.get("usuario")}
        return [u for u in self.usuarios if u.get("usuario") in con_marcas]

    def _refrescar_tabla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        nombres = {u.get("usuario"): u.get("nombre", "") for u in self.usuarios}
        for i in self.inasistencias:
            self.tabla.insert("", "end",
                              values=(i["fecha"], i["usuario"], nombres.get(i["usuario"], "")))
        self.lbl_estado.config(
            text=f"{len(self.inasistencias)} inasistencia(s) en {self.var_mes.get()}.",
            fg=COLORES["exito"] if self.inasistencias else COLORES["texto_gris"])