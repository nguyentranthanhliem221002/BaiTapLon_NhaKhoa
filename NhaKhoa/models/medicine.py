from sqlalchemy import Column, Integer, String, ForeignKey, Float
from NhaKhoa.models.base import Base
from sqlalchemy.orm import relationship

class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = {"extend_existing": True}
    medicine_type_id = Column(Integer, ForeignKey("medicine_types.id"))
    price = Column(Float, nullable=False)

    medicine_type = relationship("MedicineType", back_populates="medicines")