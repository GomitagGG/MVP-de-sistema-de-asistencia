# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['primeraventana.py', 'usuarioventana.py', 'gestion_usuarios.py', 'dashboard_admin.py', 'modelos.py', 'gestion_registros.py', 'theme.py', 'icons.py', 'components.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('img/Fixmol3.png', 'img'),
        ('icon/Fixmol_icon.ico', 'icon'),
    ],
    hiddenimports=['gestion_usuarios', 'dashboard_admin', 'modelos', 'gestion_registros', 'theme', 'icons', 'components'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# Incluir la credencial de Firebase SOLO si existe (evita fallar el build)
credencial = os.path.join('config', 'firebase-key.json')
if os.path.exists(credencial):
    a.datas += [('config/firebase-key.json', credencial, 'DATA')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SistemaAsistencia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/Fixmol_icon.ico',
)
