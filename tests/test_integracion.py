from modelos import Alerta, Marcacion

from fake_db import FakeDB


def test_flujo_entrada_atrasada_genera_alerta():
    db = FakeDB()
    m = Marcacion(usuario="juan", correo="j@e.cl", accion="entrada",
                  fecha="2026-09-07", hora="09:45:00")
    atrasado = m.es_entrada_atrasada()
    m.guardar(db, atrasado=atrasado, salida_anticipada=False)

    if atrasado:
        Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", m.fecha, m.hora)

    alertas = Alerta.listar(db)
    assert len(alertas) == 1
    assert alertas[0]["tipo"] == "atraso"
    assert alertas[0]["usuario"] == "juan"
    assert alertas[0]["fecha"] == "2026-09-07"
    assert alertas[0]["estado"] == "pendiente"


def test_flujo_entrada_puntual_no_genera_alerta():
    db = FakeDB()
    m = Marcacion(usuario="juan", accion="entrada",
                  fecha="2026-09-07", hora="09:15:00")
    atrasado = m.es_entrada_atrasada()
    m.guardar(db, atrasado=atrasado, salida_anticipada=False)

    if atrasado:
        Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", m.fecha, m.hora)

    assert len(Alerta.listar(db)) == 0


def test_flujo_salida_anticipada_genera_alerta():
    db = FakeDB()
    m = Marcacion(usuario="ana", accion="salida",
                  fecha="2026-09-07", hora="16:00:00")
    salida_anticipada = m.es_salida_anticipada()
    m.guardar(db, atrasado=False, salida_anticipada=salida_anticipada)

    if salida_anticipada:
        Alerta.crear(db, Alerta.TIPO_SALIDA_ANTICIPADA, "ana", m.fecha, m.hora)

    alertas = Alerta.listar(db)
    assert len(alertas) == 1
    assert alertas[0]["tipo"] == "salida_anticipada"


def test_flujo_mismo_dia_no_duplica_alerta():
    db = FakeDB()
    for _ in range(3):
        m = Marcacion(usuario="juan", accion="entrada",
                      fecha="2026-09-07", hora="10:00:00")
        atrasado = m.es_entrada_atrasada()
        m.guardar(db, atrasado=atrasado, salida_anticipada=False)
        if atrasado:
            Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", m.fecha, m.hora)
    assert len(Alerta.listar(db)) == 1


def test_flujo_inasistencia_genera_alerta():
    db = FakeDB()
    db.collection("usuarios").add({
        "usuario": "pedro", "correo": "pedro@e.cl",
        "clave": "123", "rol": "trabajador", "nombre": "Pedro",
    })
    usuarios = [u.to_dict() for u in db.collection("usuarios").get()]

    ausentes = {u["usuario"] for u in usuarios
                if u["usuario"] not in {"juan"}}
    for u in ausentes:
        Alerta.crear(db, Alerta.TIPO_INASISTENCIA, u, "2026-09-07")

    alertas = Alerta.listar(db)
    assert len(alertas) == 1
    assert alertas[0]["tipo"] == "inasistencia"
    assert alertas[0]["usuario"] == "pedro"


def test_flujo_alertas_marcadas_leidas_desaparecen_de_pendientes():
    db = FakeDB()
    a = Alerta.crear(db, Alerta.TIPO_ATRASO, "juan", "2026-09-07", "09:45:00")
    assert len(Alerta.listar(db, estado="pendiente")) == 1
    Alerta.marcar_leida(db, a._id)
    assert len(Alerta.listar(db, estado="pendiente")) == 0
    assert len(Alerta.listar(db, estado="leida")) == 1