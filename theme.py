COLORS = {
    "bg_app": "#0B1020",
    "bg_sidebar": "#111827",
    "bg_topbar": "#0F172A",
    "surface": "#171E2E",
    "surface_raised": "#202A3C",
    "surface_hover": "#26344A",
    "input_bg": "#0F172A",
    "border": "#293448",
    "border_active": "#52627A",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "accent": "#E85561",
    "accent_hover": "#F26772",
    "accent_dark": "#B83F4A",
    "success": "#35C48D",
    "success_bg": "#163C35",
    "warning": "#F4B860",
    "warning_bg": "#46371F",
    "danger": "#F06A6A",
    "danger_bg": "#48252E",
    "info": "#4D8DDB",
    "white": "#FFFFFF",
    "black": "#000000",
}

FONTS = {
    "page_title": ("Segoe UI", 25, "bold"),
    "page_subtitle": ("Segoe UI", 11),
    "card_title": ("Segoe UI", 11, "bold"),
    "metric_value": ("Segoe UI", 28, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "small_bold": ("Segoe UI", 9, "bold"),
    "nav": ("Segoe UI", 10),
    "nav_active": ("Segoe UI", 10, "bold"),
    "table_header": ("Segoe UI", 9, "bold"),
}


def configure_styles(root=None):
    """Configura los estilos visuales del tema oscuro para la interfaz Tkinter.

    @param root: Raíz de Tkinter sobre la que se aplicará el estilo.
    @return ttk.Style: Estilo configurado y listo para usar en la aplicación.
    """
    from tkinter import ttk
    c = COLORS
    f = FONTS
    style = ttk.Style(root) if root else ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Dark.Treeview",
        background=c["surface"],
        fieldbackground=c["surface"],
        foreground=c["text_primary"],
        borderwidth=0,
        relief="flat",
        rowheight=64,
        font=f["body"],
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", c["surface_raised"])],
        foreground=[("selected", c["text_primary"])],
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=c["surface_raised"],
        foreground=c["text_secondary"],
        borderwidth=0,
        relief="flat",
        padding=(12, 14),
        font=f["table_header"],
    )
    style.map(
        "Dark.Treeview.Heading",
        background=[("active", c["surface_hover"])],
    )

    style.configure(
        "Dark.TNotebook",
        background=c["bg_app"],
        borderwidth=0,
    )
    style.configure(
        "Dark.TNotebook.Tab",
        background=c["surface"],
        foreground=c["text_secondary"],
        padding=(16, 10),
        font=f["body_bold"],
        borderwidth=0,
    )
    style.map(
        "Dark.TNotebook.Tab",
        background=[("selected", c["surface_raised"])],
        foreground=[("selected", c["text_primary"])],
    )
    try:
        style.layout("Dark.TNotebook.Tab", [
            ("Dark.TNotebook.Tab", {
                "sticky": "nswe",
                "children": [
                    ("Notebook.focus", {
                        "side": "top",
                        "sticky": "nswe",
                        "children": [
                            ("Notebook.label", {"side": "top", "sticky": ""}),
                        ],
                    }),
                ],
            }),
        ])
    except Exception:
        pass

    style.configure(
        "Dark.Scrollbar",
        background=c["surface_raised"],
        troughcolor=c["surface"],
        bordercolor=c["surface"],
        arrowcolor=c["text_secondary"],
        relief="flat",
    )
    try:
        layout_vertical = style.layout("Vertical.TScrollbar")
        style.layout("Dark.Scrollbar", layout_vertical)
        style.layout("Vertical.Dark.Scrollbar", layout_vertical)
    except Exception:
        pass
    try:
        style.layout("Horizontal.Dark.Scrollbar", style.layout("Horizontal.TScrollbar"))
    except Exception:
        pass

    style.configure(
        "Dark.TCombobox",
        fieldbackground=c["input_bg"],
        background=c["input_bg"],
        foreground=c["text_primary"],
        arrowcolor=c["text_secondary"],
        bordercolor=c["border"],
        lightcolor=c["surface_raised"],
        darkcolor=c["surface_raised"],
        selectbackground=c["surface_raised"],
        selectforeground=c["text_primary"],
        padding=8,
        font=f["body"],
    )
    style.map(
        "Dark.TCombobox",
        bordercolor=[("focus", c["border_active"])],
        fieldbackground=[("readonly", c["input_bg"])],
        selectbackground=[("readonly", c["input_bg"])],
        selectforeground=[("readonly", c["text_primary"])],
    )
    return style