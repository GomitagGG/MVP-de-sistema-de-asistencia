import os
import sys
import random
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter


def ruta_relativa(ruta):
    """Resuelve la ruta absoluta de un recurso dentro del proyecto.

    @param ruta: Ruta relativa del archivo o recurso a resolver.
    @return str: Ruta absoluta completa para acceder al recurso.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ruta)


def get_db():
    """Obtiene la instancia de Firestore inicializada con la configuración del proyecto.

    @return firestore.Client: Cliente de Firestore listo para operar.
    """
    if not firebase_admin._apps:
        key_file = "config/firebase-key.json"
        if not os.path.exists(ruta_relativa(key_file)):
            key_file = "config/registro-asistencia-bfe64-firebase-adminsdk-fbsvc-236f010224.json"
        cred = credentials.Certificate(ruta_relativa(key_file))
        firebase_admin.initialize_app(cred)
    return firestore.client()


HORA_ENTRADA_LIMITE = "09:30"
HORA_SALIDA_LIMITE = "17:30"

# 25 trabajadores (el admin se crea aparte y NO se cuenta en asistencia)
TRABAJADORES = [
    ("juan",       "Juan",       "Perez"),
    ("maria",      "Maria",      "Garcia"),
    ("carlos",     "Carlos",     "Lopez"),
    ("ana",        "Ana",        "Martinez"),
    ("pedro",      "Pedro",      "Sanchez"),
    ("lucia",      "Lucia",      "Ramirez"),
    ("hector",     "Hector",     "Torres"),
    ("sofia",      "Sofia",      "Flores"),
    ("diego",      "Diego",      "Morales"),
    ("valentina",  "Valentina",  "Herrera"),
    ("andres",     "Andres",     "Vega"),
    ("camila",     "Camila",     "Reyes"),
    ("fernando",   "Fernando",   "Castillo"),
    ("isabel",     "Isabel",     "Rojas"),
    ("jorge",      "Jorge",      "Medina"),
    ("karen",      "Karen",      "Aguilar"),
    ("leonardo",   "Leonardo",   "Gutierrez"),
    ("marta",      "Marta",      "Ruiz"),
    ("nicolas",    "Nicolas",    "Salazar"),
    ("olivia",     "Olivia",     "Castro"),
    ("pablo",      "Pablo",      "Ortiz"),
    ("rosa",       "Rosa",       "Nunez"),
    ("samuel",     "Samuel",     "Jimenez"),
    ("tatiana",    "Tatiana",    "Blanco"),
    ("victor",     "Victor",     "Campos"),
]


def crear_config(db):
    """Crea la configuración base de la empresa en Firestore.

    @param db: Cliente de Firestore donde se almacenará la configuración.
    @return None: Guarda la información de la empresa en la colección config.
    """
    db.collection("config").document("empresa").set({
        "nombre": "Empresa Qu\u00edmica",
        "hora_entrada": HORA_ENTRADA_LIMITE,
        "hora_salida": HORA_SALIDA_LIMITE,
    })


def crear_usuarios(db):
    """Genera los usuarios administradores y trabajadores iniciales del sistema.

    @param db: Cliente de Firestore donde se crearán los usuarios.
    @return None: Inserta los documentos de usuario en la colección usuarios.
    """
    batch = db.batch()
    batch.set(db.collection("usuarios").document("admin"), {
        "usuario": "admin",
        "clave": "admin123",
        "rol": "administrador",
        "correo": "admin@empresa.com",
        "nombre": "Administrador",
    })
    for usr, nombre, apellido in TRABAJADORES:
        batch.set(db.collection("usuarios").document(usr), {
            "usuario": usr,
            "clave": "123456",
            "rol": "trabajador",
            "correo": f"{usr}@empresa.com",
            "nombre": f"{nombre} {apellido}",
        })
    batch.commit()


def dias_desde_inicio_mes():
    """Devuelve la lista de días hábiles desde el inicio del mes hasta hoy.

    @return list[datetime]: Fechas laborales dentro del mes actual.
    """
    dias = []
    hoy = datetime.now()
    primero = hoy.replace(day=1)
    d = primero
    while d <= hoy:
        if d.weekday() < 5:
            dias.append(d)
        d += timedelta(days=1)
    return dias


def limpiar_colecciones(db):
    """Borra los datos de las colecciones principales antes de sembrar la base.

    @param db: Cliente de Firestore a limpiar.
    @return None: Elimina los documentos de usuarios, marcaciones, alertas y login_log.
    """
    for coleccion in ("usuarios", "marcaciones", "alertas", "login_log"):
        n = 0
        batch = db.batch()
        docs = db.collection(coleccion).list_documents()
        for doc in docs:
            batch.delete(doc)
            n += 1
            if n % 400 == 0:
                batch.commit()
                batch = db.batch()
        if n % 400 != 0:
            batch.commit()
        print(f"  - Coleccion '{coleccion}' limpiada ({n})")


def hora_entrada_random():
    """Genera una hora de entrada aleatoria para una jornada laboral.

    @return str: Hora de entrada en formato HH:MM:SS.
    """
    if random.random() < 0.65:
        return f"09:{random.randint(0, 29):02d}:00"
    if random.random() < 0.7:
        return f"09:{random.randint(31, 59):02d}:00"
    return f"10:{random.randint(0, 15):02d}:00"


def hora_salida_random():
    """Genera una hora de salida aleatoria para una jornada laboral.

    @return str: Hora de salida en formato HH:MM:SS.
    """
    if random.random() < 0.3:
        return f"16:{random.randint(0, 59):02d}:00"
    if random.random() < 0.5:
        return f"17:{random.randint(30, 59):02d}:00"
    return f"18:{random.randint(0, 20):02d}:00"


def crear_marcaciones(db):
    """Crea una base de marcaciones aleatorias para los trabajadores.

    @param db: Cliente de Firestore donde se insertarán las marcaciones.
    @return int: Cantidad total de marcaciones creadas.
    """
    total = 0
    dias = dias_desde_inicio_mes()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    for d in dias:
        batch = db.batch()
        contador = 0
        fecha = d.strftime("%Y-%m-%d")
        es_hoy = fecha == fecha_hoy

        # D\u00edas con asistencia completa (para marcar verde en calendario)
        if es_hoy:
            presentes = TRABAJADORES[:]
        elif random.random() < 0.4:
            presentes = TRABAJADORES[:]
        else:
            presentes = random.sample(TRABAJADORES, k=random.randint(18, 24))

        for usr, _n, _a in presentes:
            entry_h = hora_entrada_random()
            if es_hoy:
                entry_h = f"09:0{random.randint(1, 9)}:{random.randint(10, 59):02d}"
                entry_h = f"09:{random.randint(10, 59):02d}:00"
            atrasado = entry_h[:5] > HORA_ENTRADA_LIMITE
            batch.set(db.collection("marcaciones").document(f"{usr}_{fecha}_entrada"), {
                "usuario": usr,
                "correo": f"{usr}@empresa.com",
                "tipo": "entrada",
                "fecha": fecha,
                "hora": entry_h,
                "atrasado": atrasado,
                "salida_anticipada": False,
            })
            total += 1
            contador += 1

            if es_hoy or random.random() < 0.9:
                exit_h = hora_salida_random()
                if es_hoy:
                    exit_h = f"18:{random.randint(0, 20):02d}:00"
                salida_ant = exit_h[:5] < HORA_SALIDA_LIMITE
                batch.set(db.collection("marcaciones").document(f"{usr}_{fecha}_salida"), {
                    "usuario": usr,
                    "correo": f"{usr}@empresa.com",
                    "tipo": "salida",
                    "fecha": fecha,
                    "hora": exit_h,
                    "atrasado": False,
                    "salida_anticipada": salida_ant,
                })
                total += 1
                contador += 1

            if contador >= 400:
                batch.commit()
                batch = db.batch()
                contador = 0
        if contador:
            batch.commit()
    return total


def crear_logins(db):
    """Crea registros de logins aleatorios para simular actividad del sistema.

    @param db: Cliente de Firestore donde se registrarán los logins.
    @return int: Cantidad total de registros de acceso creados.
    """
    total = 0
    for d in dias_desde_inicio_mes():
        batch = db.batch()
        contador = 0
        n = random.randint(2, 6)
        for i in range(n):
            usr = random.choice([u[0] for u in TRABAJADORES] + ["admin"])
            batch.set(db.collection("login_log").document(f"{usr}_{d.strftime('%Y-%m-%d')}_{i}"), {
                "usuario": usr,
                "correo": f"{usr}@empresa.com",
                "fecha": d.strftime("%Y-%m-%d"),
                "hora": f"{random.randint(7, 9):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
                "resultado": random.choice(["exitoso", "exitoso", "exitoso", "fallido"]),
            })
            total += 1
            contador += 1
            if contador >= 400:
                batch.commit()
                batch = db.batch()
                contador = 0
        if contador:
            batch.commit()
    return total


def main():
    """Función principal que sembrará la base de datos con usuarios, marcaciones y logs.

    @return None: Ejecuta la carga inicial de datos para pruebas y demo.
    """
    db = get_db()
    print("Limpiando datos anteriores...")
    limpiar_colecciones(db)
    crear_config(db)
    crear_usuarios(db)
    n_marc = crear_marcaciones(db)
    n_log = crear_logins(db)
    print(f"\nSemilla cargada correctamente.")
    print(f"  - {len(TRABAJADORES) + 1} usuarios (1 admin + {len(TRABAJADORES)} trabajadores)")
    print(f"  - {n_marc} marcaciones desde el 1 del mes hasta hoy")
    print(f"  - {n_log} logins")
    print(f"  - Admin: admin / admin123")
    print(f"  - Trabajador de ejemplo: juan / 123456")

    hoy = datetime.now().strftime("%Y-%m-%d")
    docs_hoy = db.collection("marcaciones") \
        .where(filter=FieldFilter("fecha", "==", hoy)).get()
    print(f"  - Marcaciones de hoy ({hoy}): {len(docs_hoy)}")


if __name__ == "__main__":
    main()