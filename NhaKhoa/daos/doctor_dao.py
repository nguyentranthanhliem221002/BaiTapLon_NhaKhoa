from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.specialty import Specialty
from NhaKhoa.database.db import get_session
from sqlalchemy.orm import joinedload

class DoctorDAO:
    def get_all(self):
        with get_session() as session:
            return session.query(Doctor) \
                .filter(Doctor.active == True) \
                .all()

    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(Doctor) \
                .filter(
                    Doctor.id == id,
                    Doctor.active == True
                ) \
                .first()

    def add(self, doctor: Doctor):
        with get_session() as session:
            session.add(doctor)
            session.commit()

            username = doctor.phone
            raw_password = "1"
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
                doctor.active = False
                session.commit()

    def search(self, filter_by: str, keyword: str):
        """
        Tìm kiếm bác sĩ theo filter_by và keyword.
        - Chỉ lấy bác sĩ active = True
        - Hỗ trợ tìm theo name, specialty (tên chuyên khoa), phone
        """
        with get_session() as session:
            query = session.query(Doctor) \
                .filter(Doctor.active == True)

            keyword = keyword.strip().lower()

            if filter_by == "name":
                query = query.filter(Doctor.name.ilike(f"%{keyword}%"))
            elif filter_by == "specialty":
                query = query.join(Specialty, Doctor.specialty_id == Specialty.id) \
                            .filter(Specialty.name.ilike(f"%{keyword}%"))
            elif filter_by == "phone":
                query = query.filter(Doctor.phone.ilike(f"%{keyword}%"))
            else:
                pass

            query = query.options(joinedload(Doctor.specialty))

            return query.all()

    def get_by_user_id(self, user_id: int):
        with get_session() as session:
            return session.query(Doctor) \
                .filter(
                    Doctor.user_id == user_id,
                    Doctor.active == True
                ) \
                .first()

    def get_doctors_by_specialty(self, specialty_id: int):
        with get_session() as session:
            return session.query(Doctor) \
                .filter(
                    Doctor.specialty_id == specialty_id,
                    Doctor.active == True
                ) \
                .all()



