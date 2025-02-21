# models.py
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

class User:
    def __init__(self, db_path='scheduler.db'):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize users table"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, password, email):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            password_hash = generate_password_hash(password)
            c.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                     (username, password_hash, email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            return user[0]  # Return user_id
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        
        return user if user else None