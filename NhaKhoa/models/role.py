from enum import Enum

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from NhaKhoa.models.base import Base


class RoleEnum(Enum):
    USER = 1
    PATIENT = 2
    DOCTOR = 3
    ADMIN = 4


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))

    users = relationship('User', back_populates='role', lazy=True)
    patients = relationship('Patient', back_populates='role', lazy=True)
    doctors = relationship('Doctor', back_populates='role', lazy=True)