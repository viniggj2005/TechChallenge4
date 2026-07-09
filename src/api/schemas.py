from typing import List

from pydantic import BaseModel, Field

WINDOW_SIZE = 60


class PredictRequest(BaseModel):
    prices: List[float] = Field(
        ..., description=f"Sequência com exatamente {WINDOW_SIZE} preços de fechamento históricos."
    )


class PredictResponse(BaseModel):
    prediction: float
    model: str = "LSTM"
    window_size: int = WINDOW_SIZE


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
