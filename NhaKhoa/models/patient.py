# from sqlalchemy import Column, Integer, String, ForeignKey
# from NhaKhoa.database.db import Base
#
# class Patient(Base):
#     __tablename__ = "patients"
#     __table_args__ = {"extend_existing": True}
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(100), nullable=False)
#     age = Column(Integer, nullable=False)
#     phone = Column(String(20), nullable=False)
#     address = Column(String(255))
#     user_id = Column(Integer, ForeignKey("users.id"))
#
#     user = relationship("User", back_populates="patients")
#     appointments = relationship("Appointment", back_populates="patient")
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models.role import RoleEnum


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"extend_existing": True}
    age = Column(Integer, default=999)
    phone = Column(String(20), default="")
    address = Column(String(255), default="")
    image = Column(String(255), default="")  # Thêm cột lưu đường dẫn ảnh
    user_id = Column(Integer, ForeignKey('users.id'), default=3) # theo db.py
    role_id = Column(Integer, ForeignKey("roles.id"), default=RoleEnum.PATIENT.value)

    appointments = relationship("Appointment", back_populates="patient", lazy=True)
    user = relationship('User', back_populates='patient')
    role = relationship('Role', back_populates='patients', lazy=True)

