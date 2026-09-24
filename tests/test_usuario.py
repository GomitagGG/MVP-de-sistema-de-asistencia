from modelos import Usuario

from fake_db import FakeDB


def test_buscar_por_usuario():
    """Prueba que la búsqueda por nombre de usuario encuentre al usuario correcto.

    @return None: Verifica que el documento devuelto pertenezca al usuario esperado.
    """
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
    """Prueba que la búsqueda por correo electrónico funcione correctamente.

    @return None: Verifica que el usuario identificado por correo sea el correcto.
    """
    db = FakeDB()
    db.collection("usuarios").add({
        "usuario": "ana", "correo": "ana@empresa.cl",
        "clave": "abcdef", "rol": "administrador", "nombre": "Ana Soto",
    })
    doc = Usuario.buscar_por_identificador(db, "ana@empresa.cl")
    assert doc is not None
    assert doc["usuario"] == "ana"


def test_buscar_identificador_inexistente():
    """Prueba que una búsqueda con identificador inexistente devuelva None.

    @return None: Verifica la ausencia de resultados para un usuario no registrado.
    """
    db = FakeDB()
    db.collection("usuarios").add({
        "usuario": "juan", "correo": "juan@empresa.cl",
        "clave": "123456", "rol": "trabajador", "nombre": "Juan",
    })
    assert Usuario.buscar_por_identificador(db, "pedro") is None


def test_clave_valida_correcta():
    """Prueba que una contraseña válida sea aceptada correctamente.

    @return None: Verifica que la validación retorna True para la clave correcta.
    """
    doc = {"clave": "secreta123"}
    assert Usuario.clave_valida(doc, "secreta123") is True


def test_clave_valida_incorrecta():
    """Prueba que una contraseña incorrecta sea rechazada.

    @return None: Verifica que la validación retorna False para una clave distinta.
    """
    doc = {"clave": "secreta123"}
    assert Usuario.clave_valida(doc, "otra") is False


def test_clave_valida_doc_nulo():
    """Prueba que una referencia nula no rompa la validación de clave.

    @return None: Verifica que se maneje safely un documento nulo.
    """
    assert Usuario.clave_valida(None, "secreta123") is False


def test_to_dict_incluye_campos():
    """Prueba que el método to_dict exponga los campos esperados del usuario.

    @return None: Verifica que la conversión a diccionario incluya datos básicos.
    """
    u = Usuario({"usuario": "juan", "correo": "j@e.cl", "clave": "x",
                 "rol": "trabajador", "nombre": "Juan"})
    d = u.to_dict()
    assert d["usuario"] == "juan"
    assert d["rol"] == "trabajador"
    assert d["nombre"] == "Juan"