#
# from sqlalchemy import Column, Integer, String, ForeignKey
# from NhaKhoa.database.db import Base
#
# class Doctor(Base):
#     __tablename__ = "doctors"
#     __table_args__ = {"extend_existing": True}
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(100), nullable=False)
#     specialty = Column(String(100), nullable=False)
#     phone = Column(String(20), nullable=False)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # liên kết User nếu cần
#
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models import user

class Doctor(Base):
    __tablename__ = "doctors"
    __table_args__ = {"extend_existing": True}

    specialty = Column(String(100))
    phone = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), default=1)

    appointments = relationship("Appointment", back_populates="doctor", lazy=True)
    user = relationship('User', back_populates='doctor', uselist=False)