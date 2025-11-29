import pymysql

from NhaKhoa.database.db import get_connection

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
    cursor.execute("INSERT INTO service_types(name) VALUES (%s)", (name,))
    db.commit()
    cursor.close()
    db.close()

def get_all_services():
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT s.id, s.name, s.price, t.name AS type_name
        FROM services s
        JOIN service_types t ON s.service_type_id = t.id
    """)
    services = cursor.fetchall()
    cursor.close()
    db.close()
    return services

def add_service(name, type_id, price):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO services(name, service_type_id, price) VALUES (%s,%s,%s)",
        (name, type_id, price)
    )
    db.commit()
    cursor.close()
    db.close()
