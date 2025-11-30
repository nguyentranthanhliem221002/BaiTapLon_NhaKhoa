from sqlalchemy import Column, Integer, String, ForeignKey, Float
from NhaKhoa.database.db import Base
from sqlalchemy.orm import relationship

class MedicineType(Base):
    __tablename__ = "medicine_types"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    medicines = relationship("Medicine", back_populates="medicine_type")
