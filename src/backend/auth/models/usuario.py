import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    lgpd_accepted_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
