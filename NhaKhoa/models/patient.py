# from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
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
from NhaKhoa.database.db import Base

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255))
    image = Column(String(255))  # Thêm cột lưu đường dẫn ảnh
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")

