import pymysql
import bcrypt
from datetime import datetime

DB_NAME = "dentalclinic_local"

def get_connection():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_database():
    """Tạo database, bảng và seed data đầy đủ (users có tất cả cột ngay từ đầu)"""
    db = pymysql.connect(host="127.0.0.1", user="root", password="")
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Tạo database nếu chưa có
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")

    # ----------------------------
    # Bảng users (đầy đủ các cột)
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE,
            password VARCHAR (255),
            role VARCHAR(20),
            email VARCHAR(255) UNIQUE,
            reset_token VARCHAR(255),
            reset_token_expiry DATETIME
        )
    """)

    # ----------------------------
    # Bảng patients
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            age INT,
            phone VARCHAR(20),
            address VARCHAR(255)
        )
    """)

    # ----------------------------
    # Bảng doctors
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            specialty VARCHAR(255),
            phone VARCHAR(20)
        )
    """)

    # ----------------------------
    # Bảng appointments
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT,
            doctor_id INT,
            appointment_date DATETIME,
            description TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    """)

    # ----------------------------
    # Bảng service_types
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_types (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        )
    """)

    # ----------------------------
    # Bảng services
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            service_type_id INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (service_type_id) REFERENCES service_types(id)
        )
    """)

    # ----------------------------
    # Bảng medicine_types
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_types (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        )
    """)

    # ----------------------------
    # Bảng medicines
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            medicine_type_id INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (medicine_type_id) REFERENCES medicine_types(id)
        )
    """)

    db.commit()

    # ----------------------------
    # Seed dữ liệu
    # ----------------------------
    # Users
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    if cursor.fetchone()["total"] == 0:
        users = [
            ("admin", "admin@example.com", "admin123", "admin"),
            ("doctor", "doctor@example.com", "123456", "doctor"),
            ("patient", "patient@example.com", "123456", "patient")
        ]
        for username, email, pwd, role in users:
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                (username, email, hashed, role)
            )
        db.commit()

    # Doctors
    cursor.execute("SELECT COUNT(*) AS total FROM doctors")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("""
            INSERT INTO doctors (name, specialty, phone)
            VALUES
            ('Dr. Nam', 'Nha chu', '0901123456'),
            ('Dr. Hoa', 'Chỉnh nha', '0902876543')
        """)
        db.commit()

    # Patients
    cursor.execute("SELECT COUNT(*) AS total FROM patients")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("""
            INSERT INTO patients (name, age, phone, address)
            VALUES
            ('Nguyen Van A', 25, '0901123456', 'Ha Noi'),
            ('Tran Thi B', 30, '0902987654', 'Da Nang')
        """)
        db.commit()

    # Service Types
    cursor.execute("SELECT COUNT(*) AS total FROM service_types")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("INSERT INTO service_types (name) VALUES ('Khám răng'), ('Nha khoa thẩm mỹ')")
        db.commit()

    # Services
    cursor.execute("SELECT COUNT(*) AS total FROM services")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("""
            INSERT INTO services (name, service_type_id, price) VALUES
            ('Trám răng', 1, 150000),
            ('Tẩy trắng răng', 2, 500000)
        """)
        db.commit()

    # Medicine Types
    cursor.execute("SELECT COUNT(*) AS total FROM medicine_types")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("INSERT INTO medicine_types (name) VALUES ('Thuốc giảm đau'), ('Thuốc kháng sinh')")
        db.commit()

    # Medicines
    cursor.execute("SELECT COUNT(*) AS total FROM medicines")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("""
            INSERT INTO medicines (name, medicine_type_id, price) VALUES
            ('Paracetamol', 1, 2000),
            ('Amoxicillin', 2, 5000)
        """)
        db.commit()
    # ----------------------------
    # Bảng bills
    # ----------------------------
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS bills
                   (
                       id
                       INT
                       AUTO_INCREMENT
                       PRIMARY
                       KEY,
                       appointment_id
                       INT
                       NOT
                       NULL,
                       amount
                       DECIMAL
                   (
                       10,
                       2
                   ) NOT NULL,
                       status VARCHAR
                   (
                       50
                   ) DEFAULT 'Chưa thanh toán',
                       payment_method VARCHAR
                   (
                       50
                   ),
                       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY
                   (
                       appointment_id
                   ) REFERENCES appointments
                   (
                       id
                   )
                       )
                   """)
    db.commit()

    cursor.close()
    db.close()
    print(">>> ✓ Database & Tables ready!")
