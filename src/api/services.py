import logging
from typing import List

import numpy as np
import torch

from src.api.model_loader import WINDOW_SIZE, ModelBundle

logger = logging.getLogger("api.services")


class ModelNotLoadedError(RuntimeError):
    pass


class InvalidPricesError(ValueError):
    pass


def validate_prices(prices: List[float]) -> None:
    if len(prices) != WINDOW_SIZE:
        raise InvalidPricesError(
            f"O campo 'prices' deve conter exatamente {WINDOW_SIZE} valores numéricos."
        )
    if any(price <= 0 for price in prices):
        raise InvalidPricesError("Todos os valores em 'prices' devem ser maiores que zero.")


def predict_next_price(model_bundle: ModelBundle, prices: List[float]) -> float:
    validate_prices(prices)

    if not model_bundle.is_loaded:
        raise ModelNotLoadedError("Modelo não está carregado.")

    prices_array = np.array(prices, dtype=np.float32).reshape(-1, 1)
    normalized_prices = model_bundle.scaler.transform(prices_array)

    input_tensor = torch.tensor(normalized_prices, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        prediction = model_bundle.model(input_tensor).numpy()

    unnormalized_prediction = model_bundle.scaler.inverse_transform(prediction)

    return float(unnormalized_prediction[0][0])
