# NhaKhoa/models/schedule.py
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base

class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"extend_existing": True}

    name = Column(String(100), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    from_date = Column(DateTime, nullable=False)
    to_date = Column(DateTime, nullable=False)
    num_patient = Column(Integer, default=0)
    max_patient = Column(Integer, default=10)

    # Relationships
    doctor = relationship("Doctor", back_populates="schedules")
    appointments = relationship("Appointment", back_populates="schedule")
