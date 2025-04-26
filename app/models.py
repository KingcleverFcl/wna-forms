from sqlalchemy import Column, Integer, String
from app.database import Base, engine

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String)
    total_forms = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)

class Form(Base):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True, index=True)
    creator = Column(String, index=True)
    total_questions = Column(Integer)
    total_answers = Column(Integer)
    link_form = Column(String, unique=True, index=True)
