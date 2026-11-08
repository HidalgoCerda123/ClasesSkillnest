import logging
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_cadena_queja_segura,
    construir_paso_clasificacion,
    procesar_mensaje_seguro,
)


# ======================= CLASIFICACIÓN ================================

def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Queja \n")

    paso_clasificacion = construir_paso_clasificacion(modelo_falso)
    resultado = paso_clasificacion.invoke({"mensaje": "esto es un desastre"})

    assert resultado == "queja"


def test_clasificacion_con_texto_vacio_no_rompe_el_flujo():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content="")
    cadena_pregunta_falsa = MagicMock()
    cadena_pregunta_falsa.return_value = "respuesta por defecto"

    paso_clasificacion = construir_paso_clasificacion(modelo_falso)
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion, cadena_pregunta=cadena_pregunta_falsa
    )
    resultado = cadena.invoke({"mensaje": ""})

    assert resultado == "respuesta por defecto"


# ======================= BIFURCACIÓN ==================================

def test_enrutamiento_va_a_cadena_queja():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "queja"
    cadena_queja_falsa = MagicMock()
    cadena_queja_falsa.return_value = "respuesta de queja"

    cadena = construir_cadena_con_enrutamiento(
        clasificacion_falsa, cadena_queja=cadena_queja_falsa
    )
    resultado = cadena.invoke({"mensaje": "no me funciona nada"})

    assert cadena_queja_falsa.called
    assert resultado == "respuesta de queja"


def test_enrutamiento_va_a_cadena_sugerencia():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "sugerencia"
    cadena_sugerencia_falsa = MagicMock()
    cadena_sugerencia_falsa.return_value = "respuesta de sugerencia"

    cadena = construir_cadena_con_enrutamiento(
        clasificacion_falsa, cadena_sugerencia=cadena_sugerencia_falsa
    )
    resultado = cadena.invoke({"mensaje": "agreguen modo oscuro"})

    assert cadena_sugerencia_falsa.called
    assert resultado == "respuesta de sugerencia"


def test_enrutamiento_va_a_cadena_pregunta():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "pregunta"
    cadena_pregunta_falsa = MagicMock()
    cadena_pregunta_falsa.return_value = "respuesta de pregunta"

    cadena = construir_cadena_con_enrutamiento(
        clasificacion_falsa, cadena_pregunta=cadena_pregunta_falsa
    )
    resultado = cadena.invoke({"mensaje": "¿cómo cambio mi contraseña?"})

    assert cadena_pregunta_falsa.called
    assert resultado == "respuesta de pregunta"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "categoria_inventada"
    cadena_queja_falsa = MagicMock()
    cadena_sugerencia_falsa = MagicMock()
    cadena_pregunta_falsa = MagicMock()
    cadena_pregunta_falsa.return_value = "respuesta por defecto"

    cadena = construir_cadena_con_enrutamiento(
        clasificacion_falsa,
        cadena_queja=cadena_queja_falsa,
        cadena_sugerencia=cadena_sugerencia_falsa,
        cadena_pregunta=cadena_pregunta_falsa,
    )
    resultado = cadena.invoke({"mensaje": "mensaje cualquiera"})

    assert cadena_pregunta_falsa.called
    assert not cadena_queja_falsa.called
    assert not cadena_sugerencia_falsa.called
    assert resultado == "respuesta por defecto"


# ======================= FALLBACKS ====================================

def test_cadena_queja_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(x):
        raise ConnectionError("simulado")

    cadena_segura = construir_cadena_queja_segura(
        RunnableLambda(fallar_a_proposito)
    )
    resultado = cadena_segura.invoke({"mensaje": "esto no funciona"})

    assert "equipo" in resultado.lower()


def test_cadena_queja_no_usa_fallback_si_la_ruta_funciona():
    cadena_segura = construir_cadena_queja_segura(
        RunnableLambda(lambda x: "respuesta normal de queja")
    )
    resultado = cadena_segura.invoke({"mensaje": "esto no funciona"})

    assert resultado == "respuesta normal de queja"


# ======================= FLUJO COMPLETO ===============================

def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")
    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa
    )

    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert "no pudimos procesar" in resultado.lower()


def test_procesar_mensaje_seguro_registra_el_error(caplog):
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("fallo simulado")
    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa
    )

    with caplog.at_level(logging.ERROR):
        procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert "fallo simulado" in caplog.text


def test_procesar_mensaje_seguro_devuelve_la_respuesta_si_todo_funciona():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "pregunta"
    cadena_pregunta_falsa = MagicMock()
    cadena_pregunta_falsa.return_value = "respuesta normal"
    cadena = construir_cadena_con_enrutamiento(
        clasificacion_falsa, cadena_pregunta=cadena_pregunta_falsa
    )

    resultado = procesar_mensaje_seguro(cadena, "¿cómo cambio mi contraseña?")

    assert resultado == "respuesta normal"
