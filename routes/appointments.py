from dao.appointment_dao import AppointmentDAO
from models.appointment import Appointment

appointment_dao = AppointmentDAO()

@app.route("/appointments")
def appointments():
    appointments = appointment_dao.get_all()
    return render_template("appointments/index.html", appointments=appointments)

@app.route("/appointments/add", methods=["GET", "POST"])
def add_appointment():
    from dao.patient_dao import PatientDAO
    from dao.doctor_dao import DoctorDAO
    patient_dao = PatientDAO()
    doctor_dao = DoctorDAO()

    if request.method == "POST":
        patient_id = int(request.form["patient_id"])
        doctor_id = int(request.form["doctor_id"])
        appointment_date = request.form["appointment_date"]
        description = request.form["description"]
        appointment_dao.add(Appointment(None, patient_id, doctor_id, appointment_date, description))
        return redirect("/appointments")

    patients = patient_dao.get_all()
    doctors = doctor_dao.get_all()
    return render_template("appointments/add.html", patients=patients, doctors=doctors)

@app.route("/appointments/edit/<int:id>", methods=["GET", "POST"])
def edit_appointment(id):
    appointment = next((a for a in appointment_dao.get_all() if a.id == id), None)
    from dao.patient_dao import PatientDAO
    from dao.doctor_dao import DoctorDAO
    patient_dao = PatientDAO()
    doctor_dao = DoctorDAO()

    if request.method == "POST":
        appointment.patient_id = int(request.form["patient_id"])
        appointment.doctor_id = int(request.form["doctor_id"])
        appointment.appointment_date = request.form["appointment_date"]
        appointment.description = request.form["description"]
        # bạn cần viết hàm update trong AppointmentDAO
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments
            SET patient_id=%s, doctor_id=%s, appointment_date=%s, description=%s
            WHERE id=%s
        """, (appointment.patient_id, appointment.doctor_id, appointment.appointment_date, appointment.description, appointment.id))
        conn.commit()
        conn.close()
        return redirect("/appointments")

    patients = patient_dao.get_all()
    doctors = doctor_dao.get_all()
    return render_template("appointments/edit.html", appointment=appointment, patients=patients, doctors=doctors)

@app.route("/appointments/delete/<int:id>")
def delete_appointment(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect("/appointments")
