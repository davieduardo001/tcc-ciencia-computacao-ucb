# Build a partir da raiz do repositório:
#   flyctl deploy --config src/backend/gateway/fly.toml --dockerfile src/backend/gateway/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/backend/gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend/models ./models
COPY src/backend/shared ./shared
COPY src/backend/gateway ./gateway

EXPOSE 8000

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
