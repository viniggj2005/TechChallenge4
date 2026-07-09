"""Checagem de disponibilidade dos serviços da stack (API, Prometheus, Grafana).

Prova que os containers estão de pé consultando os endpoints de health de cada
serviço pela rede interna do docker-compose.
"""

from typing import List, NamedTuple

import requests

from src.frontend.api_client import check_health as api_health
from src.frontend.config import GRAFANA_HEALTH_URL, PROMETHEUS_URL

TIMEOUT = 10


class ServiceStatus(NamedTuple):
    name: str
    ok: bool
    detail: str


def _check_http(name: str, url: str, expect_json_ok: bool = False) -> ServiceStatus:
    """Verifica um endpoint de health via HTTP. Nunca lança exceção."""
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        if expect_json_ok:
            data = resp.json()
            ok = str(data.get("database", "")).lower() == "ok"
            return ServiceStatus(name, ok, "OK" if ok else f"resposta inesperada: {data}")
        return ServiceStatus(name, True, "OK")
    except requests.RequestException as exc:
        return ServiceStatus(name, False, f"indisponível ({exc.__class__.__name__})")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        return ServiceStatus(name, False, f"resposta inesperada ({exc.__class__.__name__})")


def check_all() -> List[ServiceStatus]:
    """Retorna o status de API, Prometheus e Grafana. Cada checagem é isolada:
    a falha de um serviço nunca impede a checagem dos demais nem lança exceção.
    """
    results = []
    for label, check_fn in (
        ("API LSTM", lambda: ServiceStatus("API LSTM", *api_health())),
        ("Prometheus", lambda: _check_http("Prometheus", f"{PROMETHEUS_URL}/-/healthy")),
        ("Grafana", lambda: _check_http("Grafana", GRAFANA_HEALTH_URL, expect_json_ok=True)),
    ):
        try:
            results.append(check_fn())
        except Exception as exc:  # noqa: BLE001 - blindagem final; nunca deve propagar
            results.append(ServiceStatus(label, False, f"erro inesperado ({exc.__class__.__name__})"))
    return results
