# class ServiceType:
#     def __init__(self, id=None, name=""):
#         self.id = id
#         self.name = name
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base

class ServiceType(Base):
    __tablename__ = "service_types"

    services = relationship('Service', back_populates='service_type', lazy=True)
