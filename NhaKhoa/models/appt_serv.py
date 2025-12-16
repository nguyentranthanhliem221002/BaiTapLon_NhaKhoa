# from sqlalchemy import Column, Integer, ForeignKey
#
# from NhaKhoa.models.base import Base
#
#
# class Appointment_Service(Base):
#     __tablename__ = "appointment_services"
#     __table_args__ = {"extend_existing": True}
#
#     appt_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
#     service_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)