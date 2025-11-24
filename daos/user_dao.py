from database.db import get_connection
from models.user import User
import bcrypt

class UserDAO:

    def get_by_username(self, username):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        row = cursor.fetchone()
        conn.close()
        return User(*row) if row else None

    def register(self, u: User):
        conn = get_connection()
        cursor = conn.cursor()
        hashed = bcrypt.hashpw(u.password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO users(username, password, role)
            VALUES (%s, %s, %s)
        """, (u.username, hashed, u.role))
        conn.commit()
        conn.close()

    def login(self, username, password):
        user = self.get_by_username(username)
        if not user:
            return None
        if bcrypt.checkpw(password.encode(), user.password.encode()):
            return user
        return None
