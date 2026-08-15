from sqlalchemy import Column, Integer, String
from models.base import Base


class TestLinha(Base):
    __tablename__ = "test_linha"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(10), unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
