import pytest

from gestion_registros import (
    _dias_habiles,
    crear_id_registro,
    detectar_inasistencias,
    ultimo_dia_mes,
)


def test_dias_habiles_semana_completa():
    dias = _dias_habiles("2026-09-07", "2026-09-11")
    assert dias == ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]


def test_dias_habiles_excluye_fin_de_semana():
    dias = _dias_habiles("2026-09-11", "2026-09-14")
    assert dias == ["2026-09-11", "2026-09-14"]


def test_dias_habiles_rango_vacio_o_inverso():
    assert _dias_habiles("2026-09-14", "2026-09-12") == []


def test_ultimo_dia_mes_no_diciembre():
    assert ultimo_dia_mes("2026-02-01") == "2026-02-28"


def test_ultimo_dia_mes_diciembre():
    assert ultimo_dia_mes("2026-12-01") == "2026-12-31"


def test_crear_id_registro():
    assert crear_id_registro("juan", "2026-09-07", "entrada") == "juan_2026-09-07_entrada"


def test_detectar_inasistencias_usuario_sin_marcas():
    marcaciones = []
    usuarios = [{"usuario": "juan", "nombre": "Juan"}]
    resultado = detectar_inasistencias(marcaciones, usuarios, "2026-09-07", "2026-09-11")
    assert len(resultado) == 5
    assert resultado[0] == {"usuario": "juan", "fecha": "2026-09-07"}


def test_detectar_inasistencias_descarta_dias_con_marca():
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
    marcaciones = [
        {"usuario": "juan", "fecha": "2026-09-08", "tipo": "entrada"},
    ]
    usuarios = [{"usuario": "juan", "nombre": "Juan"}]
    resultado = detectar_inasistencias(marcaciones, usuarios, "2026-09-07", "2026-09-11")
    fechas = [i["fecha"] for i in resultado]
    assert "2026-09-08" not in fechas


def test_detectar_inasistencias_multiples_usuarios():
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