from sqlalchemy import Column, Float, String, DateTime, Uuid, func
from models.base import Base
import uuid


class AlertaAtraso(Base):
    __tablename__ = "alertas"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    usuario_id = Column(Uuid, nullable=False, index=True)
    linha_id = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="ativo")
    atraso_inicio_minutos = Column(Float, nullable=False)
    ultimo_atraso_notificado = Column(Float, nullable=True)
    ultimo_alerta_enviado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=func.now())
    cancelado_em = Column(DateTime, nullable=True)
