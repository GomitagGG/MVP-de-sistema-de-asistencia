"""Limpia las marcaciones y alertas de los días no laborables (feriados).

Los feriados se excluyen de la siembra y de los cálculos de día hábil, pero
si la base fue poblada antes de esa corrección quedan registros de esos días.
Este script elimina las marcaciones y alertas de las fechas en FERIADOS.

Ejecutar una sola vez para dejar la base coherente con el calendario.
"""

import sys

from google.cloud.firestore_v1.base_query import FieldFilter

from modelos import FERIADOS, get_db


def limpiar():
    """Elimina marcaciones y alertas de los feriados definidos.

    @return None: Borra en Firestore los documentos de los días feriados.
    """
    db = get_db()
    for fecha in sorted(FERIADOS):
        n_marc = 0
        n_alertas = 0
        for coleccion in ("marcaciones", "alertas"):
            docs = db.collection(coleccion) \
                .where(filter=FieldFilter("fecha", "==", fecha)).get()
            batch = db.batch()
            contador = 0
            for d in docs:
                batch.delete(d.reference)
                contador += 1
                if contador >= 400:
                    batch.commit()
                    batch = db.batch()
                    contador = 0
            if contador:
                batch.commit()
            if coleccion == "marcaciones":
                n_marc = len(docs)
            else:
                n_alertas = len(docs)
        print(f"{fecha}: {n_marc} marcaciones y {n_alertas} alertas eliminadas")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    limpiar()