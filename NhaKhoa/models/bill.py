from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models.bill_med import BillMedicine
from NhaKhoa.models.bill_serv import BillService


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = {"extend_existing": True}

    name = Column(String(100), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    total = Column(Float, default=0)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False)

    status = relationship("Status", back_populates="bills")
    appointment = relationship("Appointment", back_populates="bill", uselist=False)
    bill_services = relationship(BillService, back_populates="bill")
    bill_medicines = relationship(BillMedicine, back_populates="bill")
