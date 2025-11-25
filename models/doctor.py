# models/doctor.py
from models.user import User

class Doctor(User):
    def __init__(self, id=None, username="", email="", role="doctor",
                 password="", name="", specialty="", phone="", user_id=None):
        super().__init__(id=id, username=username, email=email, role=role, password=password)
        self.name = name
        self.specialty = specialty
        self.phone = phone
        self.user_id = user_id
