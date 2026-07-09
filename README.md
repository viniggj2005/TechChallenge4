# TechChallenge4
Repositorio referente ao curso de pós graduação em Machine Learning Engineering

Sistema de previsão de preços da ação **PETR4.SA** com rede neural LSTM, disponibilizado via API
REST (FastAPI), interface de visualização (Streamlit) e monitoramento (Prometheus + Grafana).

| Serviço    | Descrição                                              | URL local              |
| ---------- | ------------------------------------------------------ | ---------------------- |
| API        | FastAPI servindo o modelo LSTM (`/predict`, `/health`) | http://localhost:8000  |
| Swagger    | Documentação interativa da API                         | http://localhost:8000/docs |
| Streamlit  | Visualização: previsão do modelo x valor real          | http://localhost:8501  |
| Prometheus | Coleta de métricas da API                              | http://localhost:9090  |
| Grafana    | Dashboards de observabilidade (admin/admin)            | http://localhost:3000  |

Para subir tudo: `cd infra && docker compose up -d --build`.

## Interface de visualização (Streamlit)

Abra http://localhost:8501:

1. Confira o **painel de status** (API, Prometheus, Grafana devem aparecer 🟢) — use o botão
   **Verificar saúde** para revalidar.
2. Escolha um **dia de previsão** (de 90 dias atrás até amanhã).
3. Clique em **Carregar 60 dias** para buscar os pregões do Yahoo Finance.
4. Clique em **Prever com a LSTM** — os 60 fechamentos são enviados à API e a previsão é exibida.
   - Datas passadas comparam a previsão com o **valor real** (gráfico sobreposto + erro absoluto/%).
   - Datas futuras (amanhã) mostram só a previsão.
5. Use o link do **Grafana** na barra lateral para a observabilidade da API.

## Cirando a imagem e subindo os containers

Build & subida

docker compose build api — imagem construída sem erros.
docker compose up -d — os 3 serviços (api, prometheus, grafana) subiram, api reportando healthy no healthcheck.
API (dentro do container)

/health → {"status":"healthy","model_loaded":true}
/predict (60 preços) → previsão retornada corretamente
/metrics → métricas Prometheus expostas (via prometheus-fastapi-instrumentator)
Prometheus

Target api:8000/metrics com status up — coleta funcionando.
Grafana

Health check OK, datasource "Prometheus" provisionado automaticamente apontando para http://prometheus:9090.
Dashboard "LSTM Stock API - Monitoramento" provisionado automaticamente (disponibilidade, req/s por endpoint, taxa de erros 4xx/5xx, latência p95).



## Dashboard de observabilidade grafana 

1. Abra o Grafana no navegador
Acesse: http://localhost:3000

2. Faça login
Usuário: admin
Senha: admin
(Essas credenciais estão definidas no infra/docker-compose.yml, no serviço grafana, via GF_SECURITY_ADMIN_USER / GF_SECURITY_ADMIN_PASSWORD.)

Na primeira vez o Grafana pode pedir para trocar a senha — você pode clicar em "Skip" se quiser manter admin/admin.

3. Abra o dashboard já provisionado
Você não precisa criar nada manualmente — o dashboard é carregado automaticamente ao subir o container. Para abri-lo:

No menu lateral esquerdo, clique no ícone de Dashboards (quatro quadrados).
Você verá o dashboard "LSTM Stock API - Monitoramento" na lista.
Clique nele para abrir.
Ou acesse diretamente pela URL:
http://localhost:3000/d/lstm-stock-api/lstm-stock-api-monitoramento

4. O que você vai ver
O dashboard tem 5 painéis, atualizando a cada 10s:

Disponibilidade da API (up) — 1 = API respondendo, 0 = fora do ar.
Requisições por segundo (por endpoint) — tráfego em /health, /predict, etc.
Taxa de erros (4xx e 5xx).
Latência p95 — tempo de resposta.
Total de requisições por status HTTP.
5. Gerando dados para ver os gráficos se movendo
Se os gráficos estiverem vazios/planos, é porque ainda não houve tráfego. Gere algumas chamadas: