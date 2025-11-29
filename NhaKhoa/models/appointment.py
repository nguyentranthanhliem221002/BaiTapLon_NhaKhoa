class Appointment:
    def __init__(self, id=None, patient_id=None, doctor_id=None, appointment_date=None, description=""):
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.description = description