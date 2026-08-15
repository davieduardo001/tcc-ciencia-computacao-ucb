# Build a partir da raiz do repositório:
#   flyctl deploy --config src/backend/auth/fly.toml --dockerfile src/backend/auth/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/backend/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend/shared ./shared
COPY src/backend/auth ./auth

EXPOSE 8000

CMD ["uvicorn", "auth.main:app", "--host", "0.0.0.0", "--port", "8000"]
