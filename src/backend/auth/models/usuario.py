from sqlalchemy import Column, String, DateTime, Uuid, func
from models.base import Base
import uuid


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    status = Column(String(50), default="ativo")
    tentativas_falhas = Column(Integer, default=0)
    bloqueado_ate = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=func.now())
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())