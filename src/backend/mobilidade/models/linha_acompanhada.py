from sqlalchemy import Column, Integer, String, DateTime, Uuid, func
from models.base import Base
import uuid


class LinhaAcompanhada(Base):
    __tablename__ = "linhas_acompanhadas"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    usuario_id = Column(Uuid, nullable=False, index=True)
    linha_id = Column(String(20), nullable=False, index=True)
    criado_em = Column(DateTime, default=func.now())
    ativo = Column(Integer, default=1)
