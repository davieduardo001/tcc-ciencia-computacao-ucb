# Build a partir da raiz do repositório:
#   flyctl deploy --config src/backend/colaboracao/fly.toml --dockerfile src/backend/colaboracao/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/backend/colaboracao/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend/shared ./shared
COPY src/backend/colaboracao ./colaboracao

EXPOSE 8000

CMD ["uvicorn", "colaboracao.main:app", "--host", "0.0.0.0", "--port", "8000"]
