# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

datas = [("img", "img"), ("icon", "icon")]
binaries = []
hiddenimports = ["gestion_usuarios", "usuarioventana"]

# Incluir la credencial de Firebase SOLO si existe (evita fallar el build).
# Se copia como firebase-key.json para que el exe siempre la encuentre.
for nombre in ["firebase-key.json",
               "registro-asistencia-bfe64-firebase-adminsdk-fbsvc-1d738c49d5.json"]:
    fuente = os.path.join("config", nombre)
    if os.path.exists(fuente):
        datas.append(("config/firebase-key.json", "config"))
        print(f"Credencial de Firebase incluida: {fuente}")

# Reunir datos/binarios/imports ocultos de los paquetes de Google/Firebase.
for modulo in ["google.cloud.firestore_v1", "google.api_core", "google.auth", "google.cloud"]:
    d, b, h = collect_all(modulo)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["primeraventana.py", "usuarioventana.py", "gestion_usuarios.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SistemaAsistencia",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="icon/Fixmol_icon.ico",
)