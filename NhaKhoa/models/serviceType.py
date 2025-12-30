from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models.specialty import Specialty

class ServiceType(Base):
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    specialty_id = Column(Integer, ForeignKey('specialty.id'))
    specialty = relationship("Specialty", back_populates="service_types")
    status = Column(Integer, default=0)
    services = relationship('Service', back_populates='service_type')

    def __repr__(self):
        return f"<ServiceType {self.name}>"