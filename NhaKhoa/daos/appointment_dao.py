from NhaKhoa.database.db import get_session
from sqlalchemy.orm import joinedload
from datetime import datetime

from NhaKhoa.models.bill import Bill
from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.appointment import Appointment
from NhaKhoa.models.patient import Patient
from NhaKhoa.models.schedule import Schedule
from NhaKhoa.daos.bill_dao import BillDAO as bill_dao


class AppointmentDAO:
    def __init__(self):
        # Initialize BillDAO as an instance variable
        self.bill_dao = bill_dao()

    def get_all(self):
        with get_session() as session:
            return session.query(Bill) \
                .options(
                joinedload(Bill.status),
                joinedload(Bill.appointment, innerjoin=True)
                .joinedload(Appointment.patient, innerjoin=True),
                joinedload(Bill.appointment, innerjoin=True)
                .joinedload(Appointment.schedule, innerjoin=True)
                .joinedload(Schedule.doctor, innerjoin=True)
            ) \
                .all()

    def get_all_with_details(self):
        with get_session() as session:
            return session.query(Appointment) \
                .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.schedule).joinedload(Schedule.doctor)
            ) \
                .all()

    # def get_all_with_doctor_names(self):
    #     """Returns Appointment objects with all relationships preloaded."""
    #     with get_session() as session:
    #         pass
    #     return session.query(Appointment) \
    #         .options(
    #         joinedload(Appointment.patient),  # Load patient
    #         joinedload(Appointment.schedule)  # Load schedule
    #         .joinedload(Schedule.doctor)  # Load doctor through schedule
    #     ) \
    #         .all()
    def get_all_with_doctor_names(self):
        with get_session() as session:
            return session.query(Appointment) \
                .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.schedule)
                .joinedload(Schedule.doctor)
            ) \
                .filter(Appointment.active == 1) \
                .all()

    def get_by_doctor_id(self, doctor_id: int):
        with get_session() as session:
            return session.query(Appointment) \
                .join(Appointment.schedule) \
                .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.schedule)
                .joinedload(Schedule.doctor)
            ) \
                .filter(
                Schedule.doctor_id == doctor_id,
                Appointment.active == 1
            ) \
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
            bill_dao = self.bill_dao
            bill = bill_dao.create_from_appointment(appointment_id=appointment.id)
            session.add(bill)
            session.commit()

    def update(self, appointment: Appointment):
        with get_session() as session:
            session.merge(appointment)
            session.commit()

    def get_by_patient_id(self, patient_id: int):
        with get_session() as session:
            return session.query(Appointment) \
                .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.schedule).joinedload(Schedule.doctor),
                joinedload(Appointment.bill)  # ← QUAN TRỌNG: Preload bill để dùng appt.bill an toàn
            ) \
                .filter(
                Appointment.patient_id == patient_id,
                Appointment.active == 1
            ) \
                .all()


    def delete(self, id: int):
        with get_session() as session:
            appt = session.get(Appointment, id)
            if not appt:
                return

            appt.active = 0
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
                query = query.join(Appointment.schedule) \
                    .join(Schedule.doctor) \
                    .filter(Doctor.name.ilike(f"%{keyword}%"))

            elif filter_by == "schedule":
                pass
            elif filter_by == "date":
                try:
                    dt = datetime.strptime(keyword, "%Y-%m-%d").date()
                    query = query.filter(Appointment.schedule.has(Schedule.from_date == dt))
                except ValueError:
                    return []
            return query.all()

    def exists_by_patient_and_schedule(self, patient_id: int, schedule_id: int):
        with get_session() as session:
            return session.query(Appointment).filter(
                Appointment.patient_id == patient_id,
                Appointment.schedule_id == schedule_id,
                Appointment.active == 1
            ).first() is not None


