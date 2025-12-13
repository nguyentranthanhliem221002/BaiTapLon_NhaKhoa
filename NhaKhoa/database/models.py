from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, DateTime, Text
from sqlalchemy.orm import relationship
from NhaKhoa import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True)
    password = Column(String(255))
    role = Column(String(20), default="patient")
    email = Column(String(255), unique=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    age = Column(Integer)
    phone = Column(String(20))
    address = Column(String(255))
    userId = Column(String(255), nullable=True)


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    specialty = Column(String(255))
    phone = Column(String(20))
    userId = Column(String(255), nullable=True)


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    appointment_date = Column(DateTime)
    description = Column(Text, default="")

    patient = relationship("Patient")
    doctor = relationship("Doctor")


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    amount = Column(DECIMAL(10, 2))
    status = Column(String(50), default="Chưa thanh toán")
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    appointment = relationship("Appointment")


class ServiceType(Base):
    __tablename__ = "service_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    service_type_id = Column(Integer, ForeignKey("service_types.id"))
    price = Column(DECIMAL(10, 2))

    service_type = relationship("ServiceType")


class MedicineType(Base):
    __tablename__ = "medicine_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)


class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    medicine_type_id = Column(Integer, ForeignKey("medicine_types.id"))
    price = Column(DECIMAL(10, 2))

    medicine_type = relationship("MedicineType")
