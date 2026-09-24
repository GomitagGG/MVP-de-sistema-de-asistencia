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
from datetime import datetime

from modelos import get_db


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


if __name__ == "__main__":
    main()