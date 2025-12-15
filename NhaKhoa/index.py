# index.py
from flask import Flask, render_template, redirect, request, session, url_for, flash, jsonify
from urllib.parse import unquote

from flask import Flask, render_template, redirect, request, session, url_for, flash
from functools import wraps
import bcrypt
import secrets
from datetime import datetime, timedelta
import requests
import json
from werkzeug.utils import secure_filename
import os
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient

from NhaKhoa import app
from NhaKhoa.daos.schedule_dao import ScheduleDAO
from NhaKhoa.daos.specialty_dao import SpecialtyDAO
# Import DAO và Models
from NhaKhoa.database.db import init_database, get_connection
from NhaKhoa.models.role import RoleEnum
from daos.user_dao import UserDAO
from daos.patient_dao import PatientDAO
from daos.doctor_dao import DoctorDAO
from daos.bill_dao import BillDAO
from daos.appointment_dao import AppointmentDAO
from daos.service_dao import ServiceDAO
from daos.serviceType_dao import ServiceTypeDAO
from daos.medicine_dao import MedicineDAO
from daos.medicineType_dao import MedicineTypeDAO

from NhaKhoa.models.user import User
from NhaKhoa.models.patient import Patient
from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.appointment import Appointment


# CONFIG FLASK-MAIL
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='youremail@gmail.com',  # Thay bằng Gmail của bạn
    MAIL_PASSWORD='yourapppassword'       # Thay bằng App Password
)
mail = Mail(app)

# GOOGLE OAUTH CONFIG
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# DECORATOR PHÂN QUYỀN
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

# INIT DAO
user_dao = UserDAO()
patient_dao = PatientDAO()
doctor_dao = DoctorDAO()
appointment_dao = AppointmentDAO()
bill_dao = BillDAO()
service_dao = ServiceDAO()
serviceType_dao = ServiceTypeDAO()
medicine_dao = MedicineDAO()
medicineType_dao = MedicineTypeDAO()
specialty_dao = SpecialtyDAO()
schedule_dao = ScheduleDAO()

@app.context_processor
def inject_role_enum():
    return dict(RoleEnum=RoleEnum)

# DASHBOARD
@app.route("/")
@app.route("/dashboard")
@login_required()
def dashboard():
    return render_template("index.html", user=session["user"], role=session["role"])

# Search
@app.route("/search")
def search():
    query = request.args.get("q", "")
    return f"Bạn đã tìm: {query}"

# ACCOUNT: REGISTER / LOGIN / LOGOUT
@app.route("/account/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        date_of_birth = request.form["dob"]

        if date_of_birth:
            format = '%Y-%m-%d'
            date_of_birth = datetime.strptime(date_of_birth, format)

        if password != confirm_password:
            return render_template("account/register.html", error="Mật khẩu không khớp!")

        if user_dao.get_by_username(username) or user_dao.get_by_username(email):
            return render_template("account/register.html", error="Tên tài khoản hoặc email đã tồn tại!")

        new_user = User(name=username, password=password, email=email)
        try:
            user_dao.register(new_user, date_of_birth)
        finally:
            flash("Đăng ký thành công! Vui lòng đăng nhập.")
        return redirect(url_for("login"))

    return render_template("account/register.html")

@app.route("/account/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form["username"].strip()
        password = request.form["password"]
        user = user_dao.login(username_or_email, password)
        if user:
            session["user"] = user.name
            session["user_id"] = user.id
            session["role"] = user.role_id
            return redirect(url_for("dashboard"))

        return render_template("account/login.html", error="Sai tài khoản hoặc mật khẩu!")
    return render_template("account/login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# PASSWORD RESET / CHANGE
@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()
        user = user_dao.get_by_username(email)
        if user:
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)
            user_dao.set_reset_token(user, token, expiry)
            reset_link = url_for("reset_password", token=token, _external=True)
            msg = Message(
                subject="Reset mật khẩu",
                sender=app.config["MAIL_USERNAME"],
                recipients=[user.email],
                body=f"Nhấn vào link để đổi mật khẩu: {reset_link}\nLink có hiệu lực 1 giờ."
            )
            mail.send(msg)
            flash("Chúng tôi đã gửi hướng dẫn reset mật khẩu đến email của bạn.")
            return redirect(url_for("login"))
        else:
            flash("Email không tồn tại!")
    return render_template("account/forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET","POST"])
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

@app.route("/change-password", methods=["GET","POST"])
@login_required()
def change_password():
    if request.method == "POST":
        current = request.form["current_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]
        user = user_dao.get_by_id(session["user_id"])
        if not user_dao.check_password(user, current):
            flash("Mật khẩu hiện tại không đúng!")
        elif new != confirm:
            flash("Mật khẩu mới không khớp!")
        else:
            user_dao.update_password(user, new)
            flash("Đổi mật khẩu thành công!")
            return redirect(url_for("dashboard"))
    return render_template("account/change_password.html")

# GOOGLE OAUTH LOGIN
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
            new_user = User(name=email, password="google_oauth", email=email, role_id=RoleEnum.PATIENT.value)
            user_dao.register(new_user)
        session["user"] = email
        session["role"] = RoleEnum.PATIENT.value
    return redirect(url_for("dashboard"))

# CRUD PATIENT
@app.route("/patients")
@login_required()
def patients():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip()

    if filter_by and keyword:
        all_patients = patient_dao.search(filter_by, keyword)
    else:
        all_patients = patient_dao.get_all()

    return render_template("patient/patients.html", patients=all_patients)
# CRUD Patient với ảnh

@app.route("/patient/add", methods=["GET", "POST"])
@login_required()
def add_patient():
    if request.method == "POST":
        data = request.form
        new_patient = Patient(
            name=data["name"],
            age=int(data["age"]),
            phone=data["phone"],
            address=data["address"]
        )

        # Upload ảnh
        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)  # tạo folder nếu chưa có
            file.save(os.path.join(upload_folder, filename))
            new_patient.image = filename  # gán tên file vào model

        patient_dao.add(new_patient)
        flash("Thêm bệnh nhân thành công!")
        return redirect(url_for("patients"))

    return render_template("patient/patient_add.html")
@app.route("/patient/doctors")
@login_required(role=RoleEnum.PATIENT.value)
def patient_doctors():
    doctors = doctor_dao.get_all()

    doctor_id = request.args.get("doctor_id")
    if doctor_id:
        try:
            doctor_id_int = int(doctor_id)
            doctors = [d for d in doctors if d.id == doctor_id_int]
        except ValueError:
            pass

    return render_template("patient/patient_doctors.html", doctors=doctors)

# @app.route('/appointments/create', methods=['POST'])
# def create_appointment():
#     data = request.get_json()
#
#     username = session.get("user")
#     if not username:
#         return jsonify({"success": False, "message": "User chưa đăng nhập!"})
#
#     user = user_dao.get_by_username(username)
#     if not user:
#         return jsonify({"success": False, "message": "User không tồn tại!"})
#
#     patient = patient_dao.get_by_user_id(user.id)
#     if not patient:
#         return jsonify({"success": False, "message": "Bệnh nhân chưa tồn tại!"})
#
#     try:
#         appointment_date = datetime.fromisoformat(data.get("appointment_date"))
#     except:
#         return jsonify({"success": False, "message": "Ngày giờ không hợp lệ!"})
#
#     new_appointment = Appointment(
#         patient_id=patient.id,
#         service_id=data.get('service_id'),
#         doctor_id=int(data.get('doctor_id')),
#         schedule_id=int(data.get('schedule_id')),
#         appointment_date=appointment_date,
#         description=data.get('description', ""),
#         name=data.get('name', f"Appointment-{patient.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}")
#     )
#
#     try:
#         appointment_dao.add(new_appointment)
#         doctor = doctor_dao.get_by_id(new_appointment.doctor_id)
#
#         return jsonify({
#             "success": True,
#             "message": "Đặt lịch thành công",
#             "event": {
#                 "id": new_appointment.id,
#                 "title": doctor.name if doctor else "Bác sĩ chưa xác định",
#                 "start": new_appointment.appointment_date.isoformat(),
#                 "description": new_appointment.description
#             }
#         })
#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)})
#


@app.route('/appointments/create', methods=['POST'])
def create_appointment():
    data = request.get_json()

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "User chưa đăng nhập!"})

    user = user_dao.get_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User không tồn tại!"})

    patient = patient_dao.get_by_user_id(user.id)
    if not patient:
        return jsonify({"success": False, "message": "Bệnh nhân chưa tồn tại!"})

    try:
        appointment_date = datetime.fromisoformat(data.get("appointment_date"))
    except:
        return jsonify({"success": False, "message": "Ngày giờ không hợp lệ!"})

    # ==== Check trùng lịch ====
    existing = appointment_dao.get_by_doctor_and_date(
        doctor_id=int(data.get('doctor_id')),
        appointment_date=appointment_date
    )
    if existing:
        return jsonify({"success": False, "message": "Lịch hẹn trùng! Vui lòng chọn thời gian khác."})
    # =========================

    new_appointment = Appointment(
        patient_id=patient.id,
        service_id=data.get('service_id'),
        doctor_id=int(data.get('doctor_id')),
        schedule_id=int(data.get('schedule_id')),
        appointment_date=appointment_date,
        description=data.get('description', ""),
        name=data.get('name', f"Appointment-{patient.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    )

    try:
        appointment_dao.add(new_appointment)
        doctor = doctor_dao.get_by_id(new_appointment.doctor_id)

        return jsonify({
            "success": True,
            "message": "Đặt lịch thành công",
            "event": {
                "id": new_appointment.id,
                "title": doctor.name if doctor else "Bác sĩ chưa xác định",
                "start": new_appointment.appointment_date.strftime("%Y-%m-%dT%H:%M")
                ,
                "description": new_appointment.description
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/appointments/cancel/<int:id>", methods=["POST"])
@login_required(role=RoleEnum.PATIENT.value)
def cancel_appointment(id):
    user = user_dao.get_by_id(session["user_id"])
    patient = patient_dao.get_by_user_id(user.id)
    appointment = appointment_dao.get_by_id(id)

    if not appointment or appointment.patient_id != patient.id:
        return jsonify({"success": False, "message": "Không tìm thấy lịch hẹn hoặc không có quyền!"})

    # Cập nhật trạng thái cancel
    appointment.active = 0
    appointment_dao.update(appointment)

    return jsonify({"success": True, "message": "Hủy lịch hẹn thành công!"})

@app.route("/appointments/events")
@login_required(role=RoleEnum.PATIENT.value)
def appointments_events():
    user = user_dao.get_by_id(session["user_id"])
    patient = patient_dao.get_by_user_id(user.id)
    if not patient:
        return jsonify([])

    appointments = appointment_dao.get_by_patient_id(patient.id)
    events = []
    for appt in appointments:
        events.append({
            "id": appt.id,
            "title": appt.doctor.name if appt.doctor else "Bác sĩ chưa xác định",
            "start": appt.appointment_date.strftime("%Y-%m-%dT%H:%M"),
            "extendedProps": {
                "id": appt.id,
                "description": appt.description
            }
        })

    return jsonify(events)

@app.route("/my_appointments")
@login_required(role=RoleEnum.USER.value)
def my_appointments():
    user = user_dao.get_by_id(session.get("user_id"))
    patient = patient_dao.get_by_user_id(user.id)
    if not patient:
        flash("Bệnh nhân không tồn tại!")
        return redirect(url_for("dashboard"))

    # Lấy appointment của patient
    appointments = appointment_dao.get_by_patient_id(patient.id)

    doctors = doctor_dao.get_all()
    services = service_dao.get_all_services()

    # Lấy tham số format từ query string
    response_format = request.args.get("format", "html").lower()

    events = []
    for appt in appointments:
        events.append({
            "id": appt.id,
            "title": appt.schedule.doctor.name if appt.schedule.doctor.name else "Bác sĩ chưa xác định",
            "start": appt.schedule.from_date.strftime("%Y-%m-%dT%H:%M"),
            "extendedProps": {
                "id": appt.id,
                "description": appt.description
            }
        })

    if response_format == "json":
        return jsonify(events)
    else:
        return render_template(
            "patient/patient_appointments.html",
            events=events,
            doctors=doctors,
            services=services
        )


@app.route("/doctors/by-service/<int:service_id>")
def doctors_by_service(service_id):
    doctors = doctor_dao.get_doctors_by_specialty(service_id)  # hoặc service_id nếu mapping đúng
    result = [{"id": d.id, "name": d.name} for d in doctors]
    return jsonify(result)
@app.route("/appointment/add_ajax", methods=["POST"])
@login_required(role=RoleEnum.PATIENT.value)
def add_appointment_ajax():
    data = request.json
    user = user_dao.get_by_id(session["user_id"])
    patient = patient_dao.get_by_user_id(user.id)

    new_appointment = Appointment(
        patient_id=patient.id,
        doctor_id=int(data["doctor_id"]),
        appointment_date=datetime.fromisoformat(data["appointment_date"]),
        description=data.get("description", "")
    )
    appointment_dao.add(new_appointment)
    doctor = doctor_dao.get_by_id(new_appointment.doctor_id)
    return {"success": True, "id": new_appointment.id, "doctor_name": doctor.name}



@app.route("/patient/edit/<int:id>", methods=["GET", "POST"])
@login_required()
def edit_patient(id):
    patient = patient_dao.get_by_id(id)
    if not patient:
        flash("Bệnh nhân không tồn tại!")
        return redirect(url_for("patients"))

    if request.method == "POST":
        data = request.form
        patient.name = data["name"]
        patient.age = int(data["age"])
        patient.phone = data["phone"]
        patient.address = data["address"]

        # Upload ảnh mới nếu có
        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            patient.image = filename  # cập nhật ảnh mới

        patient_dao.update(patient)
        flash("Cập nhật bệnh nhân thành công!")
        return redirect(url_for("patients"))

    return render_template("patient/patient_edit.html", patient=patient)

#
# @app.route("/patient/add", methods=["GET","POST"])
# @login_required()
# def add_patient():
#     if request.method == "POST":
#         data = request.form
#         new_patient = Patient(name=data["name"], age=int(data["age"]), phone=data["phone"], address=data["address"])
#         patient_dao.add(new_patient)
#         return redirect(url_for("patients"))
#     return render_template("patient/patient_add.html")
#
# @app.route("/patient/edit/<int:id>", methods=["GET","POST"])
# @login_required()
# def edit_patient(id):
#     patient = patient_dao.get_by_id(id)
#     if request.method == "POST":
#         data = request.form
#         patient.name = data["name"]
#         patient.age = int(data["age"])
#         patient.phone = data["phone"]
#         patient.address = data["address"]
#         patient_dao.update(patient)  # ✅ dùng DAO update
#         return redirect(url_for("patients"))
#     return render_template("patient/patient_edit.html", patient=patient)

@app.route("/patient/delete/<int:id>")
@login_required()
def delete_patient(id):
    patient_dao.delete(id)
    return redirect(url_for("patients"))

# CRUD DOCTOR
@app.route("/doctors")
@login_required()
def doctors():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip()
    if filter_by and keyword:
        all_doctors = doctor_dao.search(filter_by, keyword)
    else:
        all_doctors = doctor_dao.get_all()
    return render_template("doctor/doctors.html", doctors=all_doctors)

# @app.route("/doctor/add", methods=["GET","POST"])
# @login_required(role="admin")
# def add_doctor():
#     if request.method == "POST":
#         data = request.form
#         new_doctor = Doctor(name=data["name"], specialty=data["specialty"], phone=data["phone"])
#         doctor_dao.add(new_doctor)
#         return redirect(url_for("doctors"))
#     return render_template("doctor/doctor_add.html")

@app.route("/doctor/add", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def add_doctor():
    if request.method == "POST":
        data = request.form
        new_doctor = Doctor(
            name=data["name"],
            specialty=data["specialty"],
            phone=data["phone"]
        )

        # Upload ảnh
        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)  # tạo folder nếu chưa có
            file.save(os.path.join(upload_folder, filename))
            new_doctor.image = filename

        doctor_dao.add(new_doctor)
        return redirect(url_for("doctors"))
    return render_template("doctor/doctor_add.html")

# @app.route("/doctor/edit/<int:id>", methods=["GET","POST"])
# @login_required(role="admin")
# def edit_doctor(id):
#     doctor = doctor_dao.get_by_id(id)
#     if request.method == "POST":
#         data = request.form
#         doctor.name = data["name"]
#         doctor.specialty = data["specialty"]
#         doctor.phone = data["phone"]
#         doctor_dao.update(doctor)  # ✅ dùng DAO update
#         return redirect(url_for("doctors"))
#     return render_template("doctor/doctor_edit.html", doctor=doctor)

@app.route("/doctor/edit/<int:id>", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def edit_doctor(id):
    doctor = doctor_dao.get_by_id(id)
    specialty_name = specialty_dao.get_name_by_id(doctor.specialty_id)
    if request.method == "POST":
        data = request.form
        doctor.name = data["name"]
        doctor.specialty = data["specialty"]
        doctor.phone = data["phone"]

        # Upload ảnh
        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.static_folder, 'uploads', filename))
            doctor.image = filename

        doctor_dao.update(doctor)
        return redirect(url_for("doctors"))
    return render_template("doctor/doctor_edit.html", doctor=doctor, specialty_name=specialty_name)

@app.route("/doctor/delete/<int:id>")
@login_required(role=RoleEnum.ADMIN.value)
def delete_doctor(id):
    doctor_dao.delete(id)
    return redirect(url_for("doctors"))

# CRUD LỊCH HẸN (APPOINTMENT)
# @app.route("/appointments")
# @login_required()
# def appointments():
#     filter_by = request.args.get("filter_by")
#     keyword = request.args.get("keyword", "").strip()
#     if filter_by and keyword:
#         all_appointments = appointment_dao.search(filter_by, keyword)
#     else:
#         all_appointments = appointment_dao.get_all()
#     return render_template("appointment/appointments.html", appointments=all_appointments)

@app.route("/appointments")
def appointments():
    filter_by = request.args.get('filter_by')
    keyword = request.args.get('keyword', '').lower()

    # Get appointments with all relationships preloaded
    appointments = appointment_dao.get_all_with_doctor_names()

    # Apply filtering if needed
    if filter_by and keyword:
        if filter_by == 'patient':
            appointments = [
                a for a in appointments
                if a.patient and keyword in a.patient.name.lower()
            ]
        elif filter_by == 'doctor':
            appointments = [
                a for a in appointments
                if a.schedule and a.schedule.doctor and keyword in a.schedule.doctor.name.lower()
            ]
        elif filter_by == 'date':
            try:
                filter_date = datetime.strptime(keyword, '%Y-%m-%d').date()
                appointments = [
                    a for a in appointments
                    if a.schedule and a.schedule.from_date.date() == filter_date
                ]
            except ValueError:
                pass  # Ignore invalid date format

    return render_template("appointment/appointments.html", appointments=appointments)



@app.route("/appointment/add", methods=["GET","POST"])
@login_required()
def add_appointment():
    err = ""
    patients = patient_dao.get_all()
    specialties = specialty_dao.get_all()
    available_schedules = []
    datetime_obj_str = ""
    schedule_id = None
    specialty_name = ""
    doctor_name = ""
    user = user_dao.get_by_id(session["user_id"])

    specialty_id = request.args.get('specialty_id', type=int)
    patient_id = request.args.get('patient_id', type=int)
    doctor_id = request.args.get("doctor_id", type=int)
    appt_date = request.args.get('appointment_date', type=str)
    data = request.form


    doctors = []
    if specialty_id:
        doctors = doctor_dao.get_doctors_by_specialty(specialty_id)
        specialty_name = specialty_dao.get_name_by_id(specialty_id)

    if appt_date:
        appt_date = unquote(appt_date)
        format = '%Y-%m-%dT%H:%M'
        datetime_obj = datetime.strptime(appt_date, format)
        datetime_obj_str = datetime_obj.strftime(format)

        if doctor_id:
            available_schedules = schedule_dao.get_all_available_schedules(doctor_id)
            available_schedules = schedule_dao.get_available_schedules_by_time(
                available_schedules,
                datetime_obj
            )
            # for s in available_schedules:
            #     print(s.id)
            #     pass
            if available_schedules is None:
                err = "Giờ chọn phải nằm trong khoảng từ 9 đến 16"
                return err

        schedule_id = data.get("schedule_id")
        if schedule_id is not None:
            schedule_id = int(data.get("schedule_id"))

    if session.get('role') != RoleEnum.PATIENT.value:
        patient_id = patient_dao.get_by_user_id(user.id).id

    if request.method == "POST":
        doctor_id = int(data.get("doctor_id"))
        doctor_name = doctor_dao.get_by_id(doctor_id).name
        patient_id = patient_id
        schedule_id = data.get("schedule_id")
        description = data.get("description", "")
        name = f'Cuộc hẹn {specialty_name} với bác sĩ {doctor_name}'
        print(f'{patient_id}{patient_id}')
        new_appointment = Appointment(
            name=name,
            patient_id=patient_id,
            schedule_id=schedule_id,
            description=description
        )
        # print(f'Appointment {new_appointment.patient_id} - {new_appointment.schedule_id} - {new_appointment.description}')
        appointment_dao.add(new_appointment)
        return redirect(url_for("appointments"))
    return render_template("appointment/appointment_add.html",
                           patients=patients,
                           doctors=doctors,
                           specialties=specialties,
                           selected_doctor=doctor_id,
                           selected_specialty=specialty_id,
                           selected_patient=patient_id,
                           available_schedules=available_schedules,
                           fm_datetime=datetime_obj_str,
                           err=err)

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
        appointment_dao.update(appointment)  # ✅ dùng DAO update
        return redirect(url_for("appointments"))
    return render_template("appointment/appointment_edit.html", appointment=appointment, patients=patients, doctors=doctors)

@app.route("/appointment/delete/<int:id>")
@login_required()
def delete_appointment(id):
    appointment_dao.delete(id)
    return redirect(url_for("appointments"))

# CRUD DỊCH VỤ / LOẠI DỊCH VỤ (SERVICE / SERVICE TYPE)
@app.route("/service-types")
@login_required()
def service_types():
    return render_template("service/service_types.html", types=serviceType_dao.get_all_service_types())

@app.route("/service-type/add", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def add_service_type():
    if request.method == "POST":
        name = request.form["name"]
        serviceType_dao.add(name)
        flash("Thêm loại dịch vụ thành công!")
        return redirect(url_for("service_types"))
    return render_template("service/service_type_add.html")

@app.route("/services")
@login_required()
def services():
    filter_by = request.args.get("filter_by", "name")  # Mặc định filter theo "name"
    keyword = request.args.get("keyword", "").strip()
    if keyword:
        all_services = service_dao.search(filter_by, keyword)
    else:
        all_services = service_dao.get_all_services()
    return render_template("service/services.html", services=all_services)

@app.route("/service/add", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def add_service():
    types = serviceType_dao.get_all_service_types()
    if request.method == "POST":
        data = request.form
        service_dao.add_service(data["name"], int(data["service_type_id"]), float(data["price"]))
        flash("Thêm dịch vụ thành công!")
        return redirect(url_for("services"))
    return render_template("service/service_add.html", types=types)

@app.route("/service/edit/<int:id>", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def edit_service(id):
    service = service_dao.get_service_by_id(id)
    if not service:
        flash("Dịch vụ không tồn tại!")
        return redirect(url_for("services"))
    types = serviceType_dao.get_all_service_types()
    if request.method == "POST":
        data = request.form
        service.name = data["name"]
        service.service_type_id = int(data["service_type_id"])
        service.price = float(data["price"])
        service_dao.update_service(service)  # ✅ dùng DAO update
        flash("Cập nhật dịch vụ thành công!")
        return redirect(url_for("services"))
    return render_template("service/service_edit.html", service=service, types=types)

@app.route("/service/delete/<int:id>")
@login_required(role=RoleEnum.ADMIN.value)
def delete_service(id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM services WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()
    flash("Xóa dịch vụ thành công!")
    return redirect(url_for("services"))

# CRUD THUỐC / LOẠI THUỐC (MEDICINE / MEDICINE TYPE)
@app.route("/medicineTypes")
@login_required()
def medicine_types():
    keyword = request.args.get("keyword", "").strip().lower()
    types = medicineType_dao.get_all_medicine_types()
    if keyword:
        types = [t for t in types if keyword in t.name.lower()]
    return render_template("medicineType/medicineTypes.html", types=types)


@app.route("/medicineType/add", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def add_medicine_type():
    if request.method == "POST":
        name = request.form["name"]
        medicineType_dao.add_medicine_type(name)
        flash("Thêm loại thuốc thành công!")
        return redirect(url_for("medicine_types"))
    return render_template("medicineType/medicineType_add.html")

@app.route("/medicine-type/edit/<int:id>", methods=["GET", "POST"])
@login_required(role=RoleEnum.ADMIN.value)
def edit_medicine_type(id):
    type_to_edit = medicineType_dao.get_by_id(id)  # dùng instance đã init sẵn

    if not type_to_edit:
        flash("Loại thuốc không tồn tại!")
        return redirect(url_for("medicine_types"))

    if request.method == "POST":
        new_name = request.form.get("name")
        type_to_edit.name = new_name
        medicineType_dao.update(type_to_edit)
        flash("Cập nhật loại thuốc thành công!")
        return redirect(url_for("medicine_types"))

    return render_template("medicineType/medicineType_edit.html", type_obj=type_to_edit)

@app.route("/medicine-type/delete/<int:id>")
@login_required(role=RoleEnum.ADMIN.value)
def delete_medicine_type(id):
    # Gọi DAO để xóa
    success = medicineType_dao.delete(id)

    return redirect(url_for("medicine_types"))

@app.route("/medicines")
@login_required()
def medicines():
    keyword = request.args.get("keyword", "").strip()
    type_id = request.args.get("type_id")
    type_id_int = int(type_id) if type_id else None
    meds = medicine_dao.search_medicines(keyword, type_id_int)
    types = medicineType_dao.get_all_medicine_types()
    return render_template("medicine/medicines.html", medicines=meds, types=types)

@app.route("/medicine/add", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def add_medicine():
    types = medicineType_dao.get_all_medicine_types()
    if request.method == "POST":
        data = request.form
        medicine_dao.add_medicine(data["name"], int(data["medicine_type_id"]), float(data["price"]))
        flash("Thêm thuốc thành công!")
        return redirect(url_for("medicines"))
    return render_template("medicine/medicine_add.html", types=types)

# CRUD THUỐC / LOẠI THUỐC (MEDICINE / MEDICINE TYPE)
@app.route("/medicine/edit/<int:id>", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
def edit_medicine(id):
    medicine = medicine_dao.get_by_id(id)
    if not medicine:
        flash("Thuốc không tồn tại!")
        return redirect(url_for("medicines"))
    types = medicineType_dao.get_all_medicine_types()
    if request.method == "POST":
        data = request.form
        medicine.name = data["name"]
        medicine.medicine_type_id = int(data["medicine_type_id"])
        medicine.price = float(data["price"])
        medicine_dao.update_medicine(medicine)  # ✅ dùng DAO update
        flash("Cập nhật thuốc thành công!")
        return redirect(url_for("medicines"))
    return render_template("medicine/medicine_edit.html", medicine=medicine, types=types)

@app.route("/medicine/delete/<int:id>")
@login_required(role=RoleEnum.ADMIN.value)
def delete_medicine(id):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM medicines WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()
    flash("Xóa thuốc thành công!")
    return redirect(url_for("medicines"))

# CRUD HÓA ĐƠN / THANH TOÁN (BILLS / PAYMENT)
@app.route("/bills")
@login_required()
def bills():
    all_bills = bill_dao.get_all()
    status_filter = request.args.get("status", "").strip().lower()
    if status_filter:
        all_bills = [b for b in all_bills if status_filter in b.status.lower()]
    return render_template("bill/bills.html", bills=all_bills)

@app.route("/bill/add/<int:appointment_id>", methods=["GET","POST"])
@login_required(role=RoleEnum.ADMIN.value)
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

# RUN SERVER
if __name__ == "__main__":
    with app.app_context():
        init_database()
        app.run(debug=True)

