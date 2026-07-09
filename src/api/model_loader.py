import logging
import os

import joblib
import torch
import torch.nn as nn

logger = logging.getLogger("api.model_loader")

MODEL_PATH = os.getenv("MODEL_PATH", "ai_model_petr4.pth")
SCALER_PATH = os.getenv("SCALER_PATH", "scaler_petr4.pkl")
WINDOW_SIZE = 60


class SharesPredictionModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=50, num_layers=2):
        super(SharesPredictionModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out


class ModelBundle:
    def __init__(self):
        self.model: SharesPredictionModel | None = None
        self.scaler = None

    @property
    def is_loaded(self) -> bool:
        return self.model is not None and self.scaler is not None

    def load(self) -> None:
        logger.info("Carregando modelo de %s e scaler de %s", MODEL_PATH, SCALER_PATH)
        model = SharesPredictionModel(input_size=1, hidden_size=50, num_layers=2)
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        model.eval()

        self.model = model
        self.scaler = joblib.load(SCALER_PATH)
        logger.info("Modelo e scaler carregados com sucesso.")


model_bundle = ModelBundle()
