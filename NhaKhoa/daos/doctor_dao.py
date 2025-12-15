# from NhaKhoa.models.doctor import Doctor
# from NhaKhoa.database.db import get_session
#
# class DoctorDAO:
#     def get_all(self):
#         with get_session() as session:
#             return session.query(Doctor).all()
#
#     def get_by_id(self, id: int):
#         with get_session() as session:
#             return session.get(Doctor, id)
#
#     def add(self, doctor: Doctor):
#         with get_session() as session:
#             session.add(doctor)
#             session.commit()
#
#     def update(self, doctor: Doctor):
#         with get_session() as session:
#             session.add(doctor)
#             session.commit()
#
#     def delete(self, id: int):
#         with get_session() as session:
#             doctor = session.get(Doctor, id)
#             if doctor:
#                 session.delete(doctor)
#                 session.commit()
#
#     def search(self, filter_by: str, keyword: str):
#         with get_session() as session:
#             query = session.query(Doctor)
#             if filter_by == "name":
#                 query = query.filter(Doctor.name.ilike(f"%{keyword}%"))
#             elif filter_by == "specialty":
#                 query = query.filter(Doctor.specialty.ilike(f"%{keyword}%"))
#             elif filter_by == "phone":
#                 query = query.filter(Doctor.phone.ilike(f"%{keyword}%"))
#             return query.all()
#
#     def update(self, doctor: Doctor):
#         with get_session() as session:
#             session.merge(doctor)
#             session.commit()

from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.role import RoleEnum
from NhaKhoa.models.user import User
from NhaKhoa.database.db import get_session
import bcrypt
from datetime import datetime

class DoctorDAO:
    def get_all(self):
        with get_session() as session:
            return session.query(Doctor).all()

    def get_by_id(self, id: int):
        with get_session() as session:
            return session.get(Doctor, id)

    def add(self, doctor: Doctor):
        with get_session() as session:
            # Thêm bác sĩ
            session.add(doctor)
            session.commit()  # commit để bác sĩ có id

            # Tạo tài khoản User cho bác sĩ
            username = doctor.phone  # dùng số điện thoại làm username
            raw_password = "1"  # password mặc định
            hashed_password = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

            user = User(name=username, password=hashed_password, email="", role_id=RoleEnum.DOCTOR.value)
            session.add(user)
            session.commit()

    def update(self, doctor: Doctor):
        with get_session() as session:
            session.merge(doctor)
            session.commit()

    def delete(self, id: int):
        with get_session() as session:
            doctor = session.get(Doctor, id)
            if doctor:
                session.delete(doctor)
                session.commit()

    def search(self, filter_by: str, keyword: str):
        with get_session() as session:
            query = session.query(Doctor)
            if filter_by == "name":
                query = query.filter(Doctor.name.ilike(f"%{keyword}%"))
            elif filter_by == "specialty":
                query = query.filter(Doctor.specialty.ilike(f"%{keyword}%"))
            elif filter_by == "phone":
                query = query.filter(Doctor.phone.ilike(f"%{keyword}%"))
            return query.all()

    def get_doctors_by_specialty(self, specialty_id: int):
        """Get all doctors with the given specialty_id."""
        with get_session() as session:
            return session.query(Doctor).filter(Doctor.specialty_id == specialty_id).all()


