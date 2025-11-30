from sqlalchemy import Column, Integer, String, ForeignKey, Float
from NhaKhoa.database.db import Base
from sqlalchemy.orm import relationship

class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    medicine_type_id = Column(Integer, ForeignKey("medicine_types.id"))
    price = Column(Float, nullable=False)

    medicine_type = relationship("MedicineType", back_populates="medicines")