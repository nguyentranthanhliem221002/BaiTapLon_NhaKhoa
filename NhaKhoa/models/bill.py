from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.database.db import Base

class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    amount = Column(Integer, default=0)
    status = Column(String(50), default="Chưa thanh toán")
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True)

    appointment = relationship("NhaKhoa.models.appointment.Appointment", back_populates="bills")
