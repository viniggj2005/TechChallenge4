import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.model_loader import model_bundle
from src.api.schemas import HealthResponse, PredictRequest, PredictResponse
from src.api.services import InvalidPricesError, ModelNotLoadedError, predict_next_price

APP_NAME = os.getenv("APP_NAME", "lstm-stock-api")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("api.main")

app = FastAPI(
    title=APP_NAME,
    description="API para inferência de um modelo LSTM treinado para previsão do preço de fechamento de ações.",
    version=APP_VERSION,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
def load_model() -> None:
    try:
        model_bundle.load()
    except Exception:
        logger.exception("Falha ao carregar o modelo na inicialização da API.")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Erro de validação na requisição %s: %s", request.url, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", model_loaded=model_bundle.is_loaded)


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    try:
        prediction = predict_next_price(model_bundle, payload.prices)
    except InvalidPricesError as exc:
        logger.warning("Requisição de previsão rejeitada: %s", exc)
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except ModelNotLoadedError as exc:
        logger.error("Tentativa de previsão sem modelo carregado: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Modelo indisponível no momento. Tente novamente mais tarde."},
        )
    except Exception:
        logger.exception("Erro inesperado durante a inferência do modelo.")
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno ao processar a previsão."},
        )

    return PredictResponse(prediction=prediction)
