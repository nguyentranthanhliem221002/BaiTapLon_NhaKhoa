from sqlalchemy.orm import joinedload

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
