from flask import Flask, render_template, redirect, request, session, url_for, flash
from database.db import init_database, get_connection
import bcrypt
from flask_mail import Mail, Message
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import pymysql.cursors  # Để sử dụng DictCursor

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------------------
# Khởi tạo database
# -------------------
init_database()

# -------------------
# Cấu hình Flask-Mail (Gửi email reset)
# -------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'youremail@gmail.com'
app.config['MAIL_PASSWORD'] = 'yourapppassword'
mail = Mail(app)

# -------------------
# Cấu hình Google OAuth
# -------------------
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# ====================
# HOME / DASHBOARD
# ====================
@app.route("/")
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])

# ====================
# REGISTER
# ====================
@app.route("/account/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("account/register.html", error="Mật khẩu không khớp!")

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        db = get_connection()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password.decode(), "patient")
            )
            db.commit()
        except Exception:
            db.rollback()
            cursor.close()
            db.close()
            return render_template("account/register.html", error="Tên tài khoản đã tồn tại hoặc lỗi khác!")

        cursor.close()
        db.close()
        flash("Đăng ký thành công! Vui lòng đăng nhập.")
        return redirect(url_for("login"))

    return render_template("account/register.html")

# ====================
# LOGIN
# ====================
@app.route("/account/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_connection()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        return render_template("account/login.html", error="Sai tài khoản hoặc mật khẩu!")

    return render_template("account/login.html")

# ====================
# LOGOUT
# ====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ====================
# GOOGLE LOGIN
# ====================
@app.route("/login/google")
def google_login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/google/callback")
def google_callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    user_info = userinfo_response.json()
    email = user_info["email"]

    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE username=%s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (email, "", "patient")
        )
        db.commit()
    cursor.close()
    db.close()

    session["user"] = email
    session["role"] = "patient"
    return redirect(url_for("dashboard"))

# ====================
# FORGOT PASSWORD
# ====================
@app.route("/account/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        token = bcrypt.gensalt().decode()  # tạm token

        msg = Message("Reset mật khẩu", sender="youremail@gmail.com", recipients=[email])
        msg.body = f"Click link để reset mật khẩu: http://localhost:5000/account/reset-password/{token}"
        mail.send(msg)

        flash("Email reset mật khẩu đã được gửi!")
        return redirect(url_for("login"))

    return render_template("account/forgot_password.html")

# ====================
# COMMON FUNCTION
# ====================
def get_all(table_name, filter_by=None, keyword=None):
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    if filter_by and keyword:
        sql = f"SELECT * FROM {table_name} WHERE {filter_by} LIKE %s"
        cursor.execute(sql, ('%' + keyword + '%',))
    else:
        cursor.execute(f"SELECT * FROM {table_name}")
    items = cursor.fetchall()
    cursor.close()
    db.close()
    return items

# ====================
# PATIENT CRUD
# ====================
@app.route("/patients")
def patients():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword")
    patients = get_all("patients", filter_by, keyword)
    return render_template("patient/patients.html", patients=patients)

@app.route("/patient/patient_add", methods=["GET","POST"])
def add_patient():
    if request.method == "POST":
        data = request.form
        db = get_connection()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO patients (name, age, phone, address) VALUES (%s,%s,%s,%s)",
            (data["name"], int(data["age"]), data["phone"], data["address"])
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("patients"))
    return render_template("patient/patient_add.html")

@app.route("/patient/patient_edit/<int:id>", methods=["GET","POST"])
def edit_patient(id):
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM patients WHERE id=%s", (id,))
    patient = cursor.fetchone()
    if request.method == "POST":
        data = request.form
        cursor.execute(
            "UPDATE patients SET name=%s, age=%s, phone=%s, address=%s WHERE id=%s",
            (data["name"], int(data["age"]), data["phone"], data["address"], id)
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("patients"))
    cursor.close()
    db.close()
    return render_template("patient/patient_edit.html", patient=patient)

@app.route("/patient/patient_delete/<int:id>")
def delete_patient(id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM patients WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("patients"))

# ====================
# DOCTOR CRUD
# ====================
@app.route("/doctors")
def doctors():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword")
    doctors = get_all("doctors", filter_by, keyword)
    return render_template("doctor/doctors.html", doctors=doctors)

@app.route("/doctor/doctor_add", methods=["GET","POST"])
def add_doctor():
    if request.method == "POST":
        data = request.form
        db = get_connection()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO doctors (name, specialty, phone) VALUES (%s,%s,%s)",
            (data["name"], data["specialty"], data["phone"])
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("doctors"))
    return render_template("doctor/doctor_add.html")

@app.route("/doctor/doctor_edit/<int:id>", methods=["GET","POST"])
def edit_doctor(id):
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM doctors WHERE id=%s", (id,))
    doctor = cursor.fetchone()
    if request.method == "POST":
        data = request.form
        cursor.execute(
            "UPDATE doctors SET name=%s, specialty=%s, phone=%s WHERE id=%s",
            (data["name"], data["specialty"], data["phone"], id)
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("doctors"))
    cursor.close()
    db.close()
    return render_template("doctor/doctor_edit.html", doctor=doctor)

@app.route("/doctor/doctor_delete/<int:id>")
def delete_doctor(id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM doctors WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("doctors"))

# ====================
# APPOINTMENT CRUD
# ====================
@app.route("/appointments")
def appointments():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword")
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    sql = """
    SELECT a.id, p.name AS patient_name, d.name AS doctor_name, a.appointment_date, a.description
    FROM appointments a
    JOIN patients p ON a.patient_id = p.id
    JOIN doctors d ON a.doctor_id = d.id
    """
    params = ()
    if filter_by and keyword:
        if filter_by == "patient":
            sql += " WHERE p.name LIKE %s"
        elif filter_by == "doctor":
            sql += " WHERE d.name LIKE %s"
        elif filter_by == "date":
            sql += " WHERE a.appointment_date LIKE %s"
        params = ('%' + keyword + '%',)

    cursor.execute(sql, params)
    appointments = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("appointment/appointments.html", appointments=appointments)

@app.route("/appointment/appointment_add", methods=["GET","POST"])
def add_appointment():
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    if request.method == "POST":
        data = request.form
        cursor.execute(
            "INSERT INTO appointments (patient_id, doctor_id, appointment_date, description) VALUES (%s,%s,%s,%s)",
            (int(data["patient_id"]), int(data["doctor_id"]), data["appointment_date"], data["description"])
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("appointments"))

    cursor.close()
    db.close()
    return render_template("appointment/appointment_add.html", patients=patients, doctors=doctors)

@app.route("/appointment/appointment_edit/<int:id>", methods=["GET","POST"])
def edit_appointment(id):
    db = get_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM appointments WHERE id=%s", (id,))
    appointment = cursor.fetchone()
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    if request.method == "POST":
        data = request.form
        cursor.execute(
            "UPDATE appointments SET patient_id=%s, doctor_id=%s, appointment_date=%s, description=%s WHERE id=%s",
            (int(data["patient_id"]), int(data["doctor_id"]), data["appointment_date"], data["description"], id)
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("appointments"))

    cursor.close()
    db.close()
    return render_template("appointment/appointment_edit.html", appointment=appointment, patients=patients, doctors=doctors)

@app.route("/appointment/appointment_delete/<int:id>")
def delete_appointment(id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM appointments WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("appointments"))


# ====================
# RUN SERVER
# ====================
if __name__ == "__main__":
    app.run(debug=True)
