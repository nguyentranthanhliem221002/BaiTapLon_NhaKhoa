#
# from sqlalchemy import Column, Integer, String, DateTime
# from NhaKhoa.database.db import Base
#
# class User(Base):
#     __tablename__ = "users"
#     __table_args__ = {"extend_existing": True}  # <--- thêm dòng này
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     username = Column(String(50), nullable=False, unique=True)
#     email = Column(String(100), nullable=False, unique=True)
#     password = Column(String(255), nullable=False)
#     role = Column(String(50), nullable=False, default="patient")
#     reset_token = Column(String(255), nullable=True)
#     reset_token_expiry = Column(DateTime, nullable=True)
#
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from NhaKhoa.database.db import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)

    doctors = relationship("Doctor", back_populates="user")
    patients = relationship("Patient", back_populates="user")
