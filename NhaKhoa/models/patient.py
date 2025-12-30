from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models.role import RoleEnum


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"extend_existing": True}

    name = Column(String(100), nullable=False)
    age = Column(Integer, default=999)
    phone = Column(String(20), default="")
    address = Column(String(255), default="")
    image = Column(String(255), default="")
    user_id = Column(Integer, ForeignKey('users.id'), default=3)
    role_id = Column(Integer, ForeignKey("roles.id"), default=RoleEnum.PATIENT.value)
    status = Column(Integer, default=0)

    appointments = relationship("Appointment", back_populates="patient", lazy=True)
    user = relationship('User', back_populates='patient')
    role = relationship('Role', back_populates='patients', lazy=True)

