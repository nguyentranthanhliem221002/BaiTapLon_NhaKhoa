import pymysql
import bcrypt

DB_NAME = "dentalclinic_local"

def get_connection():
    """Kết nối tới database dentalclinic_local"""
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="",  # điền password nếu có
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_database():
    """Tạo database, bảng và seed data"""
    # Kết nối không có database (để tạo DB)
    db = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password=""
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)
    # Tạo database nếu chưa có
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")

    # --------------------
    # Tạo bảng
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE,
            password VARCHAR(255),
            role VARCHAR(20)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            age INT,
            phone VARCHAR(20),
            address VARCHAR(255)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            specialty VARCHAR(255),
            phone VARCHAR(20)
        )
    """)
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
    db.commit()
    print(">>> ✓ Database & Tables ready!")

    # ==========================
    # Seed dữ liệu
    # ==========================
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Seed admin
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    if cursor.fetchone()["total"] == 0:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, 'admin')",
            ("admin", hashed)
        )
        db.commit()
        print(">>> ✓ Seeded admin user")

    # Seed doctors
    cursor.execute("SELECT COUNT(*) AS total FROM doctors")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("""
            INSERT INTO doctors (name, specialty, phone)
            VALUES
            ('Dr. Nam', 'Nha chu', '0901123456'),
            ('Dr. Hoa', 'Chỉnh nha', '0902876543')
        """)
        db.commit()
        print(">>> ✓ Seeded doctor data")

    # Seed patients (tuỳ bạn muốn)
    cursor.execute("SELECT COUNT(*) AS total FROM patients")
    if cursor.fetchone()["total"] == 0:
        cursor.execute("""
            INSERT INTO patients (name, age, phone, address)
            VALUES
            ('Nguyen Van A', 25, '0901123456', 'Ha Noi'),
            ('Tran Thi B', 30, '0902987654', 'Da Nang')
        """)
        db.commit()
        print(">>> ✓ Seeded patient data")

    cursor.close()
    db.close()
