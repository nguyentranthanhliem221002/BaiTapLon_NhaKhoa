from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from NhaKhoa.models.base import Base


class Specialty(Base):
    __tablename__ = "specialties"
    __table_args__ = {"extend_existing": True}

    name = Column(String(100), nullable=False)
    description = Column(String(255), default="")

    doctors = relationship("Doctor", back_populates="specialty")