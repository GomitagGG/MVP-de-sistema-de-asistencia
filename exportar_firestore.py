import json
import os
from datetime import datetime

from modelos import get_db


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


if __name__ == "__main__":
    main()