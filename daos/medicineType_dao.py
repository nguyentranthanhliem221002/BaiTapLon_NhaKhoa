import pymysql
from database.db import get_connection

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
