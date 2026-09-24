"""Semilla de marcaciones para el dia de hoy.

Agrega (o sobrescribe) las marcaciones de entrada/salida del dia actual y sus
alertas, SIN limpiar el resto de la base (no toca usuarios, config, ni dias
anteriores). Sirve para que los reportes del dia no muestren a todos como
ausentes.

Uso:
    python semilla_hoy.py
"""

import os
import sys
from datetime import datetime

from google.cloud.firestore_v1.base_query import FieldFilter

from semilla import get_db, TRABAJADORES, HORA_ENTRADA_LIMITE, HORA_SALIDA_LIMITE


AUSENTES = ["victor"]

ENTRADAS = {
    "juan":       "09:03:00",
    "maria":      "09:15:00",
    "ana":        "09:24:00",
    "lucia":      "09:07:00",
    "diego":      "09:01:00",
    "sofia":      "09:20:00",
    "leonardo":   "09:12:00",
    "marta":      "09:28:00",
    "olivia":     "09:05:00",
    "pablo":      "09:22:00",
    "rosa":       "09:17:00",
    "samuel":     "09:09:00",
    "carlos":     "09:41:00",
    "pedro":      "09:47:00",
    "hector":     "10:05:00",
    "valentina":  "09:36:00",
    "camila":     "09:52:00",
    "isabel":     "09:58:00",
    "jorge":      "09:44:00",
    "karen":      "10:12:00",
    "nicolas":    "09:31:00",
    "andres":     "09:08:00",
    "fernando":   "09:11:00",
    "tatiana":    "09:26:00",
}

SALIDAS = {
    "juan":       "17:45:00",
    "maria":      "18:10:00",
    "ana":        "17:32:00",
    "lucia":      "16:15:00",
    "diego":      "17:50:00",
    "sofia":      "18:20:00",
    "leonardo":   "17:35:00",
    "marta":      "17:40:00",
    "olivia":     "18:02:00",
    "pablo":      "17:55:00",
    "rosa":       "17:37:00",
    "samuel":     "18:00:00",
    "carlos":     "16:50:00",
    "pedro":      "17:33:00",
    "hector":     "18:15:00",
    "valentina":  "18:05:00",
    "camila":     "17:38:00",
    "isabel":     "17:42:00",
    "jorge":      "16:20:00",
    "karen":      "17:31:00",
    "nicolas":    "17:12:00",
    "andres":     "17:58:00",
    "fernando":   "18:08:00",
    "tatiana":    "17:41:00",
}


def _correo(usr):
    """Convierte un nombre de usuario en su correo corporativo.

    @param usr: Nombre de usuario del trabajador.
    @return str: Correo electrónico de la forma usr@empresa.com.
    """
    return f"{usr}@empresa.com"


def _crear_marcaciones(db, fecha):
    """Crea las marcaciones de entrada y salida del día en Firestore.

    @param db: Cliente de Firestore.
    @param fecha: Fecha (YYYY-MM-DD) de las marcaciones a crear.
    @return int: Cantidad de marcaciones de entrada y salida escritas.
    """
    n = 0
    batch = db.batch()
    for usr, hora_ent in ENTRADAS.items():
        atrasado = hora_ent[:5] > HORA_ENTRADA_LIMITE
        batch.set(
            db.collection("marcaciones").document(f"{usr}_{fecha}_entrada"),
            {
                "usuario": usr,
                "correo": _correo(usr),
                "tipo": "entrada",
                "fecha": fecha,
                "hora": hora_ent,
                "atrasado": atrasado,
                "salida_anticipada": False,
            })
        n += 1
        hora_sal = SALIDAS[usr]
        salida_ant = hora_sal[:5] < HORA_SALIDA_LIMITE
        batch.set(
            db.collection("marcaciones").document(f"{usr}_{fecha}_salida"),
            {
                "usuario": usr,
                "correo": _correo(usr),
                "tipo": "salida",
                "fecha": fecha,
                "hora": hora_sal,
                "atrasado": False,
                "salida_anticipada": salida_ant,
            })
        n += 1
    for usr in AUSENTES:
        for tipo in ("entrada", "salida"):
            ref = db.collection("marcaciones").document(f"{usr}_{fecha}_{tipo}")
            batch.delete(ref)
    batch.commit()
    return n


def _crear_alertas(db, fecha):
    """Crea las alertas (atraso, salida anticipada, inasistencia) del día.

    @param db: Cliente de Firestore.
    @param fecha: Fecha (YYYY-MM-DD) de las alertas a crear.
    @return int: Cantidad de alertas nuevas creadas.
    """
    batch = db.batch()
    n = 0
    existentes = set()
    docs = db.collection("alertas") \
        .where(filter=FieldFilter("fecha", "==", fecha)).get()
    for d in docs:
        datos = d.to_dict()
        existentes.add((datos.get("tipo"), datos.get("usuario"), fecha))

    def _agregar(tipo, usr, hora):
        """Agrega una alerta al lote si no existe otra igual en la fecha.

        @param tipo: Tipo de alerta (atraso, salida_anticipada, inasistencia).
        @param usr: Usuario al que pertenece la alerta.
        @param hora: Hora del evento asociado (vacío para inasistencia).
        @return None: Suma el documento al batch de escritura.
        """
        nonlocal n
        if (tipo, usr, fecha) in existentes:
            return
        clave = f"alerta_{tipo}_{usr}_{fecha}"
        batch.set(db.collection("alertas").document(clave), {
            "tipo": tipo,
            "usuario": usr,
            "fecha": fecha,
            "hora": hora,
            "estado": "pendiente",
            "timestamp": datetime.now(),
        })
        n += 1

    for usr, hora_ent in ENTRADAS.items():
        if hora_ent[:5] > HORA_ENTRADA_LIMITE:
            _agregar("atraso", usr, hora_ent[:5])
    for usr, hora_sal in SALIDAS.items():
        if hora_sal[:5] < HORA_SALIDA_LIMITE:
            _agregar("salida_anticipada", usr, hora_sal[:5])
    for usr in AUSENTES:
        _agregar("inasistencia", usr, "")
    if n:
        batch.commit()
    return n


def main():
    """Siembra las marcaciones y alertas del día actual en Firestore.

    @return None: Carga los datos de hoy e imprime un resumen de resultados.
    """
    db = get_db()
    fecha = datetime.now().strftime("%Y-%m-%d")

    n_marc = _crear_marcaciones(db, fecha)
    n_alertas = _crear_alertas(db, fecha)

    presentes = len(ENTRADAS)
    atrasados = sum(1 for h in ENTRADAS.values() if h[:5] > HORA_ENTRADA_LIMITE)
    anticipadas = sum(1 for h in SALIDAS.values() if h[:5] < HORA_SALIDA_LIMITE)

    print(f"Marcaciones de hoy ({fecha}) cargadas: {n_marc}")
    print(f"  - Presentes: {presentes}")
    print(f"  - Atrasados: {atrasados}")
    print(f"  - Salidas anticipadas: {anticipadas}")
    print(f"  - Ausentes: {len(AUSENTES)} -> {', '.join(AUSENTES)}")
    print(f"Alertas creadas: {n_alertas}")

    docs_hoy = db.collection("marcaciones") \
        .where(filter=FieldFilter("fecha", "==", fecha)).get()
    print(f"Total en Firestore para hoy: {len(docs_hoy)}")


if __name__ == "__main__":
    main()