from NhaKhoa.database.db import get_connection
from NhaKhoa.models.doctor import Doctor

class DoctorDAO:
    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors")
        data = cursor.fetchall()
        conn.close()
        # Chuyển dict thành Doctor object
        return [Doctor(**row) for row in data]

    def get_by_id(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors WHERE id=%s", (id,))
        row = cursor.fetchone()
        conn.close()
        return Doctor(**row) if row else None

    def add(self, doctor: Doctor):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO doctors(name, specialty, phone) VALUES (%s,%s,%s)",
            (doctor.name, doctor.specialty, doctor.phone)
        )
        conn.commit()
        conn.close()

    def update(self, doctor: Doctor):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE doctors SET name=%s, specialty=%s, phone=%s WHERE id=%s",
            (doctor.name, doctor.specialty, doctor.phone, doctor.id)
        )
        conn.commit()
        conn.close()

    def delete(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doctors WHERE id=%s", (id,))
        conn.commit()
        conn.close()
