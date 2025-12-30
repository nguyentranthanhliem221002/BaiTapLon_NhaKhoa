# index.py
from flask import Flask, render_template, redirect, request, session, url_for, flash, jsonify
from urllib.parse import unquote

from flask import Flask, render_template, redirect, request, session, url_for, flash
from functools import wraps
import bcrypt
import requests, json, uuid, hashlib, hmac
import secrets
from datetime import datetime, timedelta,date
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
from daos.thongke_dao import ThongKeDAO

from NhaKhoa.models.user import User
from NhaKhoa.models.patient import Patient
from NhaKhoa.models.doctor import Doctor
from NhaKhoa.models.appointment import Appointment

MOMO_PARTNER_CODE = "MOMO5RGX20191128"
MOMO_ACCESS_KEY = "M8brj9K6E22vXoDB"
MOMO_SECRET_KEY = "nqQiVSgDMy809JoPF6OzP5OdBUB550Y4"
MOMO_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
MOMO_RETURN_URL = "http://127.0.0.1:5000/bill/momo_return"
MOMO_NOTIFY_URL = "http://127.0.0.1:5000/bill/momo_notify"

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='youremail@gmail.com',  # Thay bằng Gmail của bạn
    MAIL_PASSWORD='yourapppassword'       # Thay bằng App Password
)
mail = Mail(app)

GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# DECORATOR PHÂN QUYỀN
def login_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session:
                flash("Vui lòng đăng nhập!")
                return redirect(url_for("login"))
            if roles and session.get("role") not in roles:
                flash("Bạn không có quyền truy cập!")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


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
thongke_dao = ThongKeDAO()
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

@app.route("/patients")
@login_required()
def patients():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip()

    if filter_by and keyword:
        all_patients = patient_dao.search(filter_by, keyword)
    else:
        all_patients = patient_dao.get_all()

    return render_template(
        "patient/patients.html",
        patients=all_patients
    )

@app.route("/patient/add", methods=["GET", "POST"])
@login_required()
def add_patient():
    if request.method == "POST":
        data = request.form

        new_patient = Patient(
            name=data["name"],
            age=int(data["age"]),
            phone=data["phone"],
            address=data["address"],
            status=0
        )

        # Upload ảnh
        file = request.files.get("image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.static_folder, "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            new_patient.image = filename

        patient_dao.add(new_patient)
        flash("Thêm bệnh nhân thành công!")
        return redirect(url_for("patients"))

    return render_template("patient/patient_add.html")

@app.route("/patient/doctors")
@login_required(RoleEnum.USER.value, RoleEnum.PATIENT.value)
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

@app.route('/appointments/create', methods=['POST'])
@login_required()
def create_appointment():
    data = request.get_json()

    user = user_dao.get_by_id(session["user_id"])
    patient = patient_dao.get_by_user_id(user.id)

    schedule_id = int(data.get("schedule_id"))
    schedule = schedule_dao.get_by_id(schedule_id)

    if not schedule:
        return jsonify(success=False, message="Khung giờ không tồn tại")

    if appointment_dao.exists_by_patient_and_schedule(patient.id, schedule_id):
        return jsonify(
            success=False,
            message="Bạn đã có lịch hẹn ở khung giờ này rồi!"
        )

    if schedule.num_patient >= schedule.max_patient:
        return jsonify(success=False, message="Khung giờ đã đầy")

    # ✅ tăng slot
    schedule.num_patient += 1
    schedule_dao.update(schedule)

    appointment = Appointment(
        patient_id=patient.id,
        schedule_id=schedule.id,
        description=data.get("description", ""),
        name=f"Lịch khám với BS. {schedule.doctor.name}"
    )
    appointment_dao.add(appointment)

    return jsonify({
        "success": True,
        "appointment_id": appointment.id,
        "doctor_name": schedule.doctor.name,
        "start_time": schedule.from_date.isoformat()
    })

@app.route("/appointments/cancel/<int:id>", methods=["POST"])
@login_required(RoleEnum.USER.value)
def cancel_appointment(id):
    user = user_dao.get_by_id(session["user_id"])
    patient = patient_dao.get_by_user_id(user.id)
    appointment = appointment_dao.get_by_id(id)

    if not appointment or appointment.patient_id != patient.id:
        return jsonify({"success": False, "message": "Không có quyền hủy lịch!"})

    if appointment_dao.cancel(id):
        return jsonify({"success": True, "message": "Hủy lịch hẹn thành công! Lịch đã được ẩn."})
    else:
        return jsonify({"success": False, "message": "Lịch đã hủy trước đó hoặc lỗi hệ thống."})

@app.route("/appointments/events")
@login_required(RoleEnum.USER.value)
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
@login_required(RoleEnum.USER.value, RoleEnum.PATIENT.value)
def my_appointments():
    user = user_dao.get_by_id(session.get("user_id"))
    if not user:
        flash("Vui lòng đăng nhập lại!", "danger")
        return redirect(url_for("login"))

    patient = patient_dao.get_by_user_id(user.id)
    if not patient:
        flash("Bệnh nhân không tồn tại!", "danger")
        return redirect(url_for("dashboard"))

    service_types = serviceType_dao.get_all_service_types()

    appointments = appointment_dao.get_by_patient_id(patient.id)

    events = []
    for appt in appointments:
        doctor_name = appt.schedule.doctor.name if appt.schedule and appt.schedule.doctor else "Chưa xác định"
        events.append({
            "id": appt.id,
            "title": doctor_name,
            "start": appt.schedule.from_date.isoformat() if appt.schedule else "",
            "extendedProps": {
                "description": appt.description or "Không có mô tả"
            }
        })

    # Xác định role hiện tại
    current_role_name = "USER" if user.role_id == RoleEnum.USER.value else "PATIENT"

    # Chỉ khi là PATIENT mới lấy danh sách tất cả bệnh nhân để chọn
    all_patients = []
    if current_role_name == "PATIENT":
        all_patients = patient_dao.get_all()  # <-- Lấy hết bệnh nhân active

    return render_template(
        "patient/patient_appointments.html",
        events=events,
        service_types=service_types,
        patient_id=patient.id,           # patient mặc định của user hiện tại
        current_role=current_role_name,
        all_patients=all_patients        # <-- Truyền danh sách bệnh nhân vào template
    )
@app.route("/api/services_by_type/<int:type_id>")
def api_services_by_type(type_id):
    services = service_dao.get_services_by_type(type_id)
    return jsonify([{"id": s.id, "name": s.name, "price": s.price} for s in services])

@app.route("/api/available_schedules")
def api_available_schedules():
    doctor_id = request.args.get('doctor_id', type=int)
    date_str = request.args.get('date')

    if not doctor_id or not date_str:
        return jsonify([])

    try:
        # Xử lý linh hoạt: chỉ ngày hoặc có giờ
        if 'T' in date_str:
            # Có giờ: "2025-12-30T10:00"
            if len(date_str) == 16:
                date_str += ':00'
            dt = datetime.fromisoformat(date_str)
        else:
            # Chỉ ngày: "2025-12-30"
            dt = datetime.strptime(date_str, "%Y-%m-%d")

        selected_date = dt.date()

        schedules = schedule_dao.get_available_schedules_by_doctor_and_date(doctor_id, selected_date)

        return jsonify([{
            "id": s.id,
            "from": s.from_date.strftime("%H:%M"),
            "to": s.to_date.strftime("%H:%M"),
        } for s in schedules])

    except Exception as e:
        print("Lỗi load lịch:", e)
        return jsonify([])

@app.route("/doctors/by-service/<int:service_id>")
def doctors_by_service(service_id):
    doctors = doctor_dao.get_doctors_by_specialty(service_id)  # hoặc service_id nếu mapping đúng
    result = [{"id": d.id, "name": d.name} for d in doctors]
    return jsonify(result)

@app.route("/api/doctors_by_service_type/<int:service_type_id>")
def api_doctors_by_service_type(service_type_id):
    service_type = serviceType_dao.get_by_id(service_type_id)
    if service_type and hasattr(service_type, 'specialty_id') and service_type.specialty_id:
        doctors = doctor_dao.get_doctors_by_specialty(service_type.specialty_id)
    else:
        doctors = doctor_dao.get_all()  # fallback
    return jsonify([{"id": d.id, "name": d.name} for d in doctors])
@app.route("/appointment/add_ajax", methods=["POST"])
@login_required(RoleEnum.USER.value)
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
    patient = patient_dao.get_by_id(id)  # đã filter status = 0
    if not patient:
        flash("Bệnh nhân không tồn tại hoặc đã bị xóa!")
        return redirect(url_for("patients"))

    if request.method == "POST":
        data = request.form

        patient.name = data["name"]
        patient.age = int(data["age"])
        patient.phone = data["phone"]
        patient.address = data["address"]

        # Upload ảnh mới nếu có
        file = request.files.get("image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.static_folder, "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            patient.image = filename

        patient_dao.update(patient)
        flash("Cập nhật bệnh nhân thành công!")
        return redirect(url_for("patients"))

    return render_template(
        "patient/patient_edit.html",
        patient=patient
    )

@app.route("/patient/delete/<int:id>")
@login_required()
def delete_patient(id):
    patient = patient_dao.get_by_id(id)
    if not patient:
        flash("Bệnh nhân không tồn tại!")
        return redirect(url_for("patients"))

    patient_dao.delete(id)
    flash("Đã xóa bệnh nhân!")
    return redirect(url_for("patients"))

@app.route("/doctors")
@login_required(RoleEnum.ADMIN.value)  # Giả sử chỉ admin xem danh sách bác sĩ
def doctors():
    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip().lower()

    if filter_by and keyword:
        all_doctors = doctor_dao.search(filter_by, keyword)
    else:
        all_doctors = doctor_dao.get_all()  # hoặc get_all_active() nếu có

    # Tạo list doctors với thêm tên chuyên khoa
    doctors_with_specialty = []
    for doc in all_doctors:
        specialty_name = specialty_dao.get_name_by_id(doc.specialty_id) or "Chưa xác định"
        doctors_with_specialty.append({
            "id": doc.id,
            "name": doc.name,
            "specialty_name": specialty_name,
            "phone": doc.phone,
            "image": doc.image
        })

    return render_template(
        "doctor/doctors.html",
        doctors=doctors_with_specialty
    )
@app.route("/doctor/add", methods=["GET", "POST"])
@login_required(RoleEnum.ADMIN.value)
def add_doctor():
    specialties = specialty_dao.get_all()

    if request.method == "POST":
        data = request.form

        new_doctor = Doctor(
            name=data.get("name"),
            specialty_id=int(data.get("specialty_id")),  # ✅ FIX
            phone=data.get("phone")
        )

        # Upload ảnh
        file = request.files.get("image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.static_folder, "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            new_doctor.image = filename

        doctor_dao.add(new_doctor)
        return redirect(url_for("doctors"))

    return render_template("doctor/doctor_add.html", specialties=specialties)

@app.route("/doctor/edit/<int:id>", methods=["GET", "POST"])
@login_required(RoleEnum.ADMIN.value)
def edit_doctor(id):
    doctor = doctor_dao.get_by_id(id)
    if not doctor:
        flash("Bác sĩ không tồn tại!", "danger")
        return redirect(url_for("doctors"))

    if request.method == "POST":
        data = request.form

        doctor.name = data["name"]
        doctor.phone = data["phone"]

        # Lấy specialty_id từ form (là ID số)
        try:
            specialty_id = int(data["specialty"])
            doctor.specialty_id = specialty_id
        except (ValueError, KeyError):
            flash("Vui lòng chọn chuyên khoa hợp lệ!", "danger")
            return redirect(url_for("edit_doctor", id=id))

        # Upload ảnh
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.static_folder, 'uploads', filename)
            file.save(upload_path)
            doctor.image = filename

        doctor_dao.update(doctor)
        flash("Cập nhật thông tin bác sĩ thành công!", "success")
        return redirect(url_for("doctors"))

    # GET: hiển thị form
    specialties = specialty_dao.get_all()  # Lấy danh sách chuyên khoa
    return render_template(
        "doctor/doctor_edit.html",
        doctor=doctor,
        specialties=specialties
    )

@app.route("/doctor/delete/<int:id>")
@login_required(RoleEnum.ADMIN.value)
def delete_doctor(id):
    doctor_dao.delete(id)
    return redirect(url_for("doctors"))

# @app.route("/appointments")
# def appointments():
#     filter_by = request.args.get('filter_by')
#     keyword = request.args.get('keyword', '').lower()
#
#     # Get appointments with all relationships preloaded
#     appointments = appointment_dao.get_all_with_doctor_names()
#
#     # Apply filtering if needed
#     if filter_by and keyword:
#         if filter_by == 'patient':
#             appointments = [
#                 a for a in appointments
#                 if a.patient and keyword in a.patient.name.lower()
#             ]
#         elif filter_by == 'doctor':
#             appointments = [
#                 a for a in appointments
#                 if a.schedule and a.schedule.doctor and keyword in a.schedule.doctor.name.lower()
#             ]
#         elif filter_by == 'date':
#             try:
#                 filter_date = datetime.strptime(keyword, '%Y-%m-%d').date()
#                 appointments = [
#                     a for a in appointments
#                     if a.schedule and a.schedule.from_date.date() == filter_date
#                 ]
#             except ValueError:
#                 pass  # Ignore invalid date format
#
#     return render_template("appointment/appointments.html", appointments=appointments)

@app.route("/appointments")
def appointments():
    filter_by = request.args.get('filter_by')
    keyword = request.args.get('keyword', '').lower()

    role = session.get("role")

    if role == RoleEnum.ADMIN.value:
        appointments = appointment_dao.get_all_with_doctor_names()

    elif role == RoleEnum.DOCTOR.value:
        user_id = session.get("user_id")
        doctor = doctor_dao.get_by_user_id(user_id)
        if not doctor:
            appointments = []
        else:
            appointments = appointment_dao.get_by_doctor_id(doctor.id)

    else:
        appointments = []

    # Filter (giữ nguyên)
    if filter_by and keyword:
        if filter_by == 'patient':
            appointments = [a for a in appointments if a.patient and keyword in a.patient.name.lower()]
        elif filter_by == 'doctor':
            appointments = [a for a in appointments if a.schedule and a.schedule.doctor and keyword in a.schedule.doctor.name.lower()]

    return render_template(
        "appointment/appointments.html",
        appointments=appointments
    )

@app.route("/appointment/add", methods=["GET", "POST"])
@login_required()
def add_appointment():
    err = ""
    patients = patient_dao.get_all()
    service_types = serviceType_dao.get_all_service_types()
    services = []
    doctors = []
    available_schedules = []
    datetime_obj_str = ""

    service_type_id = request.args.get('service_type_id', type=int)
    service_id = request.args.get('service_id', type=int)
    doctor_id = request.args.get('doctor_id', type=int)
    patient_id = request.args.get('patient_id', type=int)
    appt_date = request.args.get('appointment_date')

    user = user_dao.get_by_id(session["user_id"])

    if session.get('role') != RoleEnum.PATIENT.value and session.get('role') != RoleEnum.ADMIN.value:
        patient = patient_dao.get_by_user_id(user.id)
        if not patient:
            flash("Bệnh nhân không tồn tại!", "danger")
            return redirect(url_for("appointments"))
        patient_id = patient.id

    # else: nhân viên/admin có thể chọn bệnh nhân qua dropdown → sẽ lấy từ form khi POST

    # === LOAD DỮ LIỆU THEO BƯỚC ===
    if service_type_id:
        services = service_dao.get_services_by_type(service_type_id)

    if service_id:
        # Có thể lọc bác sĩ theo chuyên khoa liên quan đến dịch vụ ở đây (nếu có quan hệ)
        # Hiện tại lấy tất cả bác sĩ
        doctors = doctor_dao.get_all()

    # === XỬ LÝ NGÀY GIỜ VÀ LỊCH TRỐNG ===
    if appt_date:
        appt_date = unquote(appt_date)
        try:
            datetime_obj = datetime.strptime(appt_date, '%Y-%m-%dT%H:%M')
            datetime_obj_str = datetime_obj.strftime('%Y-%m-%dT%H:%M')

            if doctor_id:
                all_schedules = schedule_dao.get_all_available_schedules(doctor_id)
                available_schedules = schedule_dao.get_available_schedules_by_time(all_schedules, datetime_obj)
                if not available_schedules:
                    err = "Không có khung giờ trống vào thời điểm này. Vui lòng chọn giờ hoặc bác sĩ khác."
        except ValueError:
            err = "Định dạng ngày giờ không hợp lệ."

    # === XỬ LÝ POST – ĐẶT LỊCH ===
    if request.method == "POST":
        data = request.form

        # Lấy từ hidden fields (an toàn hơn args)
        patient_id_post = data.get("patient_id")
        service_id_post = data.get("service_id")
        doctor_id_post = data.get("doctor_id")
        schedule_id = data.get("schedule_id")
        description = data.get("description", "").strip()

        # Validate đầy đủ các trường bắt buộc
        if not all([patient_id_post, service_id_post, doctor_id_post, schedule_id]):
            flash("Thiếu thông tin cần thiết để đặt lịch. Vui lòng thử lại từ đầu.", "danger")
            return redirect(url_for("add_appointment"))

        try:
            patient_id_post = int(patient_id_post)
            service_id_post = int(service_id_post)
            doctor_id_post = int(doctor_id_post)
            schedule_id = int(schedule_id)
        except ValueError:
            flash("Dữ liệu không hợp lệ.", "danger")
            return redirect(url_for("add_appointment"))

        # Lấy object và kiểm tra tồn tại
        service = service_dao.get_service_by_id(service_id_post)
        doctor = doctor_dao.get_by_id(doctor_id_post)

        if not service:
            flash("Dịch vụ không tồn tại hoặc đã bị xóa.", "danger")
            return redirect(url_for("add_appointment"))

        if not doctor:
            flash("Bác sĩ không tồn tại hoặc không khả dụng.", "danger")
            return redirect(url_for("add_appointment"))

        # Tạo tên lịch hẹn
        name = f'Cuộc hẹn {service.name} với BS. {doctor.name}'

        # Tạo appointment
        new_appointment = Appointment(
            name=name,
            patient_id=patient_id_post,
            schedule_id=schedule_id,
            description=description
        )

        try:
            appointment_dao.add(new_appointment)
            flash("Đặt lịch hẹn thành công!", "success")
        except Exception as e:
            flash("Có lỗi khi lưu lịch hẹn. Vui lòng thử lại.", "danger")
            print(e)  # Để debug, sau này thay bằng logger

        return redirect(url_for("appointments"))

    # === RENDER TEMPLATE (GET) ===
    return render_template(
        "appointment/appointment_add.html",
        patients=patients,
        service_types=service_types,
        services=services,
        doctors=doctors,
        selected_service_type=service_type_id,
        selected_service=service_id,
        selected_doctor=doctor_id,
        selected_patient=patient_id,
        available_schedules=available_schedules,
        fm_datetime=datetime_obj_str,
        selected_datetime=appt_date,  # dùng cho hidden field nếu cần
        err=err
    )

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
@login_required(RoleEnum.ADMIN.value)
def delete_appointment(id):
    if appointment_dao.cancel(id):
        flash("Lịch hẹn đã được hủy thành công!", "success")
    else:
        flash("Lịch hẹn không tồn tại hoặc đã hủy trước đó.", "warning")
    return redirect(url_for("appointments"))

@app.route("/service-types")
@login_required()
def serviceTypes():
    return render_template("serviceTypes/serviceTypes.html", types=serviceType_dao.get_all_service_types())

@app.route("/service-type/add", methods=["GET","POST"])
@login_required(RoleEnum.ADMIN.value)
def add_service_type():
    if request.method == "POST":
        name = request.form["name"]
        serviceType_dao.add(name)
        flash("Thêm loại dịch vụ thành công!")
        return redirect(url_for("serviceTypes"))
    return render_template("serviceTypes/serviceType_add.html")

@app.route("/service-type/edit/<int:id>", methods=["GET", "POST"])
@login_required(RoleEnum.ADMIN.value)
def edit_service_type(id):
    service_type = serviceType_dao.get_by_id(id)
    if not service_type:
        flash("Loại dịch vụ không tồn tại hoặc đã bị xóa!", "danger")
        return redirect(url_for("serviceTypes"))

    if request.method == "POST":
        new_name = request.form["name"].strip()
        if not new_name:
            flash("Tên loại dịch vụ không được để trống!", "danger")
        else:
            service_type.name = new_name
            serviceType_dao.update(service_type)
            flash("Cập nhật loại dịch vụ thành công!", "success")
            return redirect(url_for("serviceTypes"))

    return render_template("serviceTypes/serviceType_edit.html", type=service_type)

@app.route("/service-type/delete/<int:id>")
@login_required(RoleEnum.ADMIN.value)
def delete_service_type(id):
    serviceType_dao.soft_delete(id)  # DAO tự flash thông báo chi tiết
    return redirect(url_for("serviceTypes"))

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
@login_required(RoleEnum.ADMIN.value)
def add_service():
    types = serviceType_dao.get_all_service_types()
    if request.method == "POST":
        data = request.form
        service_dao.add_service(data["name"], int(data["service_type_id"]), float(data["price"]))
        flash("Thêm dịch vụ thành công!")
        return redirect(url_for("services"))
    return render_template("service/service_add.html", types=types)

@app.route("/service/edit/<int:id>", methods=["GET","POST"])
@login_required(RoleEnum.ADMIN.value)
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
@login_required(RoleEnum.ADMIN.value)
def delete_service(id):
    if service_dao.soft_delete(id):
        flash("Xóa dịch vụ thành công! (Đã ẩn khỏi danh sách)", "success")
    else:
        flash("Không tìm thấy dịch vụ hoặc đã bị xóa trước đó!", "danger")
    return redirect(url_for("services"))

@app.route("/medicineTypes")
@login_required()
def medicineTypes():
    keyword = request.args.get("keyword", "").strip()
    if keyword:
        types = medicineType_dao.search(keyword)
    else:
        types = medicineType_dao.get_all_medicine_types()
    return render_template("medicineType/medicineTypes.html", types=types)

@app.route("/medicineType/add", methods=["GET","POST"])
@login_required(RoleEnum.ADMIN.value)
def add_medicine_type():
    if request.method == "POST":
        name = request.form["name"]
        medicineType_dao.add_medicine_type(name)
        flash("Thêm loại thuốc thành công!")
        return redirect(url_for("medicineTypes"))
    return render_template("medicineType/medicineType_add.html")

@app.route("/medicine-type/edit/<int:id>", methods=["GET", "POST"])
@login_required(RoleEnum.ADMIN.value)
def edit_medicine_type(id):
    type_to_edit = medicineType_dao.get_by_id(id)  # dùng instance đã init sẵn

    if not type_to_edit:
        flash("Loại thuốc không tồn tại!")
        return redirect(url_for("medicineTypes"))

    if request.method == "POST":
        new_name = request.form.get("name")
        type_to_edit.name = new_name
        medicineType_dao.update(type_to_edit)
        flash("Cập nhật loại thuốc thành công!")
        return redirect(url_for("medicineTypes"))

    return render_template("medicineType/medicineType_edit.html", type_obj=type_to_edit)

@app.route("/medicine-type/delete/<int:id>")
@login_required(RoleEnum.ADMIN.value)
def delete_medicine_type(id):
    medicineType_dao.soft_delete(id)
    return redirect(url_for("medicineTypes"))

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
@login_required(RoleEnum.ADMIN.value)
def add_medicine():
    types = medicineType_dao.get_all_medicine_types()
    if request.method == "POST":
        data = request.form
        medicine_dao.add_medicine(data["name"], int(data["medicine_type_id"]), float(data["price"]))
        flash("Thêm thuốc thành công!")
        return redirect(url_for("medicines"))
    return render_template("medicine/medicine_add.html", types=types)

@app.route("/medicine/edit/<int:id>", methods=["GET","POST"])
@login_required(RoleEnum.ADMIN.value)
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
@login_required(RoleEnum.ADMIN.value)
def delete_medicine(id):
    if medicine_dao.soft_delete(id):
        flash("Xóa thuốc thành công! (Đã ẩn khỏi danh sách)", "success")
    else:
        flash("Không tìm thấy thuốc hoặc đã bị xóa trước đó!", "danger")

    return redirect(url_for("medicines"))

@app.route("/bills")
@login_required(RoleEnum.USER.value, RoleEnum.PATIENT.value, RoleEnum.DOCTOR.value, RoleEnum.ADMIN.value)
def bills():
    user_id = session.get("user_id")
    role = session.get("role")

    if not user_id or role is None:
        flash("Vui lòng đăng nhập lại.", "danger")
        return redirect(url_for("login"))

    role_norm = role.lower() if isinstance(role, str) else role

    all_bills = bill_dao.get_all()
    bills = []

    if role_norm in [RoleEnum.ADMIN.value, "admin"]:
        bills = all_bills

    elif role_norm in [RoleEnum.USER.value, RoleEnum.PATIENT.value, "user", "patient"]:
        patient = patient_dao.get_by_user_id(user_id)
        if patient:
            bills = [b for b in all_bills if b.appointment and b.appointment.patient_id == patient.id]
        if not bills:
            flash("Bạn chưa có hóa đơn nào.", "info")

    elif role_norm in [RoleEnum.DOCTOR.value, "doctor"]:
        doctor = doctor_dao.get_by_user_id(user_id)
        if doctor:
            bills = [
                b for b in all_bills
                if b.appointment and b.appointment.schedule and b.appointment.schedule.doctor_id == doctor.id
            ]
        if not bills:
            flash("Bạn chưa có hóa đơn nào từ bệnh nhân.", "info")

    filter_by = request.args.get("filter_by")
    keyword = request.args.get("keyword", "").strip().lower()

    if filter_by and keyword:
        def matches(bill):
            if filter_by == "patient_name" and bill.appointment and bill.appointment.patient:
                return keyword in bill.appointment.patient.name.lower()
            if filter_by == "doctor_name" and bill.appointment and bill.appointment.schedule and bill.appointment.schedule.doctor:
                return keyword in bill.appointment.schedule.doctor.name.lower()
            if filter_by == "status" and bill.status and bill.status.name:
                return keyword in bill.status.name.lower()
            return False

        bills = [b for b in bills if matches(bill)]

    return render_template("bill/bills.html", bills=bills)
@app.route("/bill/add/<int:appointment_id>", methods=["GET","POST"])
@login_required(RoleEnum.ADMIN.value)
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

@app.route("/thongke/thongke")
@login_required(RoleEnum.ADMIN.value)
def thongke():
    selected_date = request.args.get("date", date.today().isoformat())
    selected_doctor_id = request.args.get("doctor_id", type=int)

    stats = thongke_dao.thong_ke_theo_ngay(
        selected_date,
        selected_doctor_id
    )

    doctors = doctor_dao.get_all()

    return render_template(
        "thongke/thongkes.html",
        stats=stats,
        selected_date=selected_date,
        doctors=doctors,
        selected_doctor_id=selected_doctor_id
    )
@app.route("/bill/pay/<int:id>", methods=["GET", "POST"])
@login_required()
def pay_bill(id):
    bill = bill_dao.get_by_id(id)
    if not bill:
        flash("Hóa đơn không tồn tại!", "danger")
        return redirect(url_for("bills"))

    test_amount = 10000  # Để test MoMo sandbox

    if request.method == "POST":
        payment_method = request.form.get("payment_method")  # Chỉ lấy khi POST

        amount = test_amount  # Chế độ test

        if payment_method == "cash":
            bill_dao.update_status(bill.id, "Đã thanh toán", "cash")
            flash(f"TEST: Thanh toán tiền mặt thành công! ({amount:,}đ)", "success")
            return redirect(url_for("bills"))

        elif payment_method == "momo":
            import uuid
            import hmac
            import hashlib
            import requests

            order_id = str(uuid.uuid4())
            request_id = str(uuid.uuid4())

            # THỨ TỰ ĐÚNG - BẮT ĐẦU BẰNG accessKey
            raw_signature = (
                f"accessKey={MOMO_ACCESS_KEY}"
                f"&amount={amount}"
                f"&extraData="
                f"&ipnUrl={MOMO_NOTIFY_URL}"
                f"&orderId={order_id}"
                f"&orderInfo=TEST - Hóa đơn #{bill.id}"
                f"&partnerCode={MOMO_PARTNER_CODE}"
                f"&redirectUrl={MOMO_RETURN_URL}"
                f"&requestId={request_id}"
                f"&requestType=captureWallet"
            )

            signature = hmac.new(
                MOMO_SECRET_KEY.encode('utf-8'),
                raw_signature.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            payload = {
                "partnerCode": MOMO_PARTNER_CODE,
                "accessKey": MOMO_ACCESS_KEY,
                "requestId": request_id,
                "amount": str(amount),
                "orderId": order_id,
                "orderInfo": f"TEST - Hóa đơn #{bill.id}",
                "redirectUrl": MOMO_RETURN_URL,
                "ipnUrl": MOMO_NOTIFY_URL,
                "extraData": "",
                "requestType": "captureWallet",
                "signature": signature
            }

            try:
                response = requests.post(MOMO_ENDPOINT, json=payload, timeout=15)
                res_json = response.json()
                print("=== MoMo Response ===")
                print(res_json)

                if res_json.get("resultCode") == 0 and res_json.get("payUrl"):
                    bill.order_id = order_id
                    bill.payment_method = "momo"
                    bill.total = amount
                    bill_dao.update(bill)
                    return redirect(res_json["payUrl"])
                else:
                    flash(f"Lỗi MoMo [{res_json.get('resultCode')}]: {res_json.get('message', 'Không rõ')}", "danger")
                    return redirect(url_for("pay_bill", id=id))

            except Exception as e:
                print("Lỗi kết nối MoMo:", e)
                flash(f"Lỗi kết nối MoMo: {str(e)}", "danger")
                return redirect(url_for("pay_bill", id=id))

    # GET request: chỉ hiển thị form, KHÔNG dùng payment_method ở đây
    return render_template(
        "bill/bill_pay.html",
        bill=bill,
        display_amount=test_amount
    )
@app.route("/bill/momo_return")
def momo_return():
    order_id = request.args.get("orderId")
    result_code = request.args.get("resultCode")

    if not order_id or not result_code:
        flash("Không nhận được phản hồi từ MoMo!", "danger")
        return redirect(url_for("bills"))

    bill = bill_dao.get_by_order_id(order_id)
    if not bill:
        flash("Không tìm thấy hóa đơn!", "danger")
        return redirect(url_for("bills"))

    if result_code == "0":
        bill_dao.update_status(bill.id, "Đã thanh toán", "momo")
        flash("TEST MoMo: Thanh toán thành công! 🎉", "success")
    else:
        flash(f"TEST MoMo: Thanh toán thất bại (mã lỗi: {result_code})", "danger")

    return redirect(url_for("bills"))
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

