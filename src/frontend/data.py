"""Coleta de dados de mercado via Yahoo Finance (yfinance).

Regra de negócio: o modelo LSTM recebe os `WINDOW_SIZE` (=60) fechamentos de
pregão imediatamente anteriores à data D e prevê o fechamento de D.
"""

from datetime import date, timedelta
from typing import Optional

import pandas as pd
import streamlit as st
import yfinance as yf

from src.frontend.config import WINDOW_SIZE


class InsufficientDataError(Exception):
    """Não há pregões suficientes para montar a janela de entrada."""


class DataFetchError(Exception):
    """Falha inesperada ao consultar o Yahoo Finance (rede, rate limit, etc.)."""


@st.cache_data(show_spinner=False, ttl=3600)
def _download(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Baixa dados brutos do Yahoo Finance (cacheado por 1h)."""
    try:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    except Exception as exc:  # noqa: BLE001 - yfinance pode lançar diversos tipos
        raise DataFetchError(
            f"Falha ao consultar o Yahoo Finance: {exc.__class__.__name__}: {exc}"
        ) from exc

    if df is None or df.empty:
        return pd.DataFrame()
    # Com múltiplos tickers o yfinance retorna colunas MultiIndex; normalizamos.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[["Close"]].dropna()


def load_input_window(ticker: str, prediction_date: date, window: int = WINDOW_SIZE) -> pd.DataFrame:
    """Retorna os `window` fechamentos de pregão anteriores a `prediction_date`.

    O `end` do yfinance é exclusivo, então usamos `end=prediction_date` para
    obter dados até o pregão anterior a D.
    """
    # ~150 dias corridos garantem >= 60 pregões (fins de semana/feriados).
    start = prediction_date - timedelta(days=150)
    df = _download(ticker, start.isoformat(), prediction_date.isoformat())

    if df.empty or len(df) < window:
        raise InsufficientDataError(
            f"Não foi possível obter {window} pregões antes de "
            f"{prediction_date.isoformat()} (obtidos: {len(df)})."
        )

    window_df = df.tail(window).copy()
    window_df.index = pd.to_datetime(window_df.index)
    return window_df


def load_real_close(ticker: str, prediction_date: date) -> Optional[float]:
    """Retorna o fechamento real de `prediction_date`, ou None se não houve pregão.

    Só faz sentido para datas passadas; para datas futuras retorna None.
    """
    if prediction_date > date.today():
        return None

    end = prediction_date + timedelta(days=1)
    df = _download(ticker, prediction_date.isoformat(), end.isoformat())
    if df.empty:
        return None

    target = pd.Timestamp(prediction_date)
    for idx in df.index:
        if pd.Timestamp(idx).normalize() == target:
            return float(df.loc[idx, "Close"])
    return None
