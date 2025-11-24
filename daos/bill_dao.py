import pymysql
from database.db import get_connection
from models.bill import Bill

class BillDAO:
    def __init__(self):
        pass

    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # <-- sửa ở đây
        cursor.execute("""
            SELECT b.*, a.patient_id, a.doctor_id
            FROM bills b
            LEFT JOIN appointments a ON b.appointment_id = a.id
        """)
        rows = cursor.fetchall()
        bills = []
        for r in rows:
            bill = Bill(
                id=r['id'],
                appointment_id=r['appointment_id'],
                amount=r['amount'],
                status=r['status'],
                payment_method=r['payment_method']
            )
            bills.append(bill)
        conn.close()
        return bills

    def get_by_id(self, bill_id):
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # <-- sửa ở đây
        cursor.execute("SELECT * FROM bills WHERE id=%s", (bill_id,))
        r = cursor.fetchone()
        conn.close()
        if r:
            return Bill(
                id=r['id'],
                appointment_id=r['appointment_id'],
                amount=r['amount'],
                status=r['status'],
                payment_method=r['payment_method']
            )
        return None

    def add(self, bill: Bill):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bills (appointment_id, amount, status) VALUES (%s, %s, %s)",
            (bill.appointment_id, bill.amount, bill.status)
        )
        conn.commit()
        conn.close()

    def get_detailed_by_id(self, bill_id):
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # <-- sửa ở đây
        cursor.execute("""
            SELECT b.*, a.patient_id, a.doctor_id, p.name AS patient_name, d.name AS doctor_name
            FROM bills b
                LEFT JOIN appointments a ON b.appointment_id = a.id
                LEFT JOIN patients p ON a.patient_id = p.id
                LEFT JOIN doctors d ON a.doctor_id = d.id
            WHERE b.id = %s
                       """, (bill_id,))
        r = cursor.fetchone()
        conn.close()
        return r

    def create_from_appointment(self, appointment_id, amount):
        bill = Bill(appointment_id=appointment_id, amount=amount)
        self.add(bill)

    def update_status(self, bill_id, status, payment_method):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE bills SET status=%s, payment_method=%s WHERE id=%s",
            (status, payment_method, bill_id)
        )
        conn.commit()
        conn.close()
