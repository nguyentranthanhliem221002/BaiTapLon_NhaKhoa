from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from NhaKhoa.models.base import Base

class Status(Base):
    __tablename__ = "statuses"
    __table_args__ = {"extend_existing": True}

    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))

    # Relationship to Bill
    bills = relationship("Bill", back_populates="status")
