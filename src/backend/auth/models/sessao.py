import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base


class Sessao(Base):
    __tablename__ = "sessao"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False)
    refresh_token_hash = Column(String(255), nullable=False)
    expira_em = Column(DateTime, nullable=False)
    revogado = Column(Boolean, default=False, nullable=False)
    user_agent = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
