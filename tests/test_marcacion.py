from datetime import datetime

import pytest

from modelos import Marcacion

from fake_db import FakeDB


def test_entrada_atrasada_antes_del_limite():
    """Prueba que una entrada antes del límite no se considere tardía.

    @return None: Verifica el caso de una hora marcada antes del umbral.
    """
    m = Marcacion(accion=Marcacion.ENTRADA, hora="09:00:00")
    assert m.es_entrada_atrasada() is False


def test_entrada_atrasada_justo_en_el_limite():
    """Prueba que una entrada justo en el límite tampoco sea retrasada.

    @return None: Verifica el comportamiento en el valor exacto de corte.
    """
    m = Marcacion(accion=Marcacion.ENTRADA, hora="09:30:00")
    assert m.es_entrada_atrasada() is False


def test_entrada_atrasada_despues_del_limite():
    """Prueba que una entrada pasada del límite sea marcada como atrasada.

    @return None: Verifica el caso en que la hora excede el umbral permitido.
    """
    m = Marcacion(accion=Marcacion.ENTRADA, hora="09:31:00")
    assert m.es_entrada_atrasada() is True


def test_salida_anticipada_despues_del_limite():
    """Prueba que una salida después del límite no sea considerada anticipada.

    @return None: Verifica que la salida en horario normal no genere alerta.
    """
    m = Marcacion(accion=Marcacion.SALIDA, hora="17:30:00")
    assert m.es_salida_anticipada() is False


def test_salida_anticipada_antes_del_limite():
    """Prueba que una salida antes del límite sea marcada como anticipada.

    @return None: Verifica la detección de salida temprana.
    """
    m = Marcacion(accion=Marcacion.SALIDA, hora="16:00:00")
    assert m.es_salida_anticipada() is True


def test_salida_no_se_considera_atraso_entrada():
    """Prueba que una salida no se evalúe como atraso de entrada.

    @return None: Verifica que la lógica dependa del tipo de acción.
    """
    m = Marcacion(accion=Marcacion.SALIDA, hora="10:00:00")
    assert m.es_entrada_atrasada() is False


def test_entrada_no_se_considera_salida_anticipada():
    """Prueba que una entrada no se evalúe como salida anticipada.

    @return None: Verifica que la lógica dependa del tipo de acción.
    """
    m = Marcacion(accion=Marcacion.ENTRADA, hora="16:00:00")
    assert m.es_salida_anticipada() is False


def test_ahora_asigna_fecha_y_hora_actual():
    """Prueba que el método ahora asigne la fecha y hora actuales correctamente.

    @return None: Verifica la información del usuario, acción y formato temporal.
    """
    m = Marcacion.ahora("juan", "juan@empresa.cl", Marcacion.ENTRADA)
    assert m.usuario == "juan"
    assert m.correo == "juan@empresa.cl"
    assert m.accion == "entrada"
    assert m.fecha == datetime.now().strftime("%Y-%m-%d")
    assert len(m.hora) == 8


def test_hoy_formato():
    """Prueba que la fecha actual se devuelva en formato ISO del calendario.

    @return None: Verifica el formato de la fecha de hoy.
    """
    assert Marcacion.hoy() == datetime.now().strftime("%Y-%m-%d")


def test_guardar_escribe_campos_correctos():
    """Prueba que guardar una marcación escriba los campos esperados en la base de datos.

    @return None: Verifica cada dato almacenado en la colección de marcaciones.
    """
    db = FakeDB()
    m = Marcacion(usuario="juan", correo="juan@empresa.cl", accion="entrada",
                  fecha="2026-09-07", hora="09:45:00")
    m.guardar(db, atrasado=True, salida_anticipada=False)
    docs = db.collection("marcaciones").get()
    assert len(docs) == 1
    datos = docs[0].to_dict()
    assert datos["usuario"] == "juan"
    assert datos["tipo"] == "entrada"
    assert datos["fecha"] == "2026-09-07"
    assert datos["hora"] == "09:45:00"
    assert datos["atrasado"] is True
    assert datos["salida_anticipada"] is False


def test_buscar_por_usuario_y_accion():
    """Prueba que la búsqueda filtre por usuario y acción en la fecha indicada.

    @return None: Verifica que el resultado devuelto corresponda al usuario correcto.
    """
    db = FakeDB()
    db.collection("marcaciones").add({
        "usuario": "juan", "tipo": "entrada", "fecha": "2026-09-07",
        "hora": "09:00:00",
    })
    db.collection("marcaciones").add({
        "usuario": "ana", "tipo": "entrada", "fecha": "2026-09-07",
        "hora": "09:10:00",
    })
    resultado = Marcacion.buscar(db, "juan", fecha="2026-09-07", accion="entrada")
    assert resultado is not None
    assert resultado["usuario"] == "juan"


def test_buscar_filtra_por_tipo():
    """Prueba que la búsqueda filtre por tipo de acción, como entrada o salida.

    @return None: Verifica que el documento devuelto corresponda al tipo buscado.
    """
    db = FakeDB()
    db.collection("marcaciones").add({
        "usuario": "juan", "tipo": "entrada", "fecha": "2026-09-07",
        "hora": "09:00:00",
    })
    db.collection("marcaciones").add({
        "usuario": "juan", "tipo": "salida", "fecha": "2026-09-07",
        "hora": "18:00:00",
    })
    resultado = Marcacion.buscar(db, "juan", fecha="2026-09-07", accion="salida")
    assert resultado is not None
    assert resultado["tipo"] == "salida"


def test_buscar_no_encuentra():
    """Prueba que la búsqueda devuelva None cuando no existe una coincidencia.

    @return None: Verifica el caso sin resultados para el usuario solicitado.
    """
    db = FakeDB()
    db.collection("marcaciones").add({
        "usuario": "juan", "tipo": "entrada", "fecha": "2026-09-07",
        "hora": "09:00:00",
    })
    assert Marcacion.buscar(db, "pedro", fecha="2026-09-07") is None