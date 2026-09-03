from sqlalchemy import Column, String, DateTime, Uuid, Integer, func
from models.base import Base
import uuid


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    lgpd_accepted_at = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(String(50), default="ativo")
    tentativas_falhas = Column(Integer, default=0)
    bloqueado_ate = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())