from flask_login import UserMixin
from db import get_db_connection

class User(UserMixin):
    """Class for handling users."""
    def __init__(self, id, username, password_hash, created_at=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at
    
    @staticmethod
    def get_by_username(username):
        """Get the user information from the database using the user's username."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return User(**user_data) if user_data else None
    
    @staticmethod
    def get_by_id(user_id):
        """Get the user information from the database using the user's ID."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return User(**user_data) if user_data else None
