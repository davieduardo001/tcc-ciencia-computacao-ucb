from sqlalchemy import Column, Integer, String
from models.base import Base


class TestReporte(Base):
    __tablename__ = "test_reporte"

    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="pendente")
