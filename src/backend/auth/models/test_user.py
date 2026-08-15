from sqlalchemy import Column, Integer, String
from models.base import Base


class TestUser(Base):
    __tablename__ = "test_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
