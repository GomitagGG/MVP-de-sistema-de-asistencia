# MVP - Sistema de Registro de Asistencia

Aplicación de escritorio en **Python + Tkinter** para el control de asistencia de una empresa de 25 trabajadores (compra y venta de productos químicos). Almacena los datos en **Firebase Firestore**.

## Requerimientos cubiertos (según el caso)

| ID | Requerimiento | Estado |
|----|---------------|--------|
| CA-01 | Control de asistencia (entrada/salida) | ✅ |
| GU-01 | Crear usuarios (solo administrador) | ✅ |
| GU-02 | Modificar usuarios (solo administrador) | ✅ |
| GU-03 | Eliminar usuarios (solo administrador) | ✅ |
| RE-01 | Reporte de atrasos (después de 9:30 am) | Pendiente |
| RE-02 | Reporte de salidas anticipadas (antes de 17:30 pm) | Pendiente |
| RE-03 | Reporte de inasistencias | Pendiente |

## Estructura del proyecto

```
primeraventana.py      Ventana de Login (usa usuario + contraseña contra Firestore)
usuarioventana.py      Ventana del trabajador (marcar entrada/salida, cerrar sesión)
gestion_usuarios.py    Gestión de usuarios (CRUD, solo administrador)
crear_exe.bat          Genera el ejecutable .exe con PyInstaller
SistemaAsistencia.spec Configuración de PyInstaller
requirements.txt       Dependencias de Python
```

## Requisitos

- Python 3.12+
- Entorno virtual con las dependencias:
  ```
  py -m venv venv
  venv\Scripts\pip install -r requirements.txt
  ```

## Configuración de Firebase

1. Crea un proyecto en [Firebase Console](https://console.firebase.google.com/).
2. Habilita **Cloud Firestore**.
3. Genera una cuenta de servicio (Service Account) con una clave privada en `Configuración > Cuentas de servicio`.
4. Guarda el archivo `.json` como `config/firebase-key.json` (carpeta `config` ignorada por git; la credencial NO debe subirse al repositorio).

> **Importante:** la credencial de servicio nunca debe compartirse ni subirse a git. El `.gitignore` ya excluye `config/` y los archivos `*-firebase-adminsdk-*.json`.

### Reglas de seguridad (Firestore Rules)

El archivo `firestore.rules` contiene las reglas de acceso a Firestore. Para aplicarlas:

1. En Firebase Console entra en **Firestore Database > Reglas**.
2. Pega el contenido de `firestore.rules` y pulsa **Publicar**.

> **Aviso importante de seguridad:** la app se conecta con una **cuenta de servicio** (service account) de `firebase-admin`. Las cuentas de servicio tienen acceso total y **las reglas de Firestore no las bloquean**; si la clave se filtra (p. ej. dentro del `.exe`), cualquiera podría leer/escribir toda la base de datos. Por eso:
> - Nunca subas la clave a git (ya está en `.gitignore`).
> - No compartas el `.exe` fuera del equipo sin cambiar la cuenta de servicio.
> - Para un producto real se recomienda migrar a **Firebase Authentication** con login por correo/contraseña y reglas basadas en el rol del usuario.

### Colección `usuarios`

Cada documento representa un usuario del sistema:

| Campo | Ejemplo |
|-------|---------|
| `usuario` | `admin` |
| `clave` | `admin123` |
| `rol` | `administrador` / `trabajador` |
| `correo` | `admin@empresa.com` |
| `nombre` | `Juan Perez` |
| `fecha` | `2026-09-03` |
| `hora` | `01:36:33` |

## Cómo ejecutar el sistema

Con el venv activado (o usando el intérprete del venv directamente):

```
cd "carpeta-del-proyecto"
venv\Scripts\python.exe primeraventana.py
```

### Credenciales de prueba

- **Administrador**: `admin` / `admin123`
- Un usuario con rol `trabajador` inicia sesión igual pero **no** ve el botón de gestión de usuarios.

## Generar el ejecutable (.exe)

Doble clic en `crear_exe.bat` (o ejecútalo desde la terminal). Produce `dist\SistemaAsistencia.exe`.

> Si la credencial está en `config\firebase-key.json`, el `.exe` la incluye dentro y funciona sin la carpeta `config`. Si no está, la app abre pero no conecta a Firebase.

Alternativa vía CI: el workflow `.github/workflows/build.yml` compila el `.exe` (Windows y Linux) al publicar una rama/tag, usando la clave guardada en el *secret* de GitHub `FIREBASE_KEY`.

## Roles y permisos

- La ventana **Gestión de Usuarios** (crear/modificar/eliminar) solo se muestra al iniciar sesión con rol `administrador`.
- Se impide eliminar al usuario con la sesión activa (integridad de datos).
- Las operaciones CRUD se aplican directo sobre Firestore y mantienen una copia local en `cache_usuarios.json` (este archivo contiene claves; no está versionado).

---
Proyecto académico — Integración de Competencias II.
