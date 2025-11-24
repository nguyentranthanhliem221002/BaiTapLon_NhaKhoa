from database.db import get_connection
from models.patient import Patient

class PatientDAO:

    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients")
        data = cursor.fetchall()
        conn.close()
        return [Patient(*row) for row in data]

    def get_by_id(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = %s", (id,))
        row = cursor.fetchone()
        conn.close()
        return Patient(*row) if row else None

    def add(self, p: Patient):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients(name, age, phone, address)
            VALUES (%s, %s, %s, %s)
        """, (p.name, p.age, p.phone, p.address))
        conn.commit()
        conn.close()

    def update(self, p: Patient):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patients
            SET name=%s, age=%s, phone=%s, address=%s
            WHERE id=%s
        """, (p.name, p.age, p.phone, p.address, p.id))
        conn.commit()
        conn.close()

    def delete(self, id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id=%s", (id,))
        conn.commit()
        conn.close()
