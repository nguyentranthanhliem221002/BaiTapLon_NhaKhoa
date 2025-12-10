# NhaKhoa/database/db.py
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text, select, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager
import pymysql
import bcrypt

from NhaKhoa import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_CHARSET, SQLALCHEMY_DATABASE_URI, data
from NhaKhoa.models.base import Base
from NhaKhoa.models.role import RoleEnum, Role
from NhaKhoa.models.schedule import Schedule
from NhaKhoa.models.specialty import Specialty

# ==============================
# TẠO DATABASE NẾU CHƯA CÓ
temp_engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/", future=True)
with temp_engine.connect() as conn:
    conn.execute(text(
        f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
        f"CHARACTER SET {DB_CHARSET} COLLATE {DB_CHARSET}_unicode_ci"
    ))
    conn.commit()

# ==============================
# ENGINE CHÍNH + SESSION

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


# ==============================
# IMPORT MODEL
from NhaKhoa.models.user import User
from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.patient import Patient
from NhaKhoa.models.appointment import Appointment
from NhaKhoa.models.bill import Bill
from NhaKhoa.models.serviceType import ServiceType
from NhaKhoa.models.service import Service
from NhaKhoa.models.medicineType import MedicineType
from NhaKhoa.models.medicine import Medicine

# ==============================
# CONTEXT MANAGER CHO SESSION
@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# ==============================
# KHỞI TẠO DATABASE + SEED DATA
def init_database():
    Base.metadata.create_all(bind=engine)

    with get_session() as db:
        # --- Roles ---
        if db.scalar(select(func.count()).select_from(Role)) == 0:
            db.add_all([
                Role(name="user", description="Regular user"),
                Role(name="patient", description="Patient"),
                Role(name="doctor", description="Doctor"),
                Role(name="admin", description="Administrator")
            ])
            db.commit()
        # --- Users ---
        if db.scalar(select(func.count()).select_from(User)) == 0: #this line error
            users = [
                ("admin", "admin@example.com", "admin123", RoleEnum.ADMIN.value),
                ("doctor", "doctor@example.com", "123456", RoleEnum.DOCTOR.value),
                ("patient", "patient@example.com", "123456", RoleEnum.PATIENT.value)
            ]
            for name, email, pwd, role in users:
                hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
                db.add(User(name=name, email=email, password=hashed, role_id=role))
            db.commit()

        # --- Specialties ---
        if db.scalar(select(func.count()).select_from(Specialty)) == 0:
            doctor_user = db.scalar(select(User).where(User.role_id == RoleEnum.DOCTOR.value))
            if doctor_user:
                db.add_all([
                    Specialty(name="Khám tổng quát", description="Khám sức khỏe tổng quát"),
                    Specialty(name="Nha khoa thẩm mỹ", description="Chuyên về thẩm mỹ răng miệng")
                ])
                db.commit()

        # --- Doctors ---
        if db.scalar(select(func.count()).select_from(Doctor)) == 0:
            doctor_user = db.scalar(select(User).where(User.role_id == RoleEnum.DOCTOR.value))
            db.add_all([
                Doctor(name="Nguyen Van Nam", specialty_id=1, phone="0901123456"),
                Doctor(name="Nguyen Van Hoa", specialty_id=2, phone="0902876543")
            ])
            db.commit()

        # --- Patients ---
        if db.scalar(select(func.count()).select_from(Patient)) == 0:
            patient_user = db.scalar(select(User).where(User.role_id == RoleEnum.PATIENT.value))
            db.add_all([
                Patient(name="Nguyen Van A", age=25, phone="0901123456", address="Ha Noi"),
                Patient(name="Tran Thi B", age=30, phone="0902987654", address="Da Nang")
            ])
            db.commit()

        # --- Service Types ---
        if db.scalar(select(func.count()).select_from(ServiceType)) == 0:
            db.add_all([
                ServiceType(name="Khám răng"),
                ServiceType(name="Nha khoa thẩm mỹ")
            ])
            db.commit()

        # --- Services ---
        if db.scalar(select(func.count()).select_from(Service)) == 0:
            db.add_all([
                Service(name="Trám răng", service_type_id=1, price=150000),
                Service(name="Tẩy trắng răng", service_type_id=2, price=500000)
            ])
            db.commit()

        # --- Medicine Types ---
        if db.scalar(select(func.count()).select_from(MedicineType)) == 0:
            db.add_all([
                MedicineType(name="Thuốc giảm đau"),
                MedicineType(name="Thuốc kháng sinh")
            ])
            db.commit()

        # --- Medicines ---
        if db.scalar(select(func.count()).select_from(Medicine)) == 0:
            db.add_all([
                Medicine(name="Paracetamol", medicine_type_id=1, price=2000),
                Medicine(name="Amoxicillin", medicine_type_id=2, price=5000)
            ])
            db.commit()

        # --- Schedules ---
        if db.scalar(select(func.count()).select_from(Schedule)) == 0:
            # Get doctors
            dr_nam = db.scalar(select(Doctor).where(Doctor.name == "Nguyen Van Nam"))
            dr_hoa = db.scalar(select(Doctor).where(Doctor.name == "Nguyen Van Hoa"))

            # Define a function to create schedules for a doctor
            def create_schedules_for_doctor(doctor, start_hour=9, end_hour=17):
                schedules = []
                now = datetime.now()
                for day in range(7):  # Create schedules for the next 7 days
                    date = now + timedelta(days=day)
                    for hour in range(start_hour, end_hour):
                        from_date = datetime(date.year, date.month, date.day, hour, 0)
                        to_date = datetime(date.year, date.month, date.day, hour + 1, 0)
                        if from_date.hour == 12:
                            continue
                        else:
                            schedules.append(Schedule(
                                name=f'Lịch hẹn với bác sĩ {doctor.name}',
                                doctor_id=doctor.id,
                                from_date=from_date,
                                to_date=to_date
                            ))
                return schedules

            # Create schedules for Dr. Nam and Dr. Hoa
            schedules = []
            schedules.extend(create_schedules_for_doctor(dr_nam))
            schedules.extend(create_schedules_for_doctor(dr_hoa))

            db.add_all(schedules)
            db.commit()

    print(">>> ✓ Database & Tables ready with seed data!")

# ==============================
# KẾT NỐI THỦ CÔNG (pymysql) CHO DAO CŨ
def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

