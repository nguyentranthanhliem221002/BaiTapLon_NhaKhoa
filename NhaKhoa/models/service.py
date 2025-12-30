from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base
from NhaKhoa.models import serviceType

class Service(Base):
    __tablename__ = "services"

    name = Column(String(100), nullable=False)
    service_type_id = Column(Integer, ForeignKey('service_types.id'))
    price = Column(Float, nullable=False)
    status = Column(Integer, default=0)

    service_type = relationship('ServiceType', back_populates='services', lazy=True)
    bill_services = relationship("BillService", back_populates="service")
