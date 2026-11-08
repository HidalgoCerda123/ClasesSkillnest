from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from cadena_tres_pasos import construir_cadena


def test_cadena_conecta_los_tres_pasos():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="punto 1\npunto 2\npunto 3"),
        AIMessage(content="texto simplificado"),
        AIMessage(content="- viñeta 1\n- viñeta 2"),
    ]

    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"mensaje": "texto de prueba"})

    assert modelo_falso.call_count == 3
    assert "viñeta" in resultado


def test_cadena_pasa_la_salida_de_cada_paso_al_siguiente():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="SALIDA_PASO_1"),
        AIMessage(content="SALIDA_PASO_2"),
        AIMessage(content="SALIDA_PASO_3"),
    ]

    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"mensaje": "ENTRADA_ORIGINAL"})

    prompt_1, prompt_2, prompt_3 = [
        str(llamada.args[0]) for llamada in modelo_falso.call_args_list
    ]
    assert "ENTRADA_ORIGINAL" in prompt_1
    assert "SALIDA_PASO_1" in prompt_2
    assert "SALIDA_PASO_2" in prompt_3
    assert resultado == "SALIDA_PASO_3"
