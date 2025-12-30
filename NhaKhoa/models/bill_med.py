from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship

from NhaKhoa.models.base import Base


class BillMedicine(Base):
    __tablename__ = "bill_medicines"
    __table_args__ = {"extend_existing": True}

    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0)

    bill = relationship("Bill", back_populates="bill_medicines")
    medicine = relationship("Medicine", back_populates="bill_medicines")