from NhaKhoa.database.db import get_connection
from NhaKhoa.models.appointment import Appointment

class AppointmentDAO:
    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.appointment_date, a.description,
                   a.patient_id, a.doctor_id,
                   p.name AS patient_name, d.name AS doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
        """)
        rows = cursor.fetchall()
        conn.close()

        appointments = []
        for row in rows:
            appt = Appointment(
                id=row["id"],
                patient_id=row["patient_id"],
                doctor_id=row["doctor_id"],
                appointment_date=row["appointment_date"],
                description=row["description"]
            )
            appt.patient_name = row["patient_name"]
            appt.doctor_name = row["doctor_name"]
            appointments.append(appt)
        return appointments

    def get_by_id(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id=%s", (id,))
        row = cursor.fetchone()
        conn.close()
        return Appointment(**row) if row else None

    def add(self, appointment: Appointment):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments(patient_id, doctor_id, appointment_date, description) VALUES (%s,%s,%s,%s)",
            (appointment.patient_id, appointment.doctor_id, appointment.appointment_date, appointment.description)
        )
        conn.commit()
        conn.close()

    def update(self, appointment: Appointment):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE appointments SET patient_id=%s, doctor_id=%s, appointment_date=%s, description=%s WHERE id=%s",
            (appointment.patient_id, appointment.doctor_id, appointment.appointment_date, appointment.description, appointment.id)
        )
        conn.commit()
        conn.close()

    def delete(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointments WHERE id=%s", (id,))
        conn.commit()
        conn.close()
