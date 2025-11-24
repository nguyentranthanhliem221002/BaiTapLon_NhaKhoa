from flask import Flask, render_template, request, redirect
from dao.patient_dao import PatientDAO
from models.patient import Patient

patient_dao = PatientDAO()

@app.route("/patients")
def patients():
    patients = patient_dao.get_all()
    return render_template("patients/index.html", patients=patients)

@app.route("/patients/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        name = request.form["name"]
        age = int(request.form["age"])
        phone = request.form["phone"]
        address = request.form["address"]
        patient_dao.add(Patient(None, name, age, phone, address))
        return redirect("/patients")
    return render_template("patients/add.html")

@app.route("/patients/edit/<int:id>", methods=["GET", "POST"])
def edit_patient(id):
    patient = patient_dao.get_by_id(id)
    if request.method == "POST":
        patient.name = request.form["name"]
        patient.age = int(request.form["age"])
        patient.phone = request.form["phone"]
        patient.address = request.form["address"]
        patient_dao.update(patient)
        return redirect("/patients")
    return render_template("patients/edit.html", patient=patient)

@app.route("/patients/delete/<int:id>")
def delete_patient(id):
    patient_dao.delete(id)
    return redirect("/patients")
