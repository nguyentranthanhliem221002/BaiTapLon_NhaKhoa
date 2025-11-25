# models/patient.py
from models.user import User

class Patient(User):
    def __init__(self, id=None, username="", email="", role="patient",
                 password="", name="", age=0, phone="", address="", user_id=None):
        super().__init__(id=id, username=username, email=email, role=role, password=password)
        self.name = name
        self.age = age
        self.phone = phone
        self.address = address
        self.user_id = user_id
