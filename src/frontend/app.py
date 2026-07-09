"""Dashboard Streamlit para consumo e visualização da API LSTM (PETR4.SA).

Fluxo:
 1. Usuário escolhe uma data de previsão (de 90 dias atrás até amanhã).
 2. App carrega do Yahoo Finance os 60 pregões anteriores a essa data.
 3. Ao prever, envia os 60 fechamentos à API LSTM e mostra o resultado.
 4. Se a data for passada, busca o valor real e compara (gráfico + métricas).
"""

from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

from src.frontend import api_client, data
from src.frontend.config import (
    API_URL,
    GRAFANA_PUBLIC_URL,
    TICKER,
    WINDOW_SIZE,
)
from src.frontend.status import check_all

st.set_page_config(page_title="Previsão LSTM - PETR4.SA", page_icon="📈", layout="wide")


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Configuração")
    st.text_input("Ativo (fixo)", value=TICKER, disabled=True)
    st.caption(f"API LSTM: `{API_URL}`")
    st.caption(f"Janela do modelo: **{WINDOW_SIZE} pregões**")
    st.markdown(f"### 📊 [Abrir dashboard no Grafana]({GRAFANA_PUBLIC_URL})")
    st.caption("Observabilidade da API (latência, req/s, erros, disponibilidade).")


st.title("📈 Previsão de fechamento — PETR4.SA (LSTM)")
st.write(
    "Selecione um dia de previsão, carregue os **60 pregões anteriores** do Yahoo Finance "
    "e envie-os ao modelo LSTM. Para datas passadas, comparamos com o valor real."
)


# --------------------------------------------------------------------------- #
# Painel de status dos serviços
# --------------------------------------------------------------------------- #
st.subheader("🩺 Status dos serviços")
status_cols = st.columns([1, 1, 1, 1])
if status_cols[3].button("🔄 Verificar saúde", use_container_width=True):
    st.session_state.pop("service_status", None)

if "service_status" not in st.session_state:
    with st.spinner("Verificando serviços..."):
        st.session_state["service_status"] = check_all()

for col, svc in zip(status_cols[:3], st.session_state["service_status"]):
    icon = "🟢" if svc.ok else "🔴"
    col.metric(label=f"{icon} {svc.name}", value="Disponível" if svc.ok else "Indisponível")
    col.caption(svc.detail)


st.divider()

# --------------------------------------------------------------------------- #
# Seleção da data e carregamento dos dados
# --------------------------------------------------------------------------- #
today = date.today()
tomorrow = today + timedelta(days=1)
min_date = today - timedelta(days=90)

st.subheader("1️⃣ Escolha o dia da previsão")
col_a, col_b = st.columns([2, 1])
prediction_date = col_a.date_input(
    "Dia a prever (fechamento)",
    value=tomorrow,
    min_value=min_date,
    max_value=tomorrow,
    help="De 90 dias atrás até amanhã. Datas passadas permitem comparar com o valor real.",
)
is_future = prediction_date > today

if col_b.button("⬇️ Carregar 60 dias (Yahoo Finance)", use_container_width=True):
    try:
        with st.spinner("Baixando dados do Yahoo Finance..."):
            window_df = data.load_input_window(TICKER, prediction_date)
        st.session_state["window_df"] = window_df
        st.session_state["window_date"] = prediction_date
        st.session_state.pop("prediction", None)
        st.session_state.pop("real_close", None)
        st.success(f"{len(window_df)} pregões carregados (até o dia anterior a {prediction_date}).")
    except data.InsufficientDataError as exc:
        st.error(str(exc))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Erro ao buscar dados do Yahoo Finance: {exc}")


# --------------------------------------------------------------------------- #
# Exibição da janela + previsão
# --------------------------------------------------------------------------- #
window_df = st.session_state.get("window_df")
window_date = st.session_state.get("window_date")

if window_df is not None and window_date == prediction_date:
    st.subheader("2️⃣ Dados de entrada e previsão")

    left, right = st.columns([1, 3])
    with left:
        st.caption("Últimos pregões enviados")
        st.dataframe(
            window_df.rename(columns={"Close": "Fechamento (R$)"}).tail(10),
            use_container_width=True,
        )
        predict_clicked = st.button("🔮 Prever com a LSTM", type="primary", use_container_width=True)

    if predict_clicked:
        prices = [float(v) for v in window_df["Close"].tolist()]
        try:
            with st.spinner("Consultando a API LSTM..."):
                prediction = api_client.predict(prices)
        except api_client.APIError as exc:
            st.error(f"Falha na previsão: {exc}")
            st.session_state.pop("prediction", None)
            st.session_state.pop("real_close", None)
        else:
            # A previsão deu certo; buscar o valor real é "best effort" — se
            # falhar, a previsão continua exibida, apenas sem comparação.
            st.session_state["prediction"] = prediction
            real_close = None
            if not is_future:
                try:
                    real_close = data.load_real_close(TICKER, prediction_date)
                except data.DataFetchError as exc:
                    st.warning(f"Não foi possível obter o valor real para comparação: {exc}")
            st.session_state["real_close"] = real_close

    prediction = st.session_state.get("prediction")
    real_close = st.session_state.get("real_close")

    with right:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=window_df.index,
                y=window_df["Close"],
                mode="lines",
                name="Fechamento (60 dias)",
                line=dict(color="#1f77b4"),
            )
        )
        pred_x = window_df.index[-1] + timedelta(days=1)
        if prediction is not None:
            fig.add_trace(
                go.Scatter(
                    x=[pred_x],
                    y=[prediction],
                    mode="markers",
                    name="Previsão LSTM",
                    marker=dict(color="orange", size=13, symbol="star"),
                )
            )
        if real_close is not None:
            fig.add_trace(
                go.Scatter(
                    x=[pred_x],
                    y=[real_close],
                    mode="markers",
                    name="Valor real",
                    marker=dict(color="green", size=13, symbol="circle"),
                )
            )
        fig.update_layout(
            title=f"PETR4.SA — janela de entrada e previsão para {prediction_date}",
            xaxis_title="Data",
            yaxis_title="Preço (R$)",
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Métricas
    if prediction is not None:
        st.subheader("3️⃣ Resultado")
        if real_close is not None:
            abs_err = abs(prediction - real_close)
            pct_err = abs_err / real_close * 100
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Previsão LSTM", f"R$ {prediction:.2f}")
            m2.metric("Valor real", f"R$ {real_close:.2f}")
            m3.metric("Erro absoluto", f"R$ {abs_err:.2f}")
            m4.metric("Erro percentual", f"{pct_err:.2f}%")
        else:
            m1, m2 = st.columns(2)
            m1.metric("Previsão LSTM", f"R$ {prediction:.2f}")
            if is_future:
                m2.info("Data futura: valor real ainda não existe para comparação.")
            else:
                m2.warning("Sem valor real para esta data (não houve pregão).")
elif window_df is not None:
    st.info("A data foi alterada. Clique em **Carregar 60 dias** novamente para atualizar a janela.")
