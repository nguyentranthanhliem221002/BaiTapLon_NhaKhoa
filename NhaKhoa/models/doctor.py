from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.database.db import Base
from NhaKhoa.models.role import RoleEnum

class Doctor(Base):
    __tablename__ = "doctors"
    __table_args__ = {"extend_existing": True}

    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    image = Column(String(200), default="")  # thêm cột lưu tên file ảnh
    specialty_id = Column(Integer, ForeignKey("specialties.id"), default=1)
    user_id = Column(Integer, ForeignKey('users.id'), default=2)
    role_id = Column(Integer, ForeignKey("roles.id"), default=RoleEnum.DOCTOR.value) #2. doctor

    schedules = relationship("Schedule", back_populates="doctor")
    user = relationship('User', back_populates='doctor', uselist=False)
    role = relationship('Role', back_populates='doctors', lazy=True)
    specialty = relationship('Specialty', back_populates='doctors', lazy=True)