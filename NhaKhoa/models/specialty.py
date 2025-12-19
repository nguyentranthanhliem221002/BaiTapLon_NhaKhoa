from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from NhaKhoa.models.base import Base  # giả sử bạn dùng Base từ đây

class Specialty(Base):
    __tablename__ = "specialty"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), default="")

    doctors = relationship("Doctor", back_populates="specialty")

    service_types = relationship("ServiceType", back_populates="specialty")

    def __repr__(self):
        return f"<Specialty {self.name}>"