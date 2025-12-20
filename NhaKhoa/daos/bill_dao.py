from sqlalchemy.orm import joinedload

from NhaKhoa.daos.status_dao import StatusDAO as status_dao
from NhaKhoa.models.appointment import Appointment
from NhaKhoa.models.bill import Bill
from NhaKhoa.database.db import get_session
from NhaKhoa.models.schedule import Schedule


class BillDAO:
    def __init__(self):
        self.status_dao = status_dao()

    def get_all(self):
        with get_session() as session:
            return session.query(Bill) \
                .options(
                joinedload(Bill.status),
                joinedload(Bill.appointment)
                .joinedload(Appointment.patient),
                joinedload(Bill.appointment)
                .joinedload(Appointment.schedule)
                .joinedload(Schedule.doctor)
            ) \
                .all()

    def get_by_id(self, bill_id: int):
        with get_session() as session:
            return session.get(Bill, bill_id)

    def get_by_order_id(self, order_id: str):
        with get_session() as session:
            return session.query(Bill).filter(Bill.order_id == order_id).first()

    def get_by_appointment_id(self, appointment_id: int):
        with get_session() as session:
            return session.query(Bill).filter(Bill.appointment_id == appointment_id).first()

    def create_from_appointment(self, appointment_id: int, total: float = 0.0):
        with get_session() as session:
            from NhaKhoa.models.status import StatusEnum

            unpaid_status = self.status_dao.get_by_name(StatusEnum.UNPAID)
            if not unpaid_status:
                raise ValueError("Trạng thái UNPAID không tồn tại!")

            bill = Bill(
                appointment_id=appointment_id,
                total=total,
                status_id=unpaid_status.id,
                payment_method="cash"
            )
            session.add(bill)
            session.commit()
            return bill

    def update(self, bill: Bill):
        with get_session() as session:
            session.merge(bill)
            session.commit()

    def update_status(self, bill_id: int, status_name: str, payment_method: str = None):
        with get_session() as session:
            bill = session.get(Bill, bill_id)
            if not bill:
                return False

            status = self.status_dao.get_by_name(status_name)
            if status:
                bill.status_id = status.id

            if payment_method:
                bill.payment_method = payment_method

            session.add(bill)
            session.commit()
            return True

    def recalculate_total(self, bill_id: int) -> bool:
        with get_session() as session:
            bill = session.get(Bill, bill_id)
            if not bill:
                return False

            total = 0.0
            for bs in bill.bill_services:
                if bs.service:
                    total += bs.service.price * bs.quantity
            for bm in bill.bill_medicines:
                if bm.medicine:
                    total += bm.medicine.price * bm.quantity

            bill.total = total
            session.commit()
            return True

    def get_by_doctor_id(self, doctor_id: int):
        with get_session() as session:
            return session.query(Bill) \
                .join(Bill.appointment) \
                .join(Appointment.schedule) \
                .options(
                joinedload(Bill.status),
                joinedload(Bill.appointment).joinedload(Appointment.patient),
                joinedload(Bill.appointment).joinedload(Appointment.schedule).joinedload(Schedule.doctor)
            ) \
                .filter(Schedule.doctor_id == doctor_id) \
                .all()