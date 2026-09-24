"""Limpia las alertas de inasistencia que son falsos positivos.

Los falsos positivos se generaron cuando la app arrancaba o el polling
regresaba sin datos de marcaciones y se creaba una alerta de inasistencia
para CADA trabajador. Esta limpieza borra las alertas de inasistencia
de los trabajadores que SÍ tienen marcación en esa misma fecha.

Ejecutar una vez cuando la cuota de Firestore esté disponible.
"""

import sys

from datetime import datetime

from google.cloud.firestore_v1.base_query import FieldFilter

from modelos import Alerta, get_db


def limpiar():
    """Elimina las alertas de inasistencia de trabajadores con marcación.

    @return None: Borra en Firestore las inasistencias falsas por fecha.
    """
    db = get_db()
    fechas = ("2026-09-22", "2026-09-23", datetime.now().strftime("%Y-%m-%d"))
    for hoy in fechas:
        marcadas = {d.to_dict().get("usuario")
                    for d in db.collection("marcaciones")
                    .where(filter=FieldFilter("fecha", "==", hoy)).get()}
        candidatas = db.collection("alertas") \
            .where(filter=FieldFilter("fecha", "==", hoy)).get()
        a_eliminar = []
        for d in candidatas:
            datos = d.to_dict()
            if datos.get("tipo") != Alerta.TIPO_INASISTENCIA:
                continue
            if datos.get("usuario") not in marcadas:
                continue
            a_eliminar.append(d.reference)
        for ref in a_eliminar:
            ref.delete()
        print(f"{hoy}: {len(marcadas)} con marcacion, "
              f"{len(a_eliminar)} alertas falsas eliminadas")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    limpiar()