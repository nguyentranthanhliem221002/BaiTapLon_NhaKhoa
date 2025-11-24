from database.db import get_connection
from models.appointment import Appointment

class AppointmentDAO:

    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, patient_id, doctor_id, appointment_date, description
            FROM appointments
        """)
        data = cursor.fetchall()
        conn.close()
        return [Appointment(*row) for row in data]

    def add(self, a: Appointment):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments(patient_id, doctor_id, appointment_date, description)
            VALUES (%s, %s, %s, %s)
        """, (a.patient_id, a.doctor_id, a.appointment_date, a.description))
        conn.commit()
        conn.close()
