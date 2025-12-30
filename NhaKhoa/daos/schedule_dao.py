from datetime import datetime,date

from sqlalchemy.orm import joinedload
from sqlalchemy import func
from NhaKhoa.database.db import get_session
from NhaKhoa.models.schedule import Schedule


class ScheduleDAO:
    def get_all(self):
        with get_session() as session:
            return session.query(Schedule).options(joinedload(Schedule.doctor)).all()

    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(Schedule).options(joinedload(Schedule.doctor)).filter(Schedule.id == id).first()

    def add(self, schedule: Schedule):
        with get_session() as session:
            session.add(schedule)
            session.commit()

    def update(self, schedule: Schedule):
        with get_session() as session:
            session.merge(schedule)
            session.commit()

    def delete(self, id: int):
        with get_session() as session:
            schedule = session.get(Schedule, id)
            if schedule:
                session.delete(schedule)
                session.commit()

    def get_available_schedules(self, doctor_id: int):
        with get_session() as session:
            return session.query(Schedule) \
                .filter(Schedule.doctor_id == doctor_id, Schedule.num_patient < Schedule.max_patient) \
                .options(joinedload(Schedule.doctor)) \
                .all()

    def get_all_available_schedules(self, doctor_id: int):
        with get_session() as session:
            today = datetime.now().date()
            return session.query(Schedule) \
                .filter(
                Schedule.doctor_id == doctor_id,
                Schedule.from_date >= today,
                Schedule.num_patient < Schedule.max_patient
            ) \
                .options(joinedload(Schedule.doctor)) \
                .order_by(Schedule.from_date) \
                .all()

    def get_available_schedules_by_time(self, available_schedules: list, selected_datetime: datetime):
        """
        Filters a list of available schedules by selected datetime (±1 hour).
        Returns filtered schedules (empty list if out of working hours).
        """
        if not (9 <= selected_datetime.hour < 16):
            return []

        selected_date = selected_datetime.date()
        selected_hour = selected_datetime.hour
        return [
            s for s in available_schedules
            if s.from_date.date() == selected_date and
               (s.from_date.hour == selected_hour or s.from_date.hour == selected_hour + 1)
        ]

    def get_available_schedules_by_doctor_and_date(self, doctor_id: int, selected_date: date):
        with get_session() as session:
            return session.query(Schedule) \
                .filter(
                Schedule.doctor_id == doctor_id,
                func.date(Schedule.from_date) == selected_date,
                Schedule.num_patient < Schedule.max_patient
            ) \
                .order_by(Schedule.from_date) \
                .all()