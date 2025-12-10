from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = {"extend_existing": True}

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    description = Column(String(255), default="")

    patient = relationship("Patient", back_populates="appointments")
    schedule = relationship("Schedule", back_populates="appointments")
    bills = relationship("Bill", back_populates="appointment")
