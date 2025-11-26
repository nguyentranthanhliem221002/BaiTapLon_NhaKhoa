from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from NhaKhoa import db, app
from datetime import datetime


class Abstract(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now)

class User(db.Model):
    __tablename__ = 'users'


    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    address = Column(String(255), nullable=True)
    image = Column(String(255), nullable=True)
    day_of_birth = Column(DateTime, nullable=False)
    full_name = Column(String(255), nullable=False)


class Doctor(User):
    __tablename__ = 'doctors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    phone = Column(String(20))

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    description = Column(Text)

    patient = relationship("Patient", backref="appointments")
    doctor = relationship("Doctor", backref="appointments")

class ServiceType(db.Model):
    __tablename__ = 'service_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

class Service(db.Model):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    service_type_id = Column(Integer, ForeignKey('service_types.id'), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)

    service_type = relationship("ServiceType", backref="services")

class MedicineType(db.Model):
    __tablename__ = 'medicine_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    medicine_type_id = Column(Integer, ForeignKey('medicine_types.id'), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)

    medicine_type = relationship("MedicineType", backref="medicines")
