from sqlalchemy.orm import joinedload

from NhaKhoa.daos.status_dao import StatusDAO as status_dao
from NhaKhoa.models.appointment import Appointment
from NhaKhoa.models.bill import Bill
from NhaKhoa.database.db import get_session
from NhaKhoa.models.schedule import Schedule


class BillDAO:
    def __init__(self):
        # Initialize BillDAO as an instance variable
        self.status_dao = status_dao()

    def get_all(self):
        with get_session() as session:
            return session.query(Bill)\
            .options(
                joinedload(Bill.status),  # Load status relationship
                joinedload(Bill.appointment)  # Load appointment relationship
                    .joinedload(Appointment.patient),  # Load patient through appointment
                joinedload(Bill.appointment)  # Load appointment relationship again
                    .joinedload(Appointment.schedule)  # Load schedule through appointment
                    .joinedload(Schedule.doctor)  # Load doctor through schedule
            ) \
            .all()

    def get_by_id(self, bill_id):
        with get_session() as session:
            return session.get(Bill, bill_id)

    def add(self, bill: Bill):
        with get_session() as session:
            session.add(bill)
            session.commit()

    def update_status(self, bill_id, status):
        with get_session() as session:
            bill = session.get(Bill, bill_id)
            if bill:
                bill.status = status
                session.add(bill)
                session.commit()

    def create_from_appointment(self, appointment_id, total=0):
        """Create a bill from an appointment with default UNPAID status"""
        with get_session() as session:
            from NhaKhoa.models.status import StatusEnum
            status = self.status_dao
            status = status.get_by_name(StatusEnum.UNPAID)
            if status:
                status = status.id

                bill = Bill(
                    appointment_id=appointment_id,
                    total=total,
                    status_id=status
                )

                session.add(bill)
                session.commit()
                return bill

    def update(self, bill: Bill):
        with get_session() as session:
            session.merge(bill)
            session.commit()
