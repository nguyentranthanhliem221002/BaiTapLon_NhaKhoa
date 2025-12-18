from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship

from NhaKhoa.models.base import Base


class BillService(Base):
    __tablename__ = "bill_services"
    __table_args__ = {"extend_existing": True}

    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    price = Column(Float, default=0)

    bill = relationship("Bill", back_populates="bill_services")
    service = relationship("Service", back_populates="bill_services")

