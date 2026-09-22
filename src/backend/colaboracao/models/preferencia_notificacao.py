import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base


class PreferenciaNotificacao(Base):
    __tablename__ = "preferencias_notificacao"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False)
    antecedencia_minutos = Column(Integer, nullable=False, default=30)
    notificacoes_ativas = Column(Boolean, nullable=False, default=True)
    alerta_chegada = Column(Boolean, nullable=False, default=True)
    alerta_cancelamento = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    atualizado_em = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    ANTECEDENCIAS_PERMITIDAS = [5, 10, 30, 60]

    @property
    def antecedencia_valida(self) -> bool:
        return self.antecedencia_minutos in self.ANTECEDENCIAS_PERMITIDAS
