from sqlalchemy import Column, Integer, String, ForeignKey, Float
from NhaKhoa.models.base import Base
from sqlalchemy.orm import relationship

class MedicineType(Base):
    __tablename__ = "medicine_types"
    __table_args__ = {"extend_existing": True}


