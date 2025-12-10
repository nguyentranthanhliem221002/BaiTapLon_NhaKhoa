from NhaKhoa.models.bill import Bill
from NhaKhoa.database.db import get_session

class BillDAO:
    def get_all(self):
        with get_session() as session:
            return session.query(Bill).all()

    def get_by_id(self, bill_id):
        with get_session() as session:
            return session.get(Bill, bill_id)

    def add(self, bill: Bill):
        with get_session() as session:
            session.add(bill)
            session.commit()

    def update_status(self, bill_id, status, payment_method):
        with get_session() as session:
            bill = session.get(Bill, bill_id)
            if bill:
                bill.status = status
                bill.payment_method = payment_method
                session.add(bill)
                session.commit()

    def create_from_appointment(self, appointment_id, amount):
        bill = Bill(appointment_id=appointment_id, amount=amount)
        self.add(bill)

    def update(self, bill: Bill):
        with get_session() as session:
            session.merge(bill)
            session.commit()
