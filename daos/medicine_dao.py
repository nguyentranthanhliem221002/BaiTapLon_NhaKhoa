import pymysql
from database.db import get_connection

# -----------------------
# Medicine Types
# -----------------------
def get_all_medicine_types():
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM medicine_types")
    types = cursor.fetchall()
    cursor.close()
    db.close()
    return types

def add_medicine_type(name):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO medicine_types (name) VALUES (%s)", (name,))
    db.commit()
    cursor.close()
    db.close()

# -----------------------
# Medicines
# -----------------------
def get_all_medicines():
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT m.id, m.name, m.price, t.id AS medicine_type_id, t.name AS type_name
        FROM medicines m
        JOIN medicine_types t ON m.medicine_type_id = t.id
    """)
    meds = cursor.fetchall()
    cursor.close()
    db.close()
    return meds

def add_medicine(name, type_id, price):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO medicines(name, medicine_type_id, price) VALUES (%s,%s,%s)",
        (name, type_id, price)
    )
    db.commit()
    cursor.close()
    db.close()
