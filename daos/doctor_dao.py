from database.db import get_connection
from models.doctor import Doctor

class DoctorDAO:

    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors")
        data = cursor.fetchall()
        conn.close()
        return [Doctor(*row) for row in data]

    def add(self, d: Doctor):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO doctors(name, specialty, phone)
            VALUES (%s, %s, %s)
        """, (d.name, d.specialty, d.phone))
        conn.commit()
        conn.close()
