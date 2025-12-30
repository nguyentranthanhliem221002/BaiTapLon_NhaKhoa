from sqlalchemy import func
from sqlalchemy.orm import joinedload

from NhaKhoa import app
from NhaKhoa.daos.status_dao import StatusDAO as status_dao
from NhaKhoa.models.appointment import Appointment
from NhaKhoa.models.bill import Bill
from NhaKhoa.database.db import get_session
from NhaKhoa.models.bill_med import BillMedicine
from NhaKhoa.models.bill_serv import BillService
from NhaKhoa.models.medicine import Medicine
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

    def get_bill_medicine(self, bill_id: int, medicine_id: int):
        with get_session() as session:
            return session.query(BillMedicine).filter(
                BillMedicine.bill_id == bill_id,
                BillMedicine.medicine_id == medicine_id).first()

    def get_bill_service(self, bill_id: int):
        with get_session() as session:
            return session.get(BillService, bill_id)

    def get_all_medicines_by_bill_id(self, bill_id: int):
        with (get_session() as session):
            return session.query(BillMedicine) \
            .filter(BillMedicine.bill_id == bill_id,
            BillMedicine.active == True) \
            .options(joinedload(BillMedicine.medicine)) \
            .all()

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

    def delete_medicine(self, bill_medicine: BillMedicine):
        with get_session() as session:
            status = False
            bill_medicine.active = status
            session.merge(bill_medicine)
            session.commit()

    def restore_medicine(self, bill_medicine: BillMedicine):
        with get_session() as session:
            status = True
            bill_medicine.active = status
            session.merge(bill_medicine)
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

    def add_bill_medicine(self, bill_id: int, medicine_id: int, quantity: int = 1):
        with get_session() as session:
            # Get the medicine to get its price
            medicine = session.get(Medicine, medicine_id)
            if not medicine:
                raise ValueError(f"Medicine with ID {medicine_id} not found")

            bill_medicine = self.get_bill_medicine(bill_id=bill_id, medicine_id=medicine_id)

            if bill_medicine:
                if bill_medicine.medicine_id == medicine_id:
                    if bill_medicine.active == False:
                        self.restore_medicine(bill_medicine=bill_medicine)

                    # Update existing record
                    if bill_medicine.quantity != quantity and quantity != 0:
                        bill_medicine.quantity = quantity  # Add to existing quantity
                        bill_medicine.price = medicine.price * bill_medicine.quantity  # Update price
                    elif quantity < 1:
                        self.delete_medicine(bill_medicine)

            else:
                # Create new record
                bill_medicine = BillMedicine(
                    bill_id=bill_id,
                    medicine_id=medicine.id,
                    quantity=quantity,
                    price=medicine.price * quantity  # Use the medicine's price
                )

            session.add(bill_medicine)

            # Update the bill total
            bill = session.get(Bill, bill_id)
            if bill:
                # Calculate new total (sum of all bill services and medicines)
                total = session.query(func.sum(BillService.price)).filter(BillService.bill_id == bill_id, BillService.active == True).scalar() or 0
                total += session.query(func.sum(BillMedicine.price * BillMedicine.quantity)).filter(
                    BillMedicine.bill_id == bill_id, BillMedicine.active == True).scalar() or 0
                bill.total = total

            session.commit()
            return bill_medicine