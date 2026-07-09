"""Cliente HTTP para a API LSTM (endpoints /health e /predict)."""

from typing import List, Tuple

import requests

from src.frontend.config import API_URL

TIMEOUT = 15


class APIError(Exception):
    """Erro ao comunicar com a API LSTM."""


def check_health() -> Tuple[bool, str]:
    """Consulta GET /health. Retorna (ok, detalhe). Nunca lança exceção."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        model_loaded = data.get("model_loaded", False)
        status = data.get("status", "unknown")
        if status == "healthy" and model_loaded:
            return True, "API saudável e modelo carregado"
        return False, f"status={status}, model_loaded={model_loaded}"
    except requests.RequestException as exc:
        return False, f"Sem resposta da API ({exc.__class__.__name__})"
    except (ValueError, KeyError, TypeError) as exc:
        # resposta 200 mas corpo não é o JSON esperado.
        return False, f"Resposta inesperada da API ({exc.__class__.__name__})"


def predict(prices: List[float]) -> float:
    """Envia os preços ao POST /predict e retorna a previsão."""
    try:
        resp = requests.post(
            f"{API_URL}/predict", json={"prices": prices}, timeout=TIMEOUT
        )
    except requests.RequestException as exc:
        raise APIError(f"Não foi possível conectar à API: {exc.__class__.__name__}") from exc

    if resp.status_code == 200:
        try:
            return float(resp.json()["prediction"])
        except (ValueError, KeyError, TypeError) as exc:
            raise APIError(
                f"Resposta inesperada da API (200 OK, mas corpo inválido): {exc}"
            ) from exc

    # Erros tratados pela API (400/422/500) trazem "detail".
    try:
        detail = resp.json().get("detail", resp.text)
    except (ValueError, AttributeError):
        detail = resp.text
    raise APIError(f"API retornou {resp.status_code}: {detail}")
