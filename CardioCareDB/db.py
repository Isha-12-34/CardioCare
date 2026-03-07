import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "CardioCareDB", "cardiocare.db")


DB_PATH = "CardioCareDB/cardiocare.db"


def get_db_connection():
    """
    Creates and returns a database connection.
    Uses a higher timeout and allows cross-thread access to
    reduce 'database is locked' errors with SQLite.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """
    Creates users and predictions tables if they do not exist
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        reset_token TEXT,
        reset_token_expiry TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Add reset_token columns if they don't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expiry TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # PREDICTIONS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    age INTEGER,
    sex TEXT,
    chest_pain TEXT,
    heart_rate INTEGER,
    bp TEXT,
    smoking TEXT,
    diet TEXT,
    exercise TEXT,
    stress TEXT,
    genetics TEXT,
    risk_level TEXT,
    risk_score REAL,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def insert_user(name, email, password, age, gender):
    """
    Inserts a new user into users table
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, email, password, age, gender)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, password, age, gender))

    conn.commit()
    conn.close()


def get_user_by_email(email):
    """
    Fetch user details by email
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def insert_prediction(user_id, age, sex, chest_pain, heart_rate, bp,
                      smoking, diet, exercise, stress, genetics,
                      risk_level, risk_score):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions (
            user_id, age, sex, chest_pain, heart_rate, bp,
            smoking, diet, exercise, stress, genetics,
            risk_level, risk_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, age, sex, chest_pain, heart_rate, bp,
        smoking, diet, exercise, stress, genetics,
        risk_level, risk_score
    ))

    conn.commit()
    conn.close()


def get_user_predictions(user_id):
    """
    Fetch all predictions of a user (history)
    """
    conn = get_db_connection()
    predictions = conn.execute("""
        SELECT * FROM predictions
        WHERE user_id = ?
        ORDER BY prediction_date DESC
    """, (user_id,)).fetchall()
    conn.close()
    return predictions


def get_user_by_id(user_id):
    """
    Fetch a single user by id
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return user


def update_user_profile(user_id, name, age, gender):
    """
    Update basic profile fields for a user
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET name = ?, age = ?, gender = ?
        WHERE id = ?
    """, (name, age, gender, user_id))
    conn.commit()
    conn.close()


def update_reset_token(email, token, expiry):
    """
    Update reset token for password reset
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET reset_token = ?, reset_token_expiry = ?
        WHERE email = ?
    """, (token, expiry, email))
    conn.commit()
    conn.close()


def get_user_by_reset_token(token):
    """
    Get user by reset token
    """
    conn = get_db_connection()
    user = conn.execute("""
        SELECT * FROM users 
        WHERE reset_token = ? AND reset_token_expiry > datetime('now')
    """, (token,)).fetchone()
    conn.close()
    return user


def update_password(user_id, new_password):
    """
    Update user password and clear reset token
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET password = ?, reset_token = NULL, reset_token_expiry = NULL
        WHERE id = ?
    """, (new_password, user_id))
    conn.commit()
    conn.close()
