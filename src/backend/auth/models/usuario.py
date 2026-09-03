from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from models.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hash_senha = Column(String(255), nullable=False)
    status = Column(String(50), default="ativo")
    tentativas_falhas = Column(Integer, default=0)
    bloqueado_ate = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=func.now())
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())
