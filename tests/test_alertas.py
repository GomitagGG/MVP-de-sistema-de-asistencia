import pytest

from modelos import Alerta

from fake_db import FakeDB


@pytest.fixture
def db():
    return FakeDB()


def test_crear_alerta(db):
    alerta = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07", "09:45:00")
    assert alerta is not None
    assert alerta._id is not None
    doc = db.collection("alertas").data[alerta._id]
    assert doc["tipo"] == "atraso"
    assert doc["usuario"] == "juan"
    assert doc["fecha"] == "2026-09-07"
    assert doc["hora"] == "09:45:00"
    assert doc["estado"] == "pendiente"


def test_crear_alerta_duplicada_no_se_crea(db):
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    segunda = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    assert segunda is None
    assert len(db.collection("alertas").data) == 1


def test_crear_alerta_misma_fecha_tipo_diferente(db):
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    alerta = Alerta.crear(db, Alerta.TIPO_SALIDA_ANTICIPADA, "juan", "2026-09-07")
    assert alerta is not None
    assert len(db.collection("alertas").data) == 2


def test_crear_alerta_mismo_tipo_usuario_distinto(db):
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    alerta = Alerta.crear(db, Alerta.TIPO_ATRASO, "ana", "2026-09-07")
    assert alerta is not None
    assert len(db.collection("alertas").data) == 2


def test_marcar_leida(db):
    alerta = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    Alerta.marcar_leida(db, alerta._id)
    assert db.collection("alertas").data[alerta._id]["estado"] == "leida"


def test_listar_estado_pendiente(db):
    a1 = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    Alerta.crear(db, Alerta.TIPO_INASISTENCIA, "ana", "2026-09-07")
    Alerta.marcar_leida(db, a1._id)
    pendientes = Alerta.listar(db, estado=Alerta.ESTADO_PENDIENTE)
    assert len(pendientes) == 1
    assert pendientes[0]["usuario"] == "ana"


def test_listar_todas(db):
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    Alerta.crear(db, Alerta.TIPO_SALIDA_ANTICIPADA, "ana", "2026-09-06")
    alertas = Alerta.listar(db)
    assert len(alertas) == 2


def test_listar_filtro_fecha(db):
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-05")
    Alerta.crear(db, Alerta.TIPO_INASISTENCIA, "ana", "2026-09-08")
    alertas = Alerta.listar(db, fecha_inicio="2026-09-01", fecha_fin="2026-09-07")
    assert len(alertas) == 1
    assert alertas[0]["tipo"] == "atraso"


def test_listar_ordenado_por_fecha(db):
    Alerta.crear(db, Alerta.TIPO_INASISTENCIA, "ana", "2026-09-09")
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    alertas = Alerta.listar(db)
    fechas = [a["fecha"] for a in alertas]
    assert fechas == sorted(fechas)