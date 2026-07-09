FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
RUN mkdir -p models
COPY ai_model_petr4.pth models/ai_model_petr4.pth
COPY scaler_petr4.pkl models/scaler_petr4.pkl

ENV MODEL_PATH=models/ai_model_petr4.pth \
    SCALER_PATH=models/scaler_petr4.pkl \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.api.main:app --host ${HOST} --port ${PORT}"]
