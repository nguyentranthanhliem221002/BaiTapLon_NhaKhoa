from sqlalchemy import func
from datetime import datetime, timedelta

from NhaKhoa.database.db import get_session
from NhaKhoa.models.bill import Bill
from NhaKhoa.models.appointment import Appointment
from NhaKhoa.models.schedule import Schedule
from NhaKhoa.models.doctor import Doctor


class ThongKeDAO:

    def thong_ke_theo_ngay(self, date_str: str, doctor_id: int | None = None):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = start_of_day + timedelta(days=1)

        with get_session() as session:

            bill_query = session.query(
                func.count(Bill.id),
                func.coalesce(func.sum(Bill.total), 0)
            ).join(
                Appointment, Bill.appointment_id == Appointment.id
            ).join(
                Schedule, Appointment.schedule_id == Schedule.id
            ).filter(
                Bill.created_date >= start_of_day,
                Bill.created_date < next_day
            )

            doctor_query = session.query(
                Doctor.id,
                Doctor.name,
                func.count(Appointment.id).label("patient_count"),
                func.coalesce(func.sum(Bill.total), 0).label("total_money")
            ).join(
                Schedule, Schedule.doctor_id == Doctor.id
            ).join(
                Appointment, Appointment.schedule_id == Schedule.id
            ).join(
                Bill, Bill.appointment_id == Appointment.id
            ).filter(
                Bill.created_date >= start_of_day,
                Bill.created_date < next_day
            )

            if doctor_id:
                bill_query = bill_query.filter(Schedule.doctor_id == doctor_id)
                doctor_query = doctor_query.filter(Doctor.id == doctor_id)

            bill_stats = bill_query.first()
            doctor_stats = doctor_query.group_by(
                Doctor.id, Doctor.name
            ).all()

            return {
                "total_bills": bill_stats[0],
                "total_revenue": bill_stats[1],
                "doctor_stats": doctor_stats
            }
