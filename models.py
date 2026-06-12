"""
Database models for Prescription Scanner.
Uses SQLite via Flask-SQLAlchemy pattern (direct sqlite3 for simplicity).
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'prescriptions.db')


def get_db():
    """Get database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        reset_token TEXT,
        reset_token_expiry TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        original_filename TEXT,
        stored_filename TEXT,
        scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        patient_name TEXT,
        patient_age TEXT,
        doctor_name TEXT,
        raw_text TEXT,
        ocr_confidence REAL,
        overall_accuracy REAL,
        medications_json TEXT,
        accuracy_metrics_json TEXT,
        pdf_path TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()


# --- User operations ---

def create_user(full_name, email, password_hash, role='user'):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO users (full_name, email, password_hash, role)
                     VALUES (?, ?, ?, ?)''', (full_name, email, password_hash, role))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_last_login(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET last_login = ? WHERE id = ?',
              (datetime.now(), user_id))
    conn.commit()
    conn.close()


def set_reset_token(email, token, expiry):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?',
              (token, expiry, email))
    conn.commit()
    conn.close()


def get_user_by_reset_token(token):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE reset_token = ? AND reset_token_expiry > ?',
              (token, datetime.now()))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_password(user_id, new_hash):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?',
              (new_hash, user_id))
    conn.commit()
    conn.close()


# --- Prescription operations ---

def save_prescription(user_id, data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO prescriptions
                 (user_id, original_filename, stored_filename, patient_name, patient_age,
                  doctor_name, raw_text, ocr_confidence, overall_accuracy,
                  medications_json, accuracy_metrics_json, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id,
               data.get('original_filename'),
               data.get('stored_filename'),
               data.get('patient_name'),
               data.get('patient_age'),
               data.get('doctor_name'),
               data.get('raw_text'),
               data.get('ocr_confidence'),
               data.get('overall_accuracy'),
               json.dumps(data.get('medications', [])),
               json.dumps(data.get('accuracy_metrics', {})),
               data.get('notes', '')))
    conn.commit()
    rx_id = c.lastrowid
    conn.close()
    return rx_id


def update_prescription_pdf(rx_id, pdf_path):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE prescriptions SET pdf_path = ? WHERE id = ?', (pdf_path, rx_id))
    conn.commit()
    conn.close()


def get_user_prescriptions(user_id, limit=50):
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, original_filename, scan_date, patient_name, patient_age,
                        doctor_name, ocr_confidence, overall_accuracy, pdf_path,
                        medications_json
                 FROM prescriptions WHERE user_id = ?
                 ORDER BY scan_date DESC LIMIT ?''', (user_id, limit))
    rows = c.fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        d['medications'] = json.loads(d.get('medications_json') or '[]')
        results.append(d)
    return results


def get_prescription_by_id(rx_id, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM prescriptions WHERE id = ? AND user_id = ?', (rx_id, user_id))
    row = c.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['medications'] = json.loads(d.get('medications_json') or '[]')
        d['accuracy_metrics'] = json.loads(d.get('accuracy_metrics_json') or '{}')
        return d
    return None


def get_all_prescriptions_for_user(user_id):
    """For CSV export."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM prescriptions WHERE user_id = ? ORDER BY scan_date DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        d['medications'] = json.loads(d.get('medications_json') or '[]')
        d['patient_info'] = {
            'name': d.get('patient_name'),
            'age': d.get('patient_age'),
            'doctor': d.get('doctor_name'),
        }
        d['scan_date'] = d.get('scan_date', '')
        results.append(d)
    return results


def get_dashboard_stats(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM prescriptions WHERE user_id = ?', (user_id,))
    total = c.fetchone()[0]
    c.execute('SELECT AVG(overall_accuracy) FROM prescriptions WHERE user_id = ?', (user_id,))
    avg_acc = c.fetchone()[0] or 0
    c.execute('SELECT COUNT(*) FROM prescriptions WHERE user_id = ? AND date(scan_date) = date("now")',
              (user_id,))
    today = c.fetchone()[0]
    conn.close()
    return {
        "total_scans": total,
        "avg_accuracy": round(float(avg_acc), 1),
        "scans_today": today,
    }
