# NhaKhoa/database/db.py
from sqlalchemy import create_engine, text, select, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager
import pymysql
import bcrypt

# ==============================
# CẤU HÌNH DATABASE
DB_USER = "root"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_NAME = "nha_khoa"
DB_CHARSET = "utf8mb4"

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
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset={DB_CHARSET}"
engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()

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
        # --- Users ---
        if db.scalar(select(func.count()).select_from(User)) == 0:
            users = [
                ("admin", "admin@example.com", "admin123", "admin"),
                ("doctor", "doctor@example.com", "123456", "doctor"),
                ("patient", "patient@example.com", "123456", "patient")
            ]
            for username, email, pwd, role in users:
                hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
                db.add(User(username=username, email=email, password=hashed, role=role))
            db.commit()

        # --- Doctors ---
        if db.scalar(select(func.count()).select_from(Doctor)) == 0:
            doctor_user = db.scalar(select(User).where(User.role == "doctor"))
            db.add_all([
                Doctor(name="Dr. Nam", specialty="Nha chu", phone="0901123456", user_id=doctor_user.id),
                Doctor(name="Dr. Hoa", specialty="Chỉnh nha", phone="0902876543", user_id=doctor_user.id)
            ])
            db.commit()

        # --- Patients ---
        if db.scalar(select(func.count()).select_from(Patient)) == 0:
            patient_user = db.scalar(select(User).where(User.role == "patient"))
            db.add_all([
                Patient(name="Nguyen Van A", age=25, phone="0901123456", address="Ha Noi", user_id=patient_user.id),
                Patient(name="Tran Thi B", age=30, phone="0902987654", address="Da Nang", user_id=patient_user.id)
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
