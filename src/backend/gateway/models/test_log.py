from sqlalchemy import Column, Integer, String
from models.base import Base


class TestLog(Base):
    __tablename__ = "test_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False)
