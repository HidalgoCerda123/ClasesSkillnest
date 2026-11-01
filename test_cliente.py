from unittest.mock import Mock, patch

import pytest

import cliente
from src.consumir_gemini import enviar_peticion

URL_FALSA = "https://ejemplo.invald"
BODY_FALSO = {"pregunta": "test"}


@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    cliente.costo_total_sesion = 0.0
    yield
    cliente.costo_total_sesion = 0.0


# ======================= TEST ENVIAR_PETICION ==========================

def test_enviar_peticion_credencial_invalida():
    respuesta_falsa = Mock(status_code=401)

    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion(URL_FALSA, BODY_FALSO)


def test_enviar_peticion_limite_de_uso():
    respuesta_falsa = Mock(status_code=429, headers={})

    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion(URL_FALSA, BODY_FALSO)


def test_enviar_peticion_exito():
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}

    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa) as post_falso:
        resultado = enviar_peticion(URL_FALSA, BODY_FALSO)

    assert resultado == {"texto": "respuesta simulada"}
    # comprueba que la función real armó la petición, no solo el valor del mock
    post_falso.assert_called_once_with(URL_FALSA, json=BODY_FALSO, timeout=120)


# ======================= TEST CON_REINTENTO ============================

def test_con_reintento_agota_intentos():
    funcion_falsa = Mock(side_effect=TimeoutError("proveedor saturado"))

    with patch("cliente.time.sleep") as sleep_falso:
        with pytest.raises(TimeoutError):
            cliente.con_reintento(funcion_falsa, intentos=3)

    assert funcion_falsa.call_count == 3
    assert sleep_falso.call_count == 2  # espera entre intentos, no tras el último


def test_con_reintento_no_reintenta_value_error():
    funcion_falsa = Mock(side_effect=ValueError("credencial invalida"))

    with patch("cliente.time.sleep") as sleep_falso:
        with pytest.raises(ValueError):
            cliente.con_reintento(funcion_falsa, intentos=3)

    assert funcion_falsa.call_count == 1
    sleep_falso.assert_not_called()


# ======================= TEST REGISTRAR_COSTO ==========================

def test_registrar_costo_acumula():
    primera = {"usageMetadata": {"totalTokenCount": 1000}}
    segunda = {"usageMetadata": {"totalTokenCount": 500}}

    costo_1 = cliente.registrar_costo(primera)
    costo_2 = cliente.registrar_costo(segunda)

    assert costo_1 == pytest.approx(0.002)
    assert costo_2 == pytest.approx(0.001)
    assert cliente.costo_total_sesion == pytest.approx(0.003)


# ======================= TEST CONSULTAR_MODELO =========================

def test_consultar_modelo_convierte_error():
    with patch("cliente.enviar_peticion", side_effect=TimeoutError("503")), \
            patch("cliente.time.sleep"):
        with pytest.raises(RuntimeError, match="no respondió"):
            cliente.consultar_modelo("¿Cuál es la capital de Chile?")

    assert cliente.costo_total_sesion == 0.0
