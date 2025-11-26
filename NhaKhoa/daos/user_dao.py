import bcrypt
from NhaKhoa.database.db import get_connection
from NhaKhoa.models.user import User
from datetime import datetime

class UserDAO:
    def get_by_username(self, username_or_email: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=%s OR email=%s",
            (username_or_email, username_or_email)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return User(
                id=row["id"],
                username=row["username"],
                password=row["password"],
                role=row["role"],
                email=row.get("email", "")
            )
        return None

    def register(self, user: User):
        conn = get_connection()
        cursor = conn.cursor()
        hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users(username, email, password, role) VALUES (%s, %s, %s, %s)",
            (user.username, user.email, hashed, user.role)
        )
        conn.commit()
        cursor.close()
        conn.close()

    def login(self, username_or_email: str, password: str):
        user = self.get_by_username(username_or_email)
        if user and self.check_password(user, password):
            return user
        return None

    def check_password(self, user: User, password: str):
        return bcrypt.checkpw(password.encode(), user.password.encode())

    def update_password(self, user: User, new_password: str):
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user.id))
        conn.commit()
        cursor.close()
        conn.close()

    # ------------------------
    # Reset Password Tokens
    # ------------------------
    def set_reset_token(self, user: User, token: str, expiry: datetime):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET reset_token=%s, reset_token_expiry=%s WHERE id=%s",
            (token, expiry, user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()

    def get_by_token(self, token: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE reset_token=%s AND reset_token_expiry >= NOW()",
            (token,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return User(
                id=row["id"],
                username=row["username"],
                password=row["password"],
                role=row["role"],
                email=row.get("email", "")
            )
        return None

    def clear_reset_token(self, user: User):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET reset_token=NULL, reset_token_expiry=NULL WHERE id=%s",
            (user.id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
