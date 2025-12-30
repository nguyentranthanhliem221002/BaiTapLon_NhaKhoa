from NhaKhoa.models.patient import Patient
from NhaKhoa.models.role import RoleEnum
from NhaKhoa.models.user import User
from NhaKhoa.database.db import get_session
import bcrypt

class PatientDAO:
    def get_all(self):
        with get_session() as session:
            return session.query(Patient) \
                .filter(Patient.active == True) \
                .all()


    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(Patient) \
                .filter(
                Patient.id == id,
                Patient.active == True
            ).first()

    def add(self, patient: Patient):
        with get_session() as session:
            session.add(patient)
            session.commit()

            username = patient.phone
            raw_password = "1"
            hashed_password = bcrypt.hashpw(
                raw_password.encode(),
                bcrypt.gensalt()
            ).decode()

            user = User(
                name=username,
                password=hashed_password,
                email="",
                role_id=RoleEnum.PATIENT.value
            )

            session.add(user)
            session.commit()

            patient.user_id = user.id
            session.commit()

    def update(self, patient: Patient):
        with get_session() as session:
            session.merge(patient)
            session.commit()

    def delete(self, id: int):
        with get_session() as session:
            patient = session.get(Patient, id)
            if not patient:
                return

            patient.active = False
            session.commit()

    def search(self, filter_by: str, keyword: str):
        with get_session() as session:
            query = session.query(Patient) \
                .filter(Patient.active == True)

            if filter_by == "name":
                query = query.filter(Patient.name.ilike(f"%{keyword}%"))
            elif filter_by == "age":
                try:
                    age_int = int(keyword)
                    query = query.filter(Patient.age == age_int)
                except ValueError:
                    return []
            elif filter_by == "phone":
                query = query.filter(Patient.phone.ilike(f"%{keyword}%"))
            return query.all()

    def get_by_user_id(self, user_id: int):
        with get_session() as session:
            return session.query(Patient) \
                .filter(
                Patient.user_id == user_id,
                Patient.active == True
            ).first()

