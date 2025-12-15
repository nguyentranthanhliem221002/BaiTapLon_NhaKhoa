from sqlalchemy.orm import Session

from NhaKhoa.models.patient import Patient
from NhaKhoa.models.user import User
from NhaKhoa.database.db import get_session
import bcrypt
from datetime import datetime

class UserDAO:
    def get_by_id(self, id: int):
        with get_session() as session:
            return session.query(User).get(id)

    def get_by_username(self, username_or_email: str):
        with get_session() as session:
            return session.query(User).filter(
                (User.name == username_or_email) | (User.email == username_or_email)
            ).first()

    def register(self, user: User, date_of_birth: datetime):
        user.password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
        age = datetime.now().year - date_of_birth.year
        patient = Patient(name=user.name, age=age)
        with get_session() as session:
            session.add(user)
            session.add(patient)
            session.commit()

            patient.user_id = user.id
            session.commit()

    def login(self, username_or_email: str, password: str):
        user = self.get_by_username(username_or_email)
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return user
        return None

    def update_password(self, user: User, new_password: str):
        with get_session() as session:
            user.password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            session.add(user)
            session.commit()

    def set_reset_token(self, user: User, token: str, expiry: datetime):
        with get_session() as session:
            user.reset_token = token
            user.reset_token_expiry = expiry
            session.add(user)
            session.commit()

    def get_by_token(self, token: str):
        with get_session() as session:
            return session.query(User).filter(
                User.reset_token == token,
                User.reset_token_expiry >= datetime.now()
            ).first()

    def clear_reset_token(self, user: User):
        with get_session() as session:
            user.reset_token = None
            user.reset_token_expiry = None
            session.add(user)
            session.commit()
