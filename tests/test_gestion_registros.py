import pytest

from gestion_registros import (
    _dias_habiles,
    crear_id_registro,
    detectar_inasistencias,
    ultimo_dia_mes,
)


def test_dias_habiles_semana_completa():
    """Prueba que la función incluya todos los días hábiles de una semana completa.

    @return None: Verifica que el rango de fechas devuelva exactamente los días laborables esperados.
    """
    dias = _dias_habiles("2026-09-07", "2026-09-11")
    assert dias == ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]


def test_dias_habiles_excluye_fin_de_semana():
    """Prueba que los fines de semana se excluyan del cálculo de días hábiles.

    @return None: Verifica que solo queden los días laborables del rango indicado.
    """
    dias = _dias_habiles("2026-09-11", "2026-09-14")
    assert dias == ["2026-09-11", "2026-09-14"]


def test_dias_habiles_excluye_feriados():
    """Prueba que los feriados se excluyan del cálculo de días hábiles.

    @return None: Verifica que 2026-09-17 y 2026-09-18 no se incluyan.
    """
    dias = _dias_habiles("2026-09-14", "2026-09-18")
    assert dias == ["2026-09-14", "2026-09-15", "2026-09-16"]


def test_dias_habiles_rango_vacio_o_inverso():
    """Prueba que un rango vacío o invertido devuelva una lista vacía.

    @return None: Verifica el caso de fechas con orden inverso.
    """
    assert _dias_habiles("2026-09-14", "2026-09-12") == []


def test_ultimo_dia_mes_no_diciembre():
    """Prueba que el último día del mes sea correcto para meses normales.

    @return None: Verifica el cálculo para febrero de 2026.
    """
    assert ultimo_dia_mes("2026-02-01") == "2026-02-28"


def test_ultimo_dia_mes_diciembre():
    """Prueba que el último día de diciembre se calcule correctamente.

    @return None: Verifica el valor esperado para el mes de diciembre.
    """
    assert ultimo_dia_mes("2026-12-01") == "2026-12-31"


def test_crear_id_registro():
    """Prueba la generación del identificador único del registro.

    @return None: Verifica que el formato del ID coincida con usuario_fecha_tipo.
    """
    assert crear_id_registro("juan", "2026-09-07", "entrada") == "juan_2026-09-07_entrada"


def test_detectar_inasistencias_usuario_sin_marcas():
    """Prueba la detección de inasistencias cuando un usuario no tiene ninguna marca.

    @return None: Verifica que se registren todas las faltas del rango indicado.
    """
    marcaciones = []
    usuarios = [{"usuario": "juan", "nombre": "Juan"}]
    resultado = detectar_inasistencias(marcaciones, usuarios, "2026-09-07", "2026-09-11")
    assert len(resultado) == 5
    assert resultado[0] == {"usuario": "juan", "fecha": "2026-09-07"}


def test_detectar_inasistencias_descarta_dias_con_marca():
    """Prueba que los días con alguna marca sean descartados como inasistencias.

    @return None: Verifica que las fechas con entrada y salida no aparezcan como faltas.
    """
    marcaciones = [
        {"usuario": "juan", "fecha": "2026-09-07", "tipo": "entrada"},
        {"usuario": "juan", "fecha": "2026-09-07", "tipo": "salida"},
    ]
    usuarios = [{"usuario": "juan", "nombre": "Juan"}]
    resultado = detectar_inasistencias(marcaciones, usuarios, "2026-09-07", "2026-09-11")
    fechas = [i["fecha"] for i in resultado]
    assert "2026-09-07" not in fechas
    assert len(fechas) == 4


def test_detectar_inasistencias_solo_entrada_no_es_inasistencia():
    """Prueba que una sola marca de entrada no se considere una inasistencia completa.

    @return None: Verifica que la fecha con entrada no aparezca como ausencia.
    """
    marcaciones = [
        {"usuario": "juan", "fecha": "2026-09-08", "tipo": "entrada"},
    ]
    usuarios = [{"usuario": "juan", "nombre": "Juan"}]
    resultado = detectar_inasistencias(marcaciones, usuarios, "2026-09-07", "2026-09-11")
    fechas = [i["fecha"] for i in resultado]
    assert "2026-09-08" not in fechas


def test_detectar_inasistencias_multiples_usuarios():
    """Prueba que la detección funcione para varios usuarios al mismo tiempo.

    @return None: Verifica que solo los usuarios sin marca para la fecha queden reportados.
    """
    marcaciones = [
        {"usuario": "ana", "fecha": "2026-09-07", "tipo": "entrada"},
    ]
    usuarios = [
        {"usuario": "ana", "nombre": "Ana"},
        {"usuario": "pedro", "nombre": "Pedro"},
    ]
    resultado = detectar_inasistencias(marcaciones, usuarios, "2026-09-07", "2026-09-08")
    assert len(resultado) == 3
    abacidos_en_0709 = [i for i in resultado if i["fecha"] == "2026-09-07"]
    assert {i["usuario"] for i in abacidos_en_0709} == {"pedro"}