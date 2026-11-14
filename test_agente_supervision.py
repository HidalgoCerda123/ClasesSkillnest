import json
import time
from types import SimpleNamespace

import agente_supervision as sup


def test_aprobacion_solo_con_s(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: " S ")
    assert sup.esperar_aprobacion("¿?") is True
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert sup.esperar_aprobacion("¿?") is False


def test_sin_respuesta_a_tiempo_no_aprueba(monkeypatch):
    def lento(_):
        time.sleep(1)
        return "s"

    monkeypatch.setattr("builtins.input", lento)
    assert sup.esperar_aprobacion("¿?", tiempo_limite_segundos=0.1) is False


def test_sin_stdin_no_aprueba(monkeypatch):
    def sin_stdin(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", sin_stdin)
    assert sup.esperar_aprobacion("¿?") is False


def test_reembolso_rechazado_no_se_ejecuta_y_queda_registrado(monkeypatch, tmp_path):
    monkeypatch.setattr(sup, "ARCHIVO_APROBACIONES", str(tmp_path / "aprob.jsonl"))
    monkeypatch.setattr(sup, "registro_aprobaciones", [])
    monkeypatch.setattr("builtins.input", lambda _: "n")
    salida = sup.generar_reembolso.invoke({"numero_pedido": "P-1", "monto": 100})
    assert "no aprobado" in salida
    assert sup.registro_aprobaciones[0]["aprobado"] is False
    guardado = json.loads((tmp_path / "aprob.jsonl").read_text(encoding="utf-8"))
    assert guardado["herramienta"] == "generar_reembolso"


def _resultado(*nombres):
    pasos = [
        (SimpleNamespace(tool=nombre, tool_input={"x": 1}), "observación")
        for nombre in nombres
    ]
    return {"intermediate_steps": pasos, "output": "listo"}


def test_traza_y_repeticiones(tmp_path):
    archivo = str(tmp_path / "trazas.jsonl")
    sup.registrar_traza("normal", "hola", _resultado("a", "b", "a"), archivo)
    sup.registrar_traza("repetida", "hola", _resultado("a", "a"), archivo)
    with open(archivo, "a", encoding="utf-8") as salida:
        salida.write("esto no es json\n")

    primera = json.loads(open(archivo, encoding="utf-8").readline())
    assert primera["acciones"][0] == {
        "herramienta": "a", "argumentos": {"x": 1}, "observacion": "observación"
    }
    assert primera["respuesta_final"] == "listo"
    assert sup.marcar_repeticiones_sospechosas(archivo) == ["repetida"]


def test_repeticiones_sin_archivo(tmp_path):
    assert sup.marcar_repeticiones_sospechosas(str(tmp_path / "no_existe.jsonl")) == []
