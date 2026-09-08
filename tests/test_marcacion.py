from datetime import datetime

import pytest

from modelos import Marcacion

from fake_db import FakeDB


def test_entrada_atrasada_antes_del_limite():
    m = Marcacion(accion=Marcacion.ENTRADA, hora="09:00:00")
    assert m.es_entrada_atrasada() is False


def test_entrada_atrasada_justo_en_el_limite():
    m = Marcacion(accion=Marcacion.ENTRADA, hora="09:30:00")
    assert m.es_entrada_atrasada() is False


def test_entrada_atrasada_despues_del_limite():
    m = Marcacion(accion=Marcacion.ENTRADA, hora="09:31:00")
    assert m.es_entrada_atrasada() is True


def test_salida_anticipada_despues_del_limite():
    m = Marcacion(accion=Marcacion.SALIDA, hora="17:30:00")
    assert m.es_salida_anticipada() is False


def test_salida_anticipada_antes_del_limite():
    m = Marcacion(accion=Marcacion.SALIDA, hora="16:00:00")
    assert m.es_salida_anticipada() is True


def test_salida_no_se_considera_atraso_entrada():
    m = Marcacion(accion=Marcacion.SALIDA, hora="10:00:00")
    assert m.es_entrada_atrasada() is False


def test_entrada_no_se_considera_salida_anticipada():
    m = Marcacion(accion=Marcacion.ENTRADA, hora="16:00:00")
    assert m.es_salida_anticipada() is False


def test_ahora_asigna_fecha_y_hora_actual():
    m = Marcacion.ahora("juan", "juan@empresa.cl", Marcacion.ENTRADA)
    assert m.usuario == "juan"
    assert m.correo == "juan@empresa.cl"
    assert m.accion == "entrada"
    assert m.fecha == datetime.now().strftime("%Y-%m-%d")
    assert len(m.hora) == 8


def test_hoy_formato():
    assert Marcacion.hoy() == datetime.now().strftime("%Y-%m-%d")


def test_guardar_escribe_campos_correctos():
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
    db = FakeDB()
    db.collection("marcaciones").add({
        "usuario": "juan", "tipo": "entrada", "fecha": "2026-09-07",
        "hora": "09:00:00",
    })
    assert Marcacion.buscar(db, "pedro", fecha="2026-09-07") is None