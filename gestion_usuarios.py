import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import sys

from modelos import get_db
from google.cloud.firestore_v1.base_query import FieldFilter


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
    return os.path.join(carpeta, "cache_usuarios.json")


def _cargar_cache():
    try:
        with open(_ruta_cache()) as f:
            return json.load(f)
    except Exception:
        return {}


def _guardar_cache(usuario, datos):
    cache = _cargar_cache()
    if datos is None:
        cache.pop(usuario, None)
    else:
        cache[usuario] = datos
    try:
        with open(_ruta_cache(), "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


class GestionUsuariosApp:
    def __init__(self, padre, usuario_actual=""):
        self.padre = padre
        self.usuario_actual = usuario_actual
        self.db = None
        self.usuarios = []
        self.seleccion_id = None
        self.firebase_ok = False

        self.ventana = tk.Toplevel(padre)
        self.ventana.title("Gesti\u00f3n de Usuarios")
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self._centrar_ventana(760, 540)
        self._offset_x = 0
        self._offset_y = 0
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
            self._cargar_usuarios()
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo conectar a la base de datos:\n{msg}"))

    def _construir_ui(self):
        header = tk.Frame(self.ventana, bg=COLORES["panel_izq"])
        header.pack(fill="x")
        tk.Label(
            header, text="GESTI\u00d3N DE USUARIOS",
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
            cuerpo, text="Cargando usuarios...", bg=COLORES["bg_oscuro"],
            fg=COLORES["texto_gris"], font=("Helvetica", 9),
        )
        self.lbl_estado.pack(anchor="w", pady=(0, 6))

        cont_tabla = tk.Frame(cuerpo, bg=COLORES["card_bg"])
        cont_tabla.pack(fill="both", expand=True)

        cols = ("usuario", "rol", "nombre", "correo")
        self.tabla = ttk.Treeview(
            cont_tabla, columns=cols, show="headings",
            selectmode="browse",
        )
        self.tabla.heading("usuario", text="Usuario")
        self.tabla.heading("rol", text="Rol")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("correo", text="Correo")
        self.tabla.column("usuario", width=120)
        self.tabla.column("rol", width=110)
        self.tabla.column("nombre", width=180)
        self.tabla.column("correo", width=220)
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

        _btn("CREAR USUARIO", self._abrir_crear, COLORES["accento"]).pack(side="left", padx=(0, 8))
        _btn("MODIFICAR USUARIO", self._abrir_modificar, COLORES["accento_oscuro"]).pack(side="left", padx=(0, 8))
        _btn("ELIMINAR USUARIO", self._eliminar_seleccionado, COLORES["panel_izq"]).pack(side="left")

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
        for u in self.usuarios:
            vals = " ".join(str(v or "").lower() for v in [u.get("usuario"), u.get("rol"),
                           u.get("nombre"), u.get("correo")])
            if texto and texto not in vals:
                continue
            self._insertar_fila(u)

    def _insertar_fila(self, u):
        self.tabla.insert("", "end", iid=u.get("__id"),
                          values=(u.get("usuario", ""), u.get("rol", ""),
                                  u.get("nombre", ""), u.get("correo", "")))

    def _cargar_usuarios(self):
        try:
            docs = self.db.collection("usuarios").get()
            self.usuarios = []
            for d in docs:
                data = d.to_dict()
                data["__id"] = d.id
                self.usuarios.append(data)
            self.ventana.after(0, self._refrescar_tabla)
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo cargar los usuarios:\n{msg}"))

    def _refrescar_tabla(self):
        self.lbl_estado.config(text=f"{len(self.usuarios)} usuario(s) cargado(s).")
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for u in self.usuarios:
            self._insertar_fila(u)

    def _obtener_seleccionado(self):
        if not self.seleccion_id:
            messagebox.showwarning("Advertencia", "Selecciona un usuario de la lista.")
            return None
        for u in self.usuarios:
            if u.get("__id") == self.seleccion_id:
                return u
        return None

    def _abrir_crear(self):
        self._abrir_formulario(None)

    def _abrir_modificar(self):
        u = self._obtener_seleccionado()
        if u:
            self._abrir_formulario(u)

    def _abrir_formulario(self, usuario_existente):
        GestionUsuarioForm(self, usuario_existente)

    def _eliminar_seleccionado(self):
        u = self._obtener_seleccionado()
        if not u:
            return
        if self.usuario_actual and u.get("usuario") == self.usuario_actual:
            messagebox.showwarning(
                "Acci\u00f3n no permitida",
                "No puedes eliminar al usuario que est\u00e1 actualmente en sesi\u00f3n.")
            return
        resp = messagebox.askyesno(
            "Confirmar eliminaci\u00f3n",
            f"\u00bfSeguro que deseas eliminar al usuario\n'{u.get('usuario')}'?\n\nEsta acci\u00f3n no se puede deshacer.",
        )
        if not resp:
            return
        threading.Thread(target=self._eliminar_en_db, args=(u,), daemon=True).start()

    def _eliminar_en_db(self, u):
        try:
            self.db.collection("usuarios").document(u["__id"]).delete()
            _guardar_cache(u.get("usuario"), None)
            self.ventana.after(0, lambda: (self._cargar_usuarios(),
                                           messagebox.showinfo("Eliminado",
                                           f"Usuario '{u.get('usuario')}' eliminado correctamente.")))
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo eliminar el usuario:\n{msg}"))

    def _guardar_creado(self, datos, id_documento):
        try:
            self.db.collection("usuarios").document(id_documento).set(datos)
            _guardar_cache(datos["usuario"], dict(datos))
            self.ventana.after(0, lambda: (self._cargar_usuarios(),
                                           messagebox.showinfo("Guardado",
                                           "Usuario creado correctamente.")))
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo guardar el usuario:\n{msg}"))

    def _guardar_modificado(self, id_documento, datos):
        try:
            self.db.collection("usuarios").document(id_documento).set(datos)
            _guardar_cache(datos["usuario"], dict(datos))
            self.ventana.after(0, lambda: (self._cargar_usuarios(),
                                           messagebox.showinfo("Guardado",
                                           "Cambios guardados correctamente.")))
        except Exception as e:
            msg = str(e)
            self.ventana.after(0, lambda: messagebox.showerror(
                "Error", f"No se pudo guardar los cambios:\n{msg}"))


class GestionUsuarioForm:
    def __init__(self, gestor, usuario_existente):
        self.gestor = gestor
        self.usuario_existente = usuario_existente

        self.ventana = tk.Toplevel(gestor.ventana)
        self.ventana.title("Modificar Usuario" if usuario_existente else "Crear Usuario")
        self.ventana.config(bg=COLORES["bg_oscuro"])
        self._centrar_ventana(440, 480)
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

        titulo = "MODIFICAR USUARIO" if self.usuario_existente else "CREAR USUARIO"
        tk.Label(
            cont, text=titulo, bg=COLORES["bg_oscuro"], fg=COLORES["titulo_panel"],
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(0, 14))

        entradas = {}
        campos = [
            ("usuario", "USUARIO", True),
            ("clave", "CONTRASE\u00d1A", True),
            ("rol", "ROL", True),
            ("nombre", "NOMBRE COMPLETO", False),
            ("correo", "CORREO", True),
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

        for clave, etiqueta, es_requerido in campos:
            if clave == "rol":
                cont_campo = tk.Frame(cont, bg=COLORES["bg_oscuro"])
                cont_campo.pack(fill="x", pady=5)
                tk.Label(
                    cont_campo, text=etiqueta, bg=COLORES["bg_oscuro"],
                    fg=COLORES["texto_gris"], font=("Helvetica", 8, "bold"), anchor="w",
                ).pack(anchor="w")
                var = tk.StringVar()
                combo = ttk.Combobox(
                    cont_campo, textvariable=var, state="readonly",
                    values=["administrador", "trabajador"],
                )
                combo.pack(fill="x", ipady=3)
                entradas[clave] = (var, combo)
            else:
                entradas[clave] = _campo(clave, etiqueta)

        datos = self.usuario_existente or {}
        for clave in campos:
            k = clave[0]
            valor = datos.get(k, "")
            if k == "rol":
                entradas[k][0].set(valor if valor in ("administrador", "trabajador") else "trabajador")
            else:
                entradas[k].insert(0, valor if valor else "")

        if self.usuario_existente:
            entradas["usuario"].config(state="disabled")

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
        import re
        usuario = entradas["usuario"].get().strip()
        clave = entradas["clave"].get().strip()
        rol = entradas["rol"][0].get().strip()
        correo = entradas["correo"].get().strip()

        if not usuario or not clave or not rol or not correo:
            self.lbl_error.config(
                text="Los campos Usuario, Contrase\u00f1a, Rol y Correo son obligatorios.")
            return False

        patron = r"^[\w\.\-]+@[\w\-]+\.[\w\.\-]+$"
        if not re.match(patron, correo):
            self.lbl_error.config(text="El correo ingresado no tiene un formato v\u00e1lido.")
            return False

        if not self.usuario_existente:
            existing = self.gestor.db.collection("usuarios")\
                .where(filter=FieldFilter("usuario", "==", usuario)).limit(1).get()
            if len(existing) > 0:
                self.lbl_error.config(text="Ya existe un usuario con ese nombre.")
                return False
        return True

    def _guardar(self, entradas):
        from datetime import datetime
        if not self._validar(entradas):
            return

        datos = {
            "usuario": entradas["usuario"].get().strip(),
            "clave": entradas["clave"].get().strip(),
            "rol": entradas["rol"][0].get().strip(),
            "nombre": entradas["nombre"].get().strip(),
            "correo": entradas["correo"].get().strip(),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
        }

        if self.usuario_existente:
            id_doc = self.usuario_existente["__id"]
            self.ventana.destroy()
            threading.Thread(target=self.gestor._guardar_modificado,
                             args=(id_doc, datos), daemon=True).start()
        else:
            id_doc = datos["usuario"]
            self.ventana.destroy()
            threading.Thread(target=self.gestor._guardar_creado,
                             args=(datos, id_doc), daemon=True).start()
