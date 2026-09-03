import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base

from auth.models.usuario import Usuario  # noqa: F401 — garante tabela 'usuarios' no metadata


class TokenResetSenha(Base):
    __tablename__ = "tokens_reset_senha"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    criado_em = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expira_em = Column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def criar_novo(usuario_id: uuid.UUID, ttl_minutos: int = 60) -> "TokenResetSenha":
        token = uuid.uuid4().hex
        agora = datetime.now(timezone.utc)
        return TokenResetSenha(
            usuario_id=usuario_id,
            token=token,
            usado=False,
            criado_em=agora,
            expira_em=agora + timedelta(minutes=ttl_minutos),
        )

    @property
    def expirado(self) -> bool:
        return datetime.now(timezone.utc) > self.expira_em

    @property
    def valido(self) -> bool:
        return not self.usado and not self.expirado
