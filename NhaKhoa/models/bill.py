from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base

class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = {"extend_existing": True}

    name = Column(String(100), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    amount = Column(Integer, default=0)
    status = Column(String(50), default="Chưa thanh toán")
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True)

    appointment = relationship("Appointment", back_populates="bills")
