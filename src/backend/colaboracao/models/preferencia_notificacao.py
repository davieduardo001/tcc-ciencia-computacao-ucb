import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base


class PreferenciaNotificacao(Base):
    __tablename__ = "preferencias_notificacao"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # O ORM não declara ForeignKey para usuarios.id (mesmo padrão de Ocorrencia
    # e RotaFavorita): cada serviço sobe isolado e o serviço de colaboração não
    # carrega o modelo Usuario do Auth. Com a FK no ORM, a tabela "usuarios"
    # não existia no metadata do processo e o flush levantava
    # NoReferencedTableError (500 em produção). A FK real continua no banco,
    # criada pela migration b2c3d4e5f6a7 — o banco garante a integridade e o
    # autogenerate do Alembic não deve ser usado pra "corrigir" a diferença.
    usuario_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
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
