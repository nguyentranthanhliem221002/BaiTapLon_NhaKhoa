from NhaKhoa.database.db import get_session
from sqlalchemy.orm import joinedload
from datetime import datetime
from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.appointment import Appointment
from NhaKhoa.models.patient import Patient
from NhaKhoa.models.schedule import Schedule


class AppointmentDAO:
    def get_all(self):
        with get_session() as session:
            return session.query(Appointment) \
                .options(joinedload(Appointment.patient), joinedload(Appointment.schedule)) \
                .all()

    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(Appointment) \
                .options(joinedload(Appointment.patient), joinedload(Appointment.schedule)) \
                .filter(Appointment.id == id).first()

    def add(self, appointment: Appointment):
        with get_session() as session:
            session.add(appointment)
            session.commit()

    def update(self, appointment: Appointment):
        with get_session() as session:
            session.merge(appointment)
            session.commit()
    def get_by_patient_id(self, patient_id: int):
        with get_session() as session:
            return session.query(Appointment) \
                .options(joinedload(Appointment.patient), joinedload(Appointment.schedule)) \
                .filter(Appointment.patient_id == patient_id).all()
    def delete(self, id: int):
        with get_session() as session:
            appt = session.get(Appointment, id)
            if appt:
                session.delete(appt)
                session.commit()

    def search(self, filter_by: str, keyword: str):
        with get_session() as session:
            query = session.query(Appointment).options(
                joinedload(Appointment.patient),
                joinedload(Appointment.schedule)
            )
            keyword_lower = keyword.lower()
            if filter_by == "patient":
                query = query.join(Appointment.patient).filter(Patient.name.ilike(f"%{keyword}%"))
            elif filter_by == "doctor":
                query = query.join(Appointment.doctor).filter(Doctor.name.ilike(f"%{keyword}%"))
            elif filter_by == "schedule":
                # Assuming you want to search by schedule details (e.g., doctor name or time)
                # You may need to join Schedule and Doctor tables if needed
                pass  # Implement as needed
            elif filter_by == "date":
                try:
                    dt = datetime.strptime(keyword, "%Y-%m-%d").date()
                    query = query.filter(Appointment.schedule.has(Schedule.from_date == dt))
                except ValueError:
                    return []
            return query.all()


