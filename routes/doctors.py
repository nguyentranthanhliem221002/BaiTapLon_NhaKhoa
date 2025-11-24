from dao.doctor_dao import DoctorDAO
from models.doctor import Doctor

doctor_dao = DoctorDAO()

@app.route("/doctors")
def doctors():
    doctors = doctor_dao.get_all()
    return render_template("doctors/index.html", doctors=doctors)

@app.route("/doctors/add", methods=["GET", "POST"])
def add_doctor():
    if request.method == "POST":
        name = request.form["name"]
        specialty = request.form["specialty"]
        phone = request.form["phone"]
        doctor_dao.add(Doctor(None, name, specialty, phone))
        return redirect("/doctors")
    return render_template("doctors/add.html")

@app.route("/doctors/edit/<int:id>", methods=["GET", "POST"])
def edit_doctor(id):
    doctor = next((d for d in doctor_dao.get_all() if d.id == id), None)
    if request.method == "POST":
        doctor.name = request.form["name"]
        doctor.specialty = request.form["specialty"]
        doctor.phone = request.form["phone"]
        doctor_dao.add(doctor)  # nếu DAO có update thì dùng update, hoặc bạn cần viết thêm update cho doctor
        return redirect("/doctors")
    return render_template("doctors/edit.html", doctor=doctor)

@app.route("/doctors/delete/<int:id>")
def delete_doctor(id):
    # tương tự Patient, nếu có update/delete trong DAO
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctors WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect("/doctors")
