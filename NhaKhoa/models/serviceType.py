# class ServiceType:
#     def __init__(self, id=None, name=""):
#         self.id = id
#         self.name = name
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from NhaKhoa.database.db import Base

class ServiceType(Base):
    __tablename__ = "service_types"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    services = relationship("Service", back_populates="service_type")
