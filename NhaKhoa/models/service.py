# class Service:
#     def __init__(self, id=None, name="", service_type_id=None, price=0):
#         self.id = id
#         self.name = name
#         self.service_type_id = service_type_id
#         self.price = price
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from NhaKhoa.database.db import Base

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    service_type_id = Column(Integer, ForeignKey("service_types.id"))
    price = Column(Float, nullable=False)

    # Thêm relationship
    service_type = relationship("ServiceType", back_populates="services")
