from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, MetaData
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()

Base1 = declarative_base(metadata=metadata)

class Base(Base1):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    active = Column(Boolean, default=True)