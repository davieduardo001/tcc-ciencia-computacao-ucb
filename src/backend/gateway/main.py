from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from gateway.routes import router as gateway_router
from gateway.middleware import AutenticacaoMiddleware

settings = get_settings()

app = FastAPI(
    title="Movecity — API Gateway",
    description="Ponto único de entrada — proxy para todos os serviços backend",
    version="0.1.0",
)

# Ordem importa: o Starlette executa o último middleware adicionado
# primeiro na entrada da requisição (é o mais "externo" da pilha).
# CORSMiddleware precisa ser o último adicionado (mais externo) pra:
#   1. Responder o preflight OPTIONS sem passar pelo AutenticacaoMiddleware
#      — preflight nunca carrega cookie, então caía em 401 antes do CORS
#      rodar, e o navegador nunca via a resposta real (só "erro de CORS").
#   2. Anexar Access-Control-Allow-Origin em QUALQUER resposta, inclusive
#      401 do AutenticacaoMiddleware — sem isso, todo 401 de rota
#      protegida (sessão expirada, sem cookie, etc.) virava "bloqueado
#      por CORS" no navegador em vez de um 401 normal que o front trata.
app.add_middleware(AutenticacaoMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gateway_router, prefix="/api", tags=["api"])


@app.get("/")
def root():
    return {"message": "Movecity — API Gateway"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway", "environment": settings.ENVIRONMENT}
