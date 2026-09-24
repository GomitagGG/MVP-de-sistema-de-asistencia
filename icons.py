import math


def _canvas(width, height, color="#FFFFFF"):
    """Crea un canvas de Tkinter con tamaño y fondo determinados.

    @param width: Ancho del canvas en píxeles.
    @param height: Alto del canvas en píxeles.
    @param color: Color de fondo del canvas.
    @return tk.Canvas: Objeto canvas configurado con el color recibido.
    """
    import tkinter as tk
    c = tk.Canvas(
        width=width,
        height=height,
        bg=color,
        highlightthickness=0,
        bd=0,
    )
    c.color = color
    return c


def _figura(c, color):
    """Normaliza el color que se utilizará en un icono.

    @param c: Contexto del canvas sobre el que se dibuja.
    @param color: Color original o None para aplicar el valor por defecto.
    @return str: Código hexadecimal del color final.
    """
    color = "#94A3B8" if color is None else color
    return color


def _casa(c, s, color):
    """Dibuja un icono de casa con líneas y un rectángulo base.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del contorno del icono.
    @return None: Agrega las formas geométricas al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.2
    w = s - 2 * pad
    x = pad
    y = s * 0.28
    c.create_polygon(x + w / 2, y - w * 0.18, x + w, y + w * 0.4,
                     x + w, y + w, w / 4, w, w / 4, w / 2, w / 2, w / 2,
                     fill="", outline=color, width=max(1, s // 10),
                     joinstyle="round")
    c.create_rectangle(x + w / 4, y + w * 0.55, x + w * 0.45, y + w,
                       fill="", outline=color, width=max(1, s // 10))


def _reloj(c, s, color):
    """Dibuja un icono de reloj con cara y manecillas.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del contorno del icono.
    @return None: Agrega las líneas y el círculo del reloj.
    """
    color = _figura(c, color)
    pad = s * 0.18
    r = (s - 2 * pad) / 2
    cx = s / 2
    cy = s / 2
    c.create_oval(pad, pad, s - pad, s - pad, outline=color, width=max(1, s // 10))
    c.create_line(cx, cy, cx, cy - r * 0.6, fill=color, width=max(1, s // 10))
    c.create_line(cx, cy, cx + r * 0.5, cy + r * 0.2, fill=color, width=max(1, s // 10))


def _grafica(c, s, color):
    """Dibuja un icono de gráfica con barras y una línea base.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del contorno y las líneas.
    @return None: Agrega la visualización del gráfico.
    """
    color = _figura(c, color)
    pad = s * 0.2
    x = [s * 0.22, s * 0.42, s * 0.62, s * 0.8]
    y = [s * 0.68, s * 0.5, s * 0.62, s * 0.34]
    c.create_line(pad, s - pad * 0.55, s - pad, s - pad * 0.55,
                  fill=color, width=max(1, s // 12))
    for xi, yi in zip(x, y):
        w = s * 0.08
        c.create_line(xi, s - pad * 0.55, xi, yi, fill=color, width=max(1, s // 8))
        c.create_rectangle(xi - w, yi, xi + w, s - pad * 0.55,
                           fill="", outline=color, width=max(1, s // 12))


def _usuarios(c, s, color):
    """Dibuja un icono de usuarios con dos figuras humanas.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del contorno del icono.
    @return None: Agrega las siluetas de usuario al canvas.
    """
    color = _figura(c, color)
    cx = s * 0.36
    cy = s * 0.4
    r = s * 0.12
    c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=max(1, s // 10))
    c.create_arc(cx - r * 2, cy, cx + r * 2, cy + r * 2.6,
                 start=190, extent=160, style="arc",
                 outline=color, width=max(1, s // 10))
    cx = s * 0.66
    r = s * 0.1
    c.create_oval(cx - r, cy - r * 0.65, cx + r, cy + r * 0.35,
                  outline=color, width=max(1, s // 12))
    c.create_arc(cx - r * 2, cy + r * 0.1, cx + r * 2, cy + r * 2.9,
                 start=190, extent=150, style="arc",
                 outline=color, width=max(1, s // 12))


def _engranaje(c, s, color):
    """Dibuja un icono de engranaje con radios y un aro central.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del contorno del engranaje.
    @return None: Agrega las líneas y óvalos del engranaje.
    """
    color = _figura(c, color)
    cx = s / 2
    cy = s / 2
    r = s * 0.22
    for i in range(8):
        a = math.radians(i * 45)
        x1 = cx + math.cos(a) * r * 0.9
        y1 = cy + math.sin(a) * r * 0.9
        x2 = cx + math.cos(a) * r * 1.9
        y2 = cy + math.sin(a) * r * 1.9
        c.create_line(x1, y1, x2, y2, fill=color, width=max(1, s // 9),
                      capstyle="round")
    c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=max(1, s // 10))
    c.create_oval(cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35,
                  outline=color, width=max(1, s // 12))


def _cerrar(c, s, color):
    """Dibuja un icono de cierre con dos líneas diagonales.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color de la cruz de cierre.
    @return None: Agrega las líneas diagonales al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.28
    c.create_line(pad, pad, s - pad, s - pad, fill=color, width=max(1, s // 9))
    c.create_line(s - pad, pad, pad, s - pad, fill=color, width=max(1, s // 9))


def _campana(c, s, color):
    """Dibuja un icono de campana con arcos y un cuerpo central.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del contorno de la campana.
    @return None: Agrega la campana al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.25
    cx = s / 2
    top = s * 0.18
    c.create_arc(pad - s * 0.1, top, s - pad + s * 0.1, s * 0.62, start=0, extent=180,
                 outline=color, width=max(1, s // 10), style="arc")
    c.create_line(cx - s * 0.14, s * 0.74, cx + s * 0.14, s * 0.74,
                  fill=color, width=max(1, s // 10))
    rx = s * 0.07
    c.create_oval(cx - rx, s * 0.72, cx + rx, s * 0.86, fill="", outline=color,
                  width=max(1, s // 12))


def _check(c, s, color):
    """Dibuja un icono de verificación con una marca de check.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color de la marca de validación.
    @return None: Agrega la marca de check al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.22
    c.create_line(pad, s * 0.55, s * 0.44, s * 0.8, fill=color, width=max(2, s // 7),
                  capstyle="round", joinstyle="round")
    c.create_line(s * 0.44, s * 0.8, s - pad, s * 0.2, fill=color, width=max(2, s // 7),
                  capstyle="round", joinstyle="round")


def _exclamacion(c, s, color):
    """Dibuja un icono de exclamación con forma vertical y punto.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color de la exclamación.
    @return None: Agrega la figura de advertencia al canvas.
    """
    color = _figura(c, color)
    cx = s / 2
    c.create_line(cx, s * 0.2, cx, s * 0.62, fill=color, width=max(2, s // 6),
                  capstyle="round")
    c.create_oval(cx - s * 0.06, s * 0.76, cx + s * 0.06, s * 0.88,
                  fill=color, outline="")


def _calendario(c, s, color):
    """Dibuja un icono de calendario con panel y líneas internas.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del contorno del calendario.
    @return None: Agrega el calendario al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.2
    c.create_rectangle(pad, s * 0.2, s - pad, s - pad, outline=color,
                       width=max(1, s // 11))
    c.create_line(s * 0.28, s * 0.1, s * 0.28, s * 0.32, fill=color, width=max(1, s // 11))
    c.create_line(s * 0.72, s * 0.1, s * 0.72, s * 0.32, fill=color, width=max(1, s // 11))
    c.create_line(pad, s * 0.42, s - pad, s * 0.42, fill=color, width=max(1, s // 11))
    c.create_line(s * 0.42, s * 0.6, s * 0.54, s * 0.6, fill=color, width=max(1, s // 11))


def _filtro(c, s, color):
    """Dibuja un icono de filtro con varias barras y bolitas.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del filtro.
    @return None: Agrega los elementos del filtro al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.22
    c.create_line(pad, s * 0.28, s - pad, s * 0.28, fill=color, width=max(1, s // 9))
    c.create_line(s * 0.34, s * 0.28, s * 0.34, s * 0.72, fill=color, width=max(1, s // 9))
    c.create_oval(s * 0.32, s * 0.72, s * 0.42, s * 0.82, fill=color, outline="")
    c.create_line(s * 0.5, s * 0.28, s * 0.5, s * 0.64, fill=color, width=max(1, s // 9))
    c.create_oval(s * 0.48, s * 0.64, s * 0.58, s * 0.74, fill=color, outline="")
    c.create_line(s * 0.66, s * 0.28, s * 0.66, s * 0.6, fill=color, width=max(1, s // 9))
    c.create_oval(s * 0.64, s * 0.6, s * 0.74, s * 0.7, fill=color, outline="")


def _descarga(c, s, color):
    """Dibuja un icono de descarga con flecha y línea base.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color de la descarga.
    @return None: Agrega la flecha y la línea de descarga al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.22
    c.create_line(s * 0.3, s * 0.44, s * 0.5, s * 0.64, fill=color, width=max(1, s // 9))
    c.create_line(s * 0.7, s * 0.44, s * 0.5, s * 0.64, fill=color, width=max(1, s // 9))
    c.create_line(pad * 0.6, s - pad, s - pad * 0.6, s - pad, fill=color,
                  width=max(1, s // 9))
    c.create_line(s * 0.5, s * 0.16, s * 0.5, s * 0.62, fill=color, width=max(1, s // 9))


def _cruz(c, s, color):
    """Dibuja un icono de cruz con líneas verticales y horizontales.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color de la cruz.
    @return None: Agrega las líneas de la cruz al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.3
    c.create_line(s * 0.5, pad, s * 0.5, s - pad, fill=color, width=max(1, s // 8))
    c.create_line(pad, s * 0.5, s - pad, s * 0.5, fill=color, width=max(1, s // 8))


def _bolígrafo(c, s, color):
    """Dibuja un icono de bolígrafo con trazo angular.

    @param c: Canvas donde se dibuja el icono.
    @param s: Tamaño del icono.
    @param color: Color del bolígrafo.
    @return None: Agrega la forma del bolígrafo al canvas.
    """
    color = _figura(c, color)
    pad = s * 0.2
    c.create_line(pad, s - pad, s * 0.3, s - pad, fill=color, width=max(1, s // 9))
    c.create_line(s - pad, pad, s * 0.34, s * 0.62, fill=color, width=max(1, s // 9))
    c.create_line(s * 0.28, s * 0.68, s * 0.52, s * 0.44, fill=color, width=max(1, s // 12))


ICONOS = {
    "home": _casa,
    "reloj": _reloj,
    "grafica": _grafica,
    "usuarios": _usuarios,
    "config": _engranaje,
    "cerrar": _cerrar,
    "campana": _campana,
    "check": _check,
    "exclamacion": _exclamacion,
    "calendario": _calendario,
    "filtro": _filtro,
    "descarga": _descarga,
    "cruz": _cruz,
    "editar": _bolígrafo,
}


def crear_icono(nombre, size=22, color="#94A3B8", bg="#111827", master=None):
    """Genera un widget de icono para ser usado en la interfaz.

    @param nombre: Nombre del icono a dibujar.
    @param size: Tamaño del icono en píxeles.
    @param color: Color del trazo del icono.
    @param bg: Color de fondo del canvas del icono.
    @param master: Contenedor principal del widget.
    @return tk.Canvas: Canvas con el icono dibujado y listo para mostrarse.
    """
    import tkinter as tk
    if master is None:
        master = tk.Frame()
    c = tk.Canvas(
        master,
        width=size,
        height=size,
        bg=bg,
        highlightthickness=0,
        bd=0,
    )
    c.create_rectangle(0, 0, size, size, fill=bg, outline="")
    fn = ICONOS.get(nombre, _casa)
    fn(c, size, color)
    c.pack_forget()
    return c