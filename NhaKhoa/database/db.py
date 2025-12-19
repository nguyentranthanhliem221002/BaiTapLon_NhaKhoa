# NhaKhoa/database/db.py
from datetime import datetime, timedelta
from contextlib import contextmanager

from sqlalchemy import create_engine, text, select, func
from sqlalchemy.orm import sessionmaker, Session

import pymysql
import bcrypt

from NhaKhoa import (
    DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_CHARSET,
    SQLALCHEMY_DATABASE_URI
)

from NhaKhoa.models.base import Base
from NhaKhoa.models.role import RoleEnum, Role
from NhaKhoa.models.status import StatusEnum, Status
from NhaKhoa.models.specialty import Specialty
from NhaKhoa.models.user import User
from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.patient import Patient
from NhaKhoa.models.serviceType import ServiceType
from NhaKhoa.models.service import Service
from NhaKhoa.models.medicineType import MedicineType
from NhaKhoa.models.medicine import Medicine
from NhaKhoa.models.schedule import Schedule


# =====================================================
# TẠO DATABASE NẾU CHƯA CÓ
# =====================================================
temp_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/",
    future=True
)

with temp_engine.connect() as conn:
    conn.execute(text(
        f"""
        CREATE DATABASE IF NOT EXISTS {DB_NAME}
        CHARACTER SET {DB_CHARSET}
        COLLATE {DB_CHARSET}_unicode_ci
        """
    ))
    conn.commit()


# =====================================================
# ENGINE CHÍNH + SESSION
# =====================================================
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# =====================================================
# KHỞI TẠO DATABASE + SEED DATA
# =====================================================
def init_database():
    Base.metadata.create_all(bind=engine)

    with get_session() as db:

        # =====================
        # ROLES
        # =====================
        if db.scalar(select(func.count(Role.id))) == 0:
            db.add_all([
                Role(name="user", description="Regular user"),
                Role(name="patient", description="Patient"),
                Role(name="doctor", description="Doctor"),
                Role(name="admin", description="Administrator"),
            ])
            db.commit()

        # =====================
        # STATUSES
        # =====================
        if db.scalar(select(func.count(Status.id))) == 0:
            db.add_all([
                Status(name=s.value, description=f"Trạng thái: {s.value}")
                for s in StatusEnum
            ])
            db.commit()

        # =====================
        # ADMIN USER (RIÊNG)
        # =====================
        if db.scalar(
            select(func.count(User.id))
            .where(User.role_id == RoleEnum.ADMIN.value)
        ) == 0:
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            db.add(User(
                name="Admin",
                email="admin@example.com",
                password=hashed,
                role_id=RoleEnum.ADMIN.value
            ))
            db.commit()

        # =====================
        # SPECIALTIES
        # =====================
        if db.scalar(select(func.count(Specialty.id))) == 0:
            db.add_all([
                Specialty(name="Khám tổng quát", description="Khám sức khỏe răng miệng tổng quát"),
                Specialty(name="Nha khoa thẩm mỹ", description="Tẩy trắng, dán sứ, niềng răng"),
                Specialty(name="Chỉnh nha", description="Niềng răng, chỉnh hình"),
                Specialty(name="Nha chu", description="Điều trị nha chu"),
                Specialty(name="Implant", description="Trồng răng Implant"),
                Specialty(name="Nội nha", description="Điều trị tủy"),
            ])
            db.commit()

        specialties = db.scalars(select(Specialty).order_by(Specialty.id)).all()

        # =====================
        # DOCTORS + USERS
        # =====================
        if db.scalar(select(func.count(Doctor.id))) == 0:
            doctors = [
                ("doctor1", "doctor1@example.com", "0901123456", specialties[0].id),
                ("doctor2", "doctor2@example.com", "0902876543", specialties[1].id),
                ("doctor3", "doctor3@example.com", "0912345678", specialties[2].id),
            ]

            for name, email, phone, specialty_id in doctors:
                hashed = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()

                user = User(
                    name=name,
                    email=email,
                    password=hashed,
                    role_id=RoleEnum.DOCTOR.value
                )
                db.add(user)
                db.flush()  # lấy user.id

                db.add(Doctor(
                    name=name,
                    phone=phone,
                    specialty_id=specialty_id,
                    user_id=user.id
                ))

            db.commit()

        # =====================
        # PATIENTS + USERS
        # =====================
        if db.scalar(select(func.count(Patient.id))) == 0:
            patients = [
                ("patient1", 28, "0903765432", "Hà Nội", "patient1@example.com"),
                ("patient2", 34, "0933876543", "Đà Nẵng", "patient2@example.com"),
                ("patient3", 22, "0977123456", "TP.HCM", "patient3@example.com"),
            ]

            for name, age, phone, address, email in patients:
                hashed = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()

                user = User(
                    name=name,
                    email=email,
                    password=hashed,
                    role_id=RoleEnum.PATIENT.value
                )
                db.add(user)
                db.flush()

                db.add(Patient(
                    name=name,
                    age=age,
                    phone=phone,
                    address=address,
                    user_id=user.id
                ))

            db.commit()

        # =====================
        # SERVICE TYPES
        # =====================
        if db.scalar(select(func.count(ServiceType.id))) == 0:
            db.add_all([
                ServiceType(name="Khám răng", specialty_id=specialties[0].id),
                ServiceType(name="Niềng răng", specialty_id=specialties[2].id),
                ServiceType(name="Tẩy trắng răng", specialty_id=specialties[1].id),
                ServiceType(name="Trồng Implant", specialty_id=specialties[4].id),
                ServiceType(name="Trám răng", specialty_id=specialties[3].id),
            ])
            db.commit()

        service_types = db.scalars(select(ServiceType).order_by(ServiceType.id)).all()

        # =====================
        # SERVICES
        # =====================
        if db.scalar(select(func.count(Service.id))) == 0:
            db.add_all([
                Service(name="Khám tổng quát", service_type_id=service_types[0].id, price=100000),
                Service(name="Cạo vôi răng", service_type_id=service_types[0].id, price=200000),
                Service(name="Niềng răng Invisalign", service_type_id=service_types[1].id, price=80000000),
                Service(name="Niềng răng mắc cài", service_type_id=service_types[1].id, price=35000000),
                Service(name="Tẩy trắng Zoom", service_type_id=service_types[2].id, price=5000000),
                Service(name="Implant Hàn Quốc", service_type_id=service_types[3].id, price=15000000),
                Service(name="Trám răng composite", service_type_id=service_types[4].id, price=500000),
            ])
            db.commit()

        # =====================
        # MEDICINE TYPES
        # =====================
        if db.scalar(select(func.count(MedicineType.id))) == 0:
            db.add_all([
                MedicineType(name="Thuốc giảm đau"),
                MedicineType(name="Thuốc kháng sinh"),
                MedicineType(name="Thuốc chống viêm"),
            ])
            db.commit()

        med_types = db.scalars(select(MedicineType).order_by(MedicineType.id)).all()

        # =====================
        # MEDICINES
        # =====================
        if db.scalar(select(func.count(Medicine.id))) == 0:
            db.add_all([
                Medicine(name="Paracetamol 500mg", medicine_type_id=med_types[0].id, price=2000),
                Medicine(name="Ibuprofen 400mg", medicine_type_id=med_types[0].id, price=5000),
                Medicine(name="Amoxicillin 500mg", medicine_type_id=med_types[1].id, price=8000),
                Medicine(name="Augmentin 1g", medicine_type_id=med_types[1].id, price=25000),
            ])
            db.commit()

        # =====================
        # SCHEDULES (LỊCH LÀM VIỆC)
        # =====================
        if db.scalar(select(func.count(Schedule.id))) == 0:
            doctors = db.scalars(select(Doctor)).all()
            now = datetime.now()

            for doctor in doctors:
                for day in range(14):
                    base_date = (now + timedelta(days=day)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    for hour in range(8, 17):
                        if hour == 12:
                            continue
                        from_time = base_date.replace(hour=hour)
                        to_time = from_time + timedelta(hours=1)

                        db.add(Schedule(
                            name=f"Lịch khám - {doctor.name}",
                            doctor_id=doctor.id,
                            from_date=from_time,
                            to_date=to_time
                        ))
            db.commit()

    print(">>> ✓ Database & Tables ready with seed data!")


# =====================================================
# RAW MYSQL CONNECTION (OPTIONAL)
# =====================================================
def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
