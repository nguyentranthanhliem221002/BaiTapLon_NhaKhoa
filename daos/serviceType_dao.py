import pymysql
from database.db import get_connection

def get_all_service_types():
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM service_types")
    types = cursor.fetchall()
    cursor.close()
    db.close()
    return types

def add_service_type(name):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO service_types (name) VALUES (%s)", (name,))
    db.commit()
    cursor.close()
    db.close()
