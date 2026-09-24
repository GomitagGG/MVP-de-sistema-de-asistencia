<<<<<<< HEAD
import json
import os
=======
"""Exporta la base de datos de Firestore a un archivo JSON en el Escritorio.

Lee todas las colecciones existentes (usuarios, marcaciones, alertas,
login_log, config) y las guarda en un único archivo .json con los timestamps
serializados en formato ISO. Es de solo lectura: no modifica la base de datos.

Uso:
    python exportar_firestore.py
"""

import json
import os
import sys
>>>>>>> 850796b75ae8f9df437d584c4dc28117d582214b
from datetime import datetime

from modelos import get_db


<<<<<<< HEAD
def serializar(valor):
    """Convierte tipos especiales de Firestore a tipos serializables en JSON."""
    if isinstance(valor, datetime):
        return {"_datetime": valor.isoformat(timespec="seconds")}
    if hasattr(valor, "path") and hasattr(valor, "id") and hasattr(valor, "parent"):
        return {"_ref": valor.path}
    if hasattr(valor, "latitude") and hasattr(valor, "longitude"):
        return {"_geo": {"lat": valor.latitude, "lng": valor.longitude}}
    if isinstance(valor, list):
        return [serializar(v) for v in valor]
    if isinstance(valor, dict):
        return {k: serializar(v) for k, v in valor.items()}
    if hasattr(valor, "bytes") and callable(valor.bytes):
        return {"_bytes": valor.bytes().decode("utf-8", errors="replace")}
    if isinstance(valor, bytes):
        return {"_bytes": valor.decode("utf-8", errors="replace")}
    return valor


def exportar_coleccion(col):
    """Exporta una coleccion completa, incluyendo subcolecciones."""
    docs = []
    snapshot = col.get()
    for doc in snapshot:
        datos = serializar(doc.to_dict())
        entrada = {"id": doc.id, **datos}
        subcols = list(doc.reference.collections())
        for subcol in subcols:
            entrada["_" + subcol.id] = exportar_coleccion(subcol)
        docs.append(entrada)
    return docs


def main():
    db = get_db()
    colecciones = list(db.collections())

    if not colecciones:
        print("No hay colecciones en la base de datos.")
        return

    resultado = {}
    for col in colecciones:
        print(f"Exportando '{col.id}' ...")
        resultado[col.id] = exportar_coleccion(col)
        print(f"  -> {len(resultado[col.id])} documentos")

    nombre_salida = f"firestore-export-{datetime.now():%Y%m%d-%H%M%S}.json"
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_salida)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nListo: {ruta}")
=======
COLECCIONES_FIJAS = ["usuarios", "marcaciones", "alertas", "login_log", "config"]


def _serializar(valor):
    """Convierte valores de Firestore a tipos serializables en JSON.

    @param valor: Valor proveniente de un documento de Firestore.
    @return obj: Valor apto para json.dump (timestamps a string ISO).
    """
    if isinstance(valor, (datetime,)):
        return valor.isoformat()
    if hasattr(valor, "isoformat"):
        try:
            return valor.isoformat()
        except Exception:
            return str(valor)
    return valor


def _colectar_colecciones(db):
    """Devuelve las colecciones a exportar (detectadas o por defecto).

    @param db: Cliente de Firestore.
    @return list[str]: Nombres de las colecciones existentes a exportar.
    """
    try:
        detectadas = [c.id for c in db.collections()]
        if detectadas:
            return sorted(set(detectadas))
    except Exception:
        pass
    return COLECCIONES_FIJAS


def _leer_coleccion(db, nombre):
    """Lee los documentos completos de una colección.

    @param db: Cliente de Firestore.
    @param nombre: Nombre de la colección a exportar.
    @return list: Documentos con sus datos serializados.
    """
    docs = db.collection(nombre).get()
    return [dict((k, _serializar(v)) for k, v in d.to_dict().items()) for d in docs]


def exportar(db, ruta):
    """Exporta todas las colecciones a un archivo JSON.

    @param db: Cliente de Firestore.
    @param ruta: Ruta absoluta del archivo .json a escribir.
    @return dict: Resumen con la cantidad de documentos por colección.
    """
    colecciones = _colectar_colecciones(db)
    datos = {"exportado": datetime.now().isoformat(), "colecciones": {}}
    resumen = {}
    for nombre in colecciones:
        docs = _leer_coleccion(db, nombre)
        datos["colecciones"][nombre] = docs
        resumen[nombre] = len(docs)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return resumen


def main():
    """Exporta la base de datos a un JSON en el Escritorio y muestra el resumen.

    @return None: Escribe el archivo e imprime el conteo por colección.
    """
    db = get_db()

    escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta = os.path.join(escritorio, f"export_firestore_{fecha}.json")

    resumen = exportar(db, ruta)

    print(f"Exportación completada: {ruta}")
    print(f"Tamaño del archivo: {os.path.getsize(ruta):,} bytes")
    for nombre, total in resumen.items():
        print(f"  - {nombre}: {total} documentos")
>>>>>>> 850796b75ae8f9df437d584c4dc28117d582214b


if __name__ == "__main__":
    main()