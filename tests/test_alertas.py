import pytest

from modelos import Alerta

from fake_db import FakeDB


@pytest.fixture
def db():
    """Crea una base de datos falsa para las pruebas relacionadas con alertas.

    @return FakeDB: Instancia en memoria utilizada por las pruebas de alertas.
    """
    return FakeDB()


def test_crear_alerta(db):
    """Verifica que se cree una alerta válida con los valores esperados.

    @param db: Instancia de FakeDB usada como almacén de datos.
    @return None: La prueba valida los campos de la alerta y el registro persistido.
    """
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
    """Comprueba que no se creen alertas duplicadas para el mismo usuario y fecha.

    @param db: Instancia de FakeDB usada para almacenar los registros de alertas.
    @return None: La prueba valida que el segundo intento de creación es rechazado.
    """
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    segunda = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    assert segunda is None
    assert len(db.collection("alertas").data) == 1


def test_crear_alerta_misma_fecha_tipo_diferente(db):
    """Confirma que se permiten distintos tipos de alerta en la misma fecha.

    @param db: Instancia de FakeDB usada para guardar los datos de alertas.
    @return None: La prueba valida que ambos tipos de alerta se conservan.
    """
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    alerta = Alerta.crear(db, Alerta.TIPO_SALIDA_ANTICIPADA, "juan", "2026-09-07")
    assert alerta is not None
    assert len(db.collection("alertas").data) == 2


def test_crear_alerta_mismo_tipo_usuario_distinto(db):
    """Comprueba que el mismo tipo de alerta puede crearse para distintos usuarios.

    @param db: Instancia de FakeDB que contiene la colección de alertas.
    @return None: La prueba verifica que la base de datos tiene dos alertas distintas.
    """
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    alerta = Alerta.crear(db, Alerta.TIPO_ATRASO, "ana", "2026-09-07")
    assert alerta is not None
    assert len(db.collection("alertas").data) == 2


def test_marcar_leida(db):
    """Verifica que el estado de la alerta cambia de pendiente a leída al marcarla.

    @param db: Instancia de FakeDB que proporciona el registro de alertas.
    @return None: La prueba confirma que el estado persistido se actualiza a leída.
    """
    alerta = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    Alerta.marcar_leida(db, alerta._id)
    assert db.collection("alertas").data[alerta._id]["estado"] == "leida"


def test_listar_estado_pendiente(db):
    """Filtra la lista de alertas para mostrar solo las que siguen pendientes.

    @param db: Instancia de FakeDB con alertas pendientes y leídas.
    @return None: La prueba comprueba que solo se devuelven las alertas pendientes.
    """
    a1 = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    Alerta.crear(db, Alerta.TIPO_INASISTENCIA, "ana", "2026-09-07")
    Alerta.marcar_leida(db, a1._id)
    pendientes = Alerta.listar(db, estado=Alerta.ESTADO_PENDIENTE)
    assert len(pendientes) == 1
    assert pendientes[0]["usuario"] == "ana"


def test_listar_todas(db):
    """Devuelve la lista completa de registros de alertas almacenados en la base de datos.

    @param db: Instancia de FakeDB cuyos registros se están listando.
    @return None: La prueba asegura que ambas alertas quedan incluidas en el resultado.
    """
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    Alerta.crear(db, Alerta.TIPO_SALIDA_ANTICIPADA, "ana", "2026-09-06")
    alertas = Alerta.listar(db)
    assert len(alertas) == 2


def test_listar_filtro_fecha(db):
    """Filtra alertas por un rango de fechas y conserva solo el registro coincidente.

    @param db: Instancia de FakeDB con alertas en varias fechas.
    @return None: La prueba valida el comportamiento de filtrado por rango de fechas.
    """
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-05")
    Alerta.crear(db, Alerta.TIPO_INASISTENCIA, "ana", "2026-09-08")
    alertas = Alerta.listar(db, fecha_inicio="2026-09-01", fecha_fin="2026-09-07")
    assert len(alertas) == 1
    assert alertas[0]["tipo"] == "atraso"


def test_listar_ordenado_por_fecha(db):
    """Asegura que la lista de alertas esté ordenada en secuencia cronológica por fecha.

    @param db: Instancia de FakeDB utilizada para crear alertas con fechas mezcladas.
    @return None: La prueba comprueba que el resultado final queda ordenado por fecha.
    """
    Alerta.crear(db, Alerta.TIPO_INASISTENCIA, "ana", "2026-09-09")
    Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07")
    alertas = Alerta.listar(db)
    fechas = [a["fecha"] for a in alertas]
    assert fechas == sorted(fechas)