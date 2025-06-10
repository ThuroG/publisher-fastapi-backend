from .database import Base
from sqlalchemy import Column, Integer, String, Boolean

class Post(Base):
    __tablename__ = 'postsorm'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    title = Column(String, nullable=False) 
    content=  Column(String, nullable=False)
    rating =  Column(Integer, nullable=True)
    published = Column(Boolean, default=False)

