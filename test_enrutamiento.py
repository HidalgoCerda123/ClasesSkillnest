from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
)


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


def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Queja \n")

    paso_clasificacion = construir_paso_clasificacion(modelo_falso)
    resultado = paso_clasificacion.invoke({"mensaje": "esto es un desastre"})

    assert resultado == "queja"


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
