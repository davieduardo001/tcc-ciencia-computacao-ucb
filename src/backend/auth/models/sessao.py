from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import relationship
from models.base import Base


class Sessao(Base):
    __tablename__ = "sessoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Uuid, ForeignKey("usuarios.id"), nullable=False)
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    criado_em = Column(DateTime, default=func.now())

    usuario = relationship("Usuario", backref="sessoes")