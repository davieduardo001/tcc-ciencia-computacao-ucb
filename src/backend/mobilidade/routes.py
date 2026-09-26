from fastapi import APIRouter, Header, Depends
from sqlalchemy.orm import Session
import uuid

from shared.database import SessionLocal
from mobilidade.services.servico_rastreamento import ServicoRastreamento
from mobilidade.services.servico_notificacoes import NotificadorNulo
from mobilidade.providers.gtfs_mock import FornecedorGTFSMock

router = APIRouter()


def get_servico() -> ServicoRastreamento:
    return ServicoRastreamento(FornecedorGTFSMock(), NotificadorNulo())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/hello")
def hello():
    return {"service": "mobilidade", "status": "ok"}


@router.get("/teste-kelvin")
def teste_kelvin():
    return {"service": "mobilidade", "autor": "Kelvin963", "mensagem": "hello world"}


@router.get("/alertas")
def listar_alertas(
    servico: ServicoRastreamento = Depends(get_servico),
    usuario_id: str = Header(...),
    db: Session = Depends(get_db),
):
    uid = uuid.UUID(usuario_id)
    alertas = servico.listar_alertas(uid, db)
    return [
        {
            "id": str(a.id),
            "linha_id": a.linha_id,
            "status": a.status,
            "atraso_inicio_minutos": a.atraso_inicio_minutos,
            "ultimo_atraso_notificado": a.ultimo_atraso_notificado,
            "ultimo_alerta_enviado_em": a.ultimo_alerta_enviado_em,
            "criado_em": a.criado_em,
            "cancelado_em": a.cancelado_em,
        }
        for a in alertas
    ]


@router.get("/linhas-acompanhadas")
def listar_linhas_acompanhadas(
    servico: ServicoRastreamento = Depends(get_servico),
    usuario_id: str = Header(...),
    db: Session = Depends(get_db),
):
    uid = uuid.UUID(usuario_id)
    linhas = servico.listar_linhas_acompanhadas(uid, db)
    return [
        {
            "linha_id": l.linha_id,
            "criado_em": l.criado_em,
            "ativo": l.ativo,
        }
        for l in linhas
    ]