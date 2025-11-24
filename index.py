from flask import Flask, render_template, redirect, request, session, url_for, flash
from database.db import init_database, get_connection
from daos.user_dao import UserDAO
from daos.patient_dao import PatientDAO
from daos.doctor_dao import DoctorDAO
from daos.bill_dao import BillDAO
from daos.appointment_dao import AppointmentDAO
from daos.service_dao import get_all_services, add_service, get_all_service_types, add_service_type
from daos.medicine_dao import get_all_medicines, add_medicine, get_all_medicine_types, add_medicine_type
from flask_mail import Mail, Message
from functools import wraps
import bcrypt
import requests
from oauthlib.oauth2 import WebApplicationClient
import json
import secrets
from datetime import datetime, timedelta

# Imports model thực tế
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.bill import Bill

# ==========================
# INIT APP
# ==========================
app = Flask(__name__)
app.secret_key = "supersecretkey"

# ==========================
# INIT DATABASE
# ==========================
init_database()

# ==========================
# CONFIG FLASK-MAIL
# ==========================
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='youremail@gmail.com',       # Thay bằng Gmail của bạn
    MAIL_PASSWORD='yourapppassword'           # Thay bằng App Password
)
mail = Mail(app)

# ==========================
# GOOGLE OAUTH CONFIG
# ==========================
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# ==========================
# DECORATOR PHÂN QUYỀN
# ==========================
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session:
                flash("Vui lòng đăng nhập!")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Bạn không có quyền truy cập!")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==========================
# DAO INIT
# ==========================
user_dao = UserDAO()
patient_dao = PatientDAO()
doctor_dao = DoctorDAO()
appointment_dao = AppointmentDAO()
bill_dao = BillDAO()

# ==========================
# HOME / DASHBOARD
# ==========================
@app.route("/")
@app.route("/dashboard")
@login_required()
def dashboard():
    return render_template("index.html", user=session["user"], role=session["role"])

# ==========================
# REGISTER / LOGIN / LOGOUT
# ==========================
@app.route("/account/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form.get("role", "patient")

        if password != confirm_password:
            return render_template("account/register.html", error="Mật khẩu không khớp!")

        if user_dao.get_by_username(username) or user_dao.get_by_username(email):
            return render_template("account/register.html", error="Tên tài khoản hoặc email đã tồn tại!")

        new_user = User(username=username, password=password, role=role, email=email)
        user_dao.register(new_user)
        flash("Đăng ký thành công! Vui lòng đăng nhập.")
        return redirect(url_for("login"))

    return render_template("account/register.html")

@app.route("/account/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form["username"].strip()
        password = request.form["password"]
        user = user_dao.login(username_or_email, password)
        if user:
            session["user"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))
        return render_template("account/login.html", error="Sai tài khoản hoặc mật khẩu!")
    return render_template("account/login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================
# QUÊN MẬT KHẨU / ĐỔI MẬT KHẨU
# ==========================
# ==========================
# QUÊN MẬT KHẨU
# ==========================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()
        user = user_dao.get_by_username(email)
        if user:
            # Tạo token
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)
            user_dao.set_reset_token(user, token, expiry)

            reset_link = url_for("reset_password", token=token, _external=True)

            # Gửi email
            msg = Message(
                subject="Reset mật khẩu",
                sender=app.config["MAIL_USERNAME"],
                recipients=[user.email],
                body=f"Để đổi mật khẩu, vui lòng nhấn vào link: {reset_link}\nLink có hiệu lực 1 giờ."
            )
            mail.send(msg)

            flash("Chúng tôi đã gửi hướng dẫn reset mật khẩu đến email của bạn.")
            return redirect(url_for("login"))
        else:
            flash("Email không tồn tại!")
    return render_template("account/forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = user_dao.get_by_token(token)
    if not user:
        flash("Token không hợp lệ hoặc đã hết hạn!")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        if new_password != confirm_password:
            flash("Mật khẩu mới không khớp!")
            return render_template("account/reset_password.html")

        user_dao.update_password(user, new_password)
        user_dao.clear_reset_token(user)
        flash("Đổi mật khẩu thành công! Hãy đăng nhập lại.")
        return redirect(url_for("login"))

    return render_template("account/reset_password.html")

@app.route("/change-password", methods=["GET", "POST"])
@login_required()
def change_password():
    if request.method == "POST":
        current = request.form["current_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

        user = user_dao.get_by_username(session["user"])
        if not user_dao.check_password(user, current):
            flash("Mật khẩu hiện tại không đúng!")
        elif new != confirm:
            flash("Mật khẩu mới không khớp!")
        else:
            user_dao.update_password(user, new)
            flash("Đổi mật khẩu thành công!")
            return redirect(url_for("dashboard"))
    return render_template("account/change_password.html")

# ==========================
# GOOGLE OAUTH LOGIN
# ==========================
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

    email = user_info.get("email")
    if email:
        existing = user_dao.get_by_username(email)
        if not existing:
            new_user = User(username=email, password="google_oauth", email=email, role="patient")
            user_dao.register(new_user)
        session["user"] = email
        session["role"] = "patient"
    return redirect(url_for("dashboard"))

# ==========================
# CRUD PATIENT
# ==========================
@app.route("/patients")
@login_required()
def patients():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip()
    all_patients = patient_dao.get_all()

    if filter_by and keyword:
        keyword_lower = keyword.lower()
        if filter_by == "name":
            all_patients = [p for p in all_patients if keyword_lower in p.name.lower()]
        elif filter_by == "age":
            try:
                age_int = int(keyword)
                all_patients = [p for p in all_patients if p.age == age_int]
            except ValueError:
                all_patients = []
        elif filter_by == "phone":
            all_patients = [p for p in all_patients if keyword_lower in p.phone.lower()]

    return render_template("patient/patients.html", patients=all_patients)

@app.route("/patient/add", methods=["GET","POST"])
@login_required()
def add_patient():
    if request.method == "POST":
        data = request.form
        new_patient = Patient(name=data["name"], age=int(data["age"]), phone=data["phone"], address=data["address"])
        patient_dao.add(new_patient)
        return redirect(url_for("patients"))
    return render_template("patient/patient_add.html")

@app.route("/patient/edit/<int:id>", methods=["GET","POST"])
@login_required()
def edit_patient(id):
    patient = patient_dao.get_by_id(id)
    if request.method == "POST":
        data = request.form
        patient.name = data["name"]
        patient.age = int(data["age"])
        patient.phone = data["phone"]
        patient.address = data["address"]
        patient_dao.update(patient)
        return redirect(url_for("patients"))
    return render_template("patient/patient_edit.html", patient=patient)

@app.route("/patient/delete/<int:id>")
@login_required()
def delete_patient(id):
    patient_dao.delete(id)
    return redirect(url_for("patients"))

# ====================
# CRUD Bác sĩ
# ====================
@app.route("/doctors")
@login_required()
def doctors():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip()

    all_doctors = doctor_dao.get_all()

    if filter_by and keyword:
        keyword_lower = keyword.lower()
        if filter_by == "name":
            all_doctors = [d for d in all_doctors if keyword_lower in d.name.lower()]
        elif filter_by == "specialty":
            all_doctors = [d for d in all_doctors if keyword_lower in d.specialty.lower()]
        elif filter_by == "phone":
            all_doctors = [d for d in all_doctors if keyword_lower in d.phone.lower()]

    return render_template("doctor/doctors.html", doctors=all_doctors)

@app.route("/doctor/add", methods=["GET","POST"])
@login_required(role="admin")
def add_doctor():
    if request.method == "POST":
        data = request.form
        new_doctor = Doctor(
            name=data["name"],
            specialty=data["specialty"],
            phone=data["phone"]
        )
        doctor_dao.add(new_doctor)
        return redirect(url_for("doctors"))
    return render_template("doctor/doctor_add.html")

@app.route("/doctor/edit/<int:id>", methods=["GET","POST"])
@login_required(role="admin")
def edit_doctor(id):
    doctor = doctor_dao.get_by_id(id)
    if request.method == "POST":
        data = request.form
        doctor.name = data["name"]
        doctor.specialty = data["specialty"]
        doctor.phone = data["phone"]
        doctor_dao.update(doctor)
        return redirect(url_for("doctors"))
    return render_template("doctor/doctor_edit.html", doctor=doctor)

@app.route("/doctor/delete/<int:id>")
@login_required(role="admin")
def delete_doctor(id):
    doctor_dao.delete(id)
    return redirect(url_for("doctors"))

# ====================
# CRUD Lịch hẹn
# ====================
@app.route("/appointments")
@login_required()
def appointments():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip()

    all_appointments = appointment_dao.get_all()

    if filter_by and keyword:
        if filter_by == "patient":
            all_appointments = [a for a in all_appointments if keyword.lower() in a.patient_name.lower()]
        elif filter_by == "doctor":
            all_appointments = [a for a in all_appointments if keyword.lower() in a.doctor_name.lower()]
        elif filter_by == "date":
            from datetime import datetime
            try:
                keyword_date = datetime.strptime(keyword, "%Y-%m-%d").date()
                all_appointments = [a for a in all_appointments if a.appointment_date.date() == keyword_date]
            except ValueError:
                all_appointments = []

    return render_template("appointment/appointments.html", appointments=all_appointments)

@app.route("/appointment/add", methods=["GET","POST"])
@login_required()
def add_appointment():
    patients = patient_dao.get_all()
    doctors = doctor_dao.get_all()
    if request.method == "POST":
        data = request.form
        new_appointment = Appointment(
            patient_id=int(data["patient_id"]),
            doctor_id=int(data["doctor_id"]),
            appointment_date=data["appointment_date"],
            description=data.get("description", "")
        )
        appointment_dao.add(new_appointment)
        return redirect(url_for("appointments"))
    return render_template("appointment/appointment_add.html", patients=patients, doctors=doctors)

@app.route("/appointment/edit/<int:id>", methods=["GET","POST"])
@login_required()
def edit_appointment(id):
    appointment = appointment_dao.get_by_id(id)
    patients = patient_dao.get_all()
    doctors = doctor_dao.get_all()

    if request.method == "POST":
        data = request.form
        appointment.patient_id = int(data["patient_id"])
        appointment.doctor_id = int(data["doctor_id"])
        appointment.appointment_date = data["appointment_date"]
        appointment.description = data.get("description", "")
        appointment_dao.update(appointment)
        return redirect(url_for("appointments"))

    return render_template(
        "appointment/appointment_edit.html",
        appointment=appointment,
        patients=patients,
        doctors=doctors
    )

@app.route("/appointment/delete/<int:id>")
@login_required()
def delete_appointment(id):
    appointment_dao.delete(id)
    return redirect(url_for("appointments"))

# ====================
# CRUD Service
# ====================
@app.route("/service-types")
@login_required()
def service_types():
    return render_template("service/service_types.html", types=get_all_service_types())

@app.route("/service-type/add", methods=["GET","POST"])
@login_required(role="admin")
def add_service_type_route():
    if request.method == "POST":
        add_service_type(request.form["name"])
        return redirect(url_for("service_types"))
    return render_template("service/service_type_add.html")

@app.route("/services")
@login_required()
def services():
    keyword = request.args.get("keyword", "").strip().lower()
    all_services = get_all_services()

    if keyword:
        all_services = [
            s for s in all_services
            if keyword in s['name'].lower() or keyword in s['type_name'].lower()
        ]

    return render_template("service/services.html", services=all_services)

@app.route("/service/add", methods=["GET","POST"])
@login_required(role="admin")
def add_service_route():
    types = get_all_service_types()
    if request.method == "POST":
        data = request.form
        add_service(data["name"], int(data["service_type_id"]), float(data["price"]))
        return redirect(url_for("services"))
    return render_template("service/service_add.html", types=types)

@app.route("/service/edit/<int:id>", methods=["GET","POST"])
@login_required(role="admin")
def edit_service(id):
    services = get_all_services()
    service = next((s for s in services if s['id'] == id), None)
    if not service:
        flash("Dịch vụ không tồn tại!")
        return redirect(url_for("services"))

    if request.method == "POST":
        data = request.form
        db = get_connection()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE services SET name=%s, service_type_id=%s, price=%s WHERE id=%s",
            (data["name"], int(data["service_type_id"]), float(data["price"]), id)
        )
        db.commit()
        cursor.close()
        db.close()
        flash("Cập nhật dịch vụ thành công!")
        return redirect(url_for("services"))

    types = get_all_service_types()
    return render_template("service/service_edit.html", service=service, types=types)

@app.route("/service/delete/<int:id>")
@login_required(role="admin")
def delete_service(id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM services WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()
    flash("Xóa dịch vụ thành công!")
    return redirect(url_for("services"))

# -----------------------
# Medicine Types
# -----------------------
@app.route("/medicineTypes")
@login_required()
def medicine_types():
    keyword = request.args.get("keyword", "").strip().lower()
    types = get_all_medicine_types()

    if keyword:
        types = [t for t in types if keyword in t['name'].lower()]

    return render_template("medicineType/medicineTypes.html", types=types)


@app.route("/medicineType/add", methods=["GET","POST"])
@login_required(role="admin")
def add_medicine_type_route():
    if request.method == "POST":
        name = request.form["name"]
        add_medicine_type(name)
        flash("Thêm loại thuốc thành công!")
        return redirect(url_for("medicine_types"))
    return render_template("medicineType/medicineType_add.html")

@app.route("/medicineType/edit/<int:id>", methods=["GET","POST"])
@login_required(role="admin")
def edit_medicine_type_route(id):
    types = get_all_medicine_types()
    type_obj = next((t for t in types if t['id'] == id), None)
    if not type_obj:
        flash("Loại thuốc không tồn tại!")
        return redirect(url_for("medicine_types"))

    if request.method == "POST":
        name = request.form["name"]
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE medicine_types SET name=%s WHERE id=%s", (name, id))
        db.commit()
        cursor.close()
        db.close()
        flash("Cập nhật loại thuốc thành công!")
        return redirect(url_for("medicine_types"))

    return render_template("medicineType/medicineType_edit.html", type_obj=type_obj)


@app.route("/medicineType/delete/<int:id>")
@login_required(role="admin")
def delete_medicine_type_route(id):
    db = get_connection()
    cursor = db.cursor()

    # Xóa tất cả thuốc thuộc loại này trước
    cursor.execute("DELETE FROM medicines WHERE medicine_type_id=%s", (id,))

    # Xóa loại thuốc
    cursor.execute("DELETE FROM medicine_types WHERE id=%s", (id,))

    db.commit()
    cursor.close()
    db.close()
    flash("Xóa loại thuốc thành công!")
    return redirect(url_for("medicine_types"))


# -----------------------
# Medicines
# -----------------------
@app.route("/medicines")
@login_required()
def medicines():
    keyword = request.args.get("keyword", "").strip().lower()
    type_id = request.args.get("type_id", "")

    meds = get_all_medicines()
    types = get_all_medicine_types()  # để truyền ra dropdown

    # Lọc theo tên
    if keyword:
        meds = [m for m in meds if keyword in m['name'].lower()]

    # Lọc theo loại
    if type_id:
        try:
            type_id_int = int(type_id)
            meds = [m for m in meds if m['medicine_type_id'] == type_id_int]
        except ValueError:
            meds = []

    return render_template("medicine/medicines.html", medicines=meds, types=types)


@app.route("/medicine/add", methods=["GET","POST"])
@login_required(role="admin")
def add_medicine_route():
    types = get_all_medicine_types()
    if request.method == "POST":
        data = request.form
        add_medicine(
            data["name"],
            int(data["medicine_type_id"]),
            float(data["price"])
        )
        flash("Thêm thuốc thành công!")
        return redirect(url_for("medicines"))
    return render_template("medicine/medicine_add.html", types=types)

@app.route("/medicine/edit/<int:id>", methods=["GET","POST"])
@login_required(role="admin")
def edit_medicine(id):
    meds = get_all_medicines()
    medicine = next((m for m in meds if m['id'] == id), None)
    if not medicine:
        flash("Thuốc không tồn tại!")
        return redirect(url_for("medicines"))

    types = get_all_medicine_types()
    if request.method == "POST":
        data = request.form
        db = get_connection()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE medicines SET name=%s, medicine_type_id=%s, price=%s WHERE id=%s",
            (data["name"], int(data["medicine_type_id"]), float(data["price"]), id)
        )
        db.commit()
        cursor.close()
        db.close()
        flash("Cập nhật thuốc thành công!")
        return redirect(url_for("medicines"))

    return render_template("medicine/medicine_edit.html", medicine=medicine, types=types)

@app.route("/medicine/delete/<int:id>")
@login_required(role="admin")
def delete_medicine(id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM medicines WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()
    flash("Xóa thuốc thành công!")
    return redirect(url_for("medicines"))

# ==========================
# CRUD Bills + Thanh toán + In hóa đơn
# ==========================
@app.route("/bills")
@login_required()
def bills():
    all_bills = bill_dao.get_all()
    status_filter = request.args.get("status", "").strip().lower()
    if status_filter:
        all_bills = [b for b in all_bills if status_filter in b.status.lower()]
    return render_template("bill/bills.html", bills=all_bills)

@app.route("/bill/add/<int:appointment_id>", methods=["GET","POST"])
@login_required(role="admin")
def add_bill(appointment_id):
    appointment = appointment_dao.get_by_id(appointment_id)
    if not appointment:
        flash("Lịch hẹn không tồn tại!")
        return redirect(url_for("appointments"))

    if request.method == "POST":
        amount = float(request.form["amount"])
        bill_dao.create_from_appointment(appointment_id, amount)
        flash("Tạo hóa đơn thành công!")
        return redirect(url_for("bills"))

    return render_template("bill/bill_add.html", appointment=appointment)

@app.route("/bill/pay/<int:id>", methods=["GET","POST"])
@login_required()
def pay_bill(id):
    bill = bill_dao.get_by_id(id)
    if not bill:
        flash("Hóa đơn không tồn tại!")
        return redirect(url_for("bills"))

    if request.method == "POST":
        payment_method = request.form["payment_method"]
        bill_dao.update_status(bill.id, "Đã thanh toán", payment_method)
        flash("Thanh toán thành công!")
        return redirect(url_for("bills"))

    return render_template("bill/bill_pay.html", bill=bill)

@app.route("/bill/print/<int:id>")
@login_required()
def print_bill(id):
    bill = bill_dao.get_by_id(id)
    if not bill:
        flash("Hóa đơn không tồn tại!")
        return redirect(url_for("bills"))
    appointment = appointment_dao.get_by_id(bill.appointment_id)
    patient = patient_dao.get_by_id(appointment.patient_id)
    doctor = doctor_dao.get_by_id(appointment.doctor_id)
    return render_template("bill/bill_print.html", bill=bill, appointment=appointment, patient=patient, doctor=doctor)
# ====================
# RUN SERVER
# ====================
if __name__ == "__main__":
    app.run(debug=True)
