# Build a partir da raiz do repositório:
#   flyctl deploy --config src/backend/mobilidade/fly.toml --dockerfile src/backend/mobilidade/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/backend/mobilidade/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend/shared ./shared
COPY src/backend/mobilidade ./mobilidade

EXPOSE 8000

CMD ["uvicorn", "mobilidade.main:app", "--host", "0.0.0.0", "--port", "8000"]
