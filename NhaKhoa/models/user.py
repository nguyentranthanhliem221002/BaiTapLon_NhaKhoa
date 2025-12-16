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
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models.role import RoleEnum

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), default=RoleEnum.USER.value)

    doctor = relationship("Doctor", back_populates="user", uselist=False)
    patient = relationship("Patient", back_populates="user", uselist=False)
    role = relationship('Role', back_populates='users', lazy=True)
