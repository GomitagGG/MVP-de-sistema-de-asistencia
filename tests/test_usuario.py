from modelos import Usuario

from fake_db import FakeDB


def test_buscar_por_usuario():
    db = FakeDB()
    db.collection("usuarios").add({
        "usuario": "juan", "correo": "juan@empresa.cl",
        "clave": "123456", "rol": "trabajador", "nombre": "Juan Perez",
    })
    doc = Usuario.buscar_por_identificador(db, "juan")
    assert doc is not None
    assert doc["usuario"] == "juan"
    assert doc["rol"] == "trabajador"
    assert doc["_id"] is not None


def test_buscar_por_correo():
    db = FakeDB()
    db.collection("usuarios").add({
        "usuario": "ana", "correo": "ana@empresa.cl",
        "clave": "abcdef", "rol": "administrador", "nombre": "Ana Soto",
    })
    doc = Usuario.buscar_por_identificador(db, "ana@empresa.cl")
    assert doc is not None
    assert doc["usuario"] == "ana"


def test_buscar_identificador_inexistente():
    db = FakeDB()
    db.collection("usuarios").add({
        "usuario": "juan", "correo": "juan@empresa.cl",
        "clave": "123456", "rol": "trabajador", "nombre": "Juan",
    })
    assert Usuario.buscar_por_identificador(db, "pedro") is None


def test_clave_valida_correcta():
    doc = {"clave": "secreta123"}
    assert Usuario.clave_valida(doc, "secreta123") is True


def test_clave_valida_incorrecta():
    doc = {"clave": "secreta123"}
    assert Usuario.clave_valida(doc, "otra") is False


def test_clave_valida_doc_nulo():
    assert Usuario.clave_valida(None, "secreta123") is False


def test_to_dict_incluye_campos():
    u = Usuario({"usuario": "juan", "correo": "j@e.cl", "clave": "x",
                 "rol": "trabajador", "nombre": "Juan"})
    d = u.to_dict()
    assert d["usuario"] == "juan"
    assert d["rol"] == "trabajador"
    assert d["nombre"] == "Juan"