"""Configurações do frontend Streamlit, lidas de variáveis de ambiente.

Os defaults apontam para `localhost` (execução fora do Docker). No
docker-compose esses valores são sobrescritos para os nomes de serviço da
rede interna (ex.: http://api:8000).
"""

import os

TICKER = "PETR4.SA"
WINDOW_SIZE = 60

# URL da API LSTM consumida pelo app.
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Endpoints de health dos serviços (rede interna quando em container).
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_HEALTH_URL = os.getenv("GRAFANA_HEALTH_URL", "http://localhost:3000/api/health")

# Link público (resolvido pelo navegador do usuário, não pela rede interna).
GRAFANA_PUBLIC_URL = os.getenv(
    "GRAFANA_PUBLIC_URL",
    "http://localhost:3000/d/lstm-stock-api/lstm-stock-api-monitoramento",
)
