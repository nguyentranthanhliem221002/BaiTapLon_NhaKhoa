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
#     address = Column(String(255), nullable=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
from email.policy import default

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models import user

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"extend_existing": True}
    age = Column(Integer, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255))
    user_id = Column(Integer, ForeignKey('users.id'), default=2)

    appointments = relationship("Appointment", back_populates="patient", lazy=True)
    user = relationship('User', back_populates='patient')
