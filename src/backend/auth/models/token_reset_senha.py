import hashlib
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base


class TokenResetSenha(Base):
    """
    Armazena apenas o hash SHA-256 do token de reset — nunca o valor em claro.
    Assim, um vazamento do banco não expõe tokens válidos utilizáveis para
    redefinir senhas (mesmo princípio aplicado ao hash de senha do usuário).
    """

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
    def hash_token(token_plano: str) -> str:
        return hashlib.sha256(token_plano.encode("utf-8")).hexdigest()

    @classmethod
    def criar_novo(
        cls, usuario_id: uuid.UUID, ttl_minutos: int = 60
    ) -> tuple["TokenResetSenha", str]:
        """Retorna (instancia_para_persistir, token_em_claro_para_enviar_por_email)."""
        token_plano = uuid.uuid4().hex
        agora = datetime.now(timezone.utc)
        instancia = cls(
            usuario_id=usuario_id,
            token=cls.hash_token(token_plano),
            usado=False,
            criado_em=agora,
            expira_em=agora + timedelta(minutes=ttl_minutos),
        )
        return instancia, token_plano

    @property
    def expirado(self) -> bool:
        return datetime.now(timezone.utc) > self.expira_em

    @property
    def valido(self) -> bool:
        return not self.usado and not self.expirado
