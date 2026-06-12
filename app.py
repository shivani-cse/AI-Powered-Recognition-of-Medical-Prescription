"""
Prescription Scanner - Main Flask Application
AI-powered medical prescription recognition system.
"""

import os
import json
import uuid
import secrets
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_file, abort)

from models import (init_db, create_user, get_user_by_email, get_user_by_id,
                    update_last_login, set_reset_token, get_user_by_reset_token,
                    update_password, save_prescription, update_prescription_pdf,
                    get_user_prescriptions, get_prescription_by_id,
                    get_all_prescriptions_for_user, get_dashboard_stats)

from utils.image_preprocessor import preprocess_for_ocr, get_image_quality_score
from utils.ocr_engine import process_prescription
from utils.training_module import (find_similar_training_sample,
                                    save_training_sample, get_training_stats)
from utils.export_utils import generate_pdf_report, export_to_csv



def sanitize_for_json(obj):
    """Recursively convert NumPy types to native Python types for JSON serialization."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
PREPROCESSED_FOLDER = os.path.join(BASE_DIR, 'static', 'preprocessed')
EXPORTS_FOLDER = os.path.join(BASE_DIR, 'static', 'exports')

for folder in [UPLOAD_FOLDER, PREPROCESSED_FOLDER, EXPORTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None


# ==================== AUTH ROUTES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')

        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            update_last_login(user['id'])
            flash(f'Welcome back, {user["full_name"]}.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'user')

        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if role not in ['user', 'pharmacist', 'doctor']:
            role = 'user'

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        user_id = create_user(full_name, email, password_hash, role)

        if user_id:
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('An account with this email already exists.', 'danger')

    return render_template('register.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = get_user_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)
            set_reset_token(email, token, expiry)
            reset_url = url_for('reset_password', token=token, _external=True)
            # In production, send email. For demo, show the link.
            flash(f'Password reset link (demo): {reset_url}', 'info')
        else:
            flash('If this email exists, a reset link has been sent.', 'info')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = get_user_by_reset_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            update_password(user['id'], generate_password_hash(password))
            flash('Password updated successfully. Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ==================== MAIN APP ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    stats = get_dashboard_stats(session['user_id'])
    prescriptions = get_user_prescriptions(session['user_id'], limit=5)
    training_stats = get_training_stats()
    return render_template('dashboard.html', user=user, stats=stats,
                           prescriptions=prescriptions,
                           training_stats=training_stats)


@app.route('/scan', methods=['GET'])
@login_required
def scan():
    return render_template('scan.html')


@app.route('/api/upload', methods=['POST'])
@login_required
def upload_prescription():
    """Upload and process prescription image."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not supported. Use PNG, JPG, JPEG, TIFF, or BMP.'}), 400

    try:
        # Save original file
        unique_id = str(uuid.uuid4())[:8]
        original_filename = secure_filename(file.filename)
        stored_filename = f"{unique_id}_{original_filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, stored_filename)
        file.save(upload_path)

        # Image quality check
        quality = get_image_quality_score(upload_path)

        # Preprocess image
        preprocess_dir = os.path.join(PREPROCESSED_FOLDER, unique_id)
        preprocessed_paths = preprocess_for_ocr(upload_path, output_dir=preprocess_dir)

        # Check training data for similar images
        similar = find_similar_training_sample(upload_path)

        # Run OCR
        ocr_result = process_prescription(preprocessed_paths)
        ocr_result['scan_date'] = datetime.now().isoformat()

        # Merge manual patient inputs (form fields override OCR if provided)
        patient_info = ocr_result.get('patient_info', {})
        manual_name   = request.form.get('manual_name', '').strip()
        manual_age    = request.form.get('manual_age', '').strip()
        manual_date   = request.form.get('manual_date', '').strip()
        manual_doctor = request.form.get('manual_doctor', '').strip()
        manual_notes  = request.form.get('manual_notes', '').strip()
        if manual_name:   patient_info['name']   = manual_name
        if manual_age:    patient_info['age']    = manual_age
        if manual_date:   patient_info['date']   = manual_date
        if manual_doctor: patient_info['doctor'] = manual_doctor
        ocr_result['patient_info'] = patient_info
        accuracy = ocr_result.get('accuracy_metrics', {})

        rx_data = {
            'original_filename': original_filename,
            'stored_filename': stored_filename,
            'patient_name': patient_info.get('name'),
            'patient_age': patient_info.get('age'),
            'doctor_name': patient_info.get('doctor'),
            'raw_text': ocr_result.get('raw_text', ''),
            'ocr_confidence': ocr_result.get('ocr_confidence', 0),
            'overall_accuracy': accuracy.get('overall_accuracy', 0),
            'medications': ocr_result.get('medications', []),
            'accuracy_metrics': accuracy,
        }
        rx_id = save_prescription(session['user_id'], rx_data)

        # Generate PDF
        pdf_filename = f"prescription_{rx_id}_{unique_id}.pdf"
        pdf_path = os.path.join(EXPORTS_FOLDER, pdf_filename)
        ocr_result['patient_info'] = patient_info
        pdf_generated = generate_pdf_report(ocr_result, pdf_path)
        if pdf_generated:
            update_prescription_pdf(rx_id, pdf_filename)

        # Save as training sample
        save_training_sample(upload_path, ocr_result, verified=False)

        response_data = {
            'success': True,
            'prescription_id': rx_id,
            'image_quality': quality,
            'similar_found': similar is not None,
            'ocr_confidence': ocr_result.get('ocr_confidence', 0),
            'patient_info': patient_info,
            'medications': ocr_result.get('medications', []),
            'accuracy_metrics': accuracy,
            'raw_text': ocr_result.get('raw_text', ''),
            'total_lines': ocr_result.get('total_lines_extracted', 0),
            'pdf_available': pdf_generated,
            'pdf_filename': pdf_filename if pdf_generated else None,
            'uploaded_image': f'/static/uploads/{stored_filename}',
        }

        return jsonify(sanitize_for_json(response_data))

    except Exception as e:
        logger.error(f"Upload processing error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Processing error: {str(e)}'}), 500


@app.route('/history')
@login_required
def history():
    prescriptions = get_user_prescriptions(session['user_id'], limit=100)
    return render_template('history.html', prescriptions=prescriptions)


@app.route('/prescription/<int:rx_id>')
@login_required
def view_prescription(rx_id):
    prescription = get_prescription_by_id(rx_id, session['user_id'])
    if not prescription:
        flash('Prescription not found.', 'danger')
        return redirect(url_for('history'))
    return render_template('view_prescription.html', prescription=prescription)


@app.route('/download/pdf/<int:rx_id>')
@login_required
def download_pdf(rx_id):
    prescription = get_prescription_by_id(rx_id, session['user_id'])
    if not prescription or not prescription.get('pdf_path'):
        flash('PDF not available for this prescription.', 'warning')
        return redirect(url_for('history'))
    pdf_path = os.path.join(EXPORTS_FOLDER, prescription['pdf_path'])
    if not os.path.exists(pdf_path):
        flash('PDF file not found.', 'danger')
        return redirect(url_for('history'))
    return send_file(pdf_path, as_attachment=True,
                     download_name=f"prescription_{rx_id}.pdf")


@app.route('/export/csv')
@login_required
def export_csv():
    prescriptions = get_all_prescriptions_for_user(session['user_id'])
    csv_filename = f"prescriptions_{session['user_id']}_{datetime.now().strftime('%Y%m%d')}.csv"
    csv_path = os.path.join(EXPORTS_FOLDER, csv_filename)
    if export_to_csv(prescriptions, csv_path):
        return send_file(csv_path, as_attachment=True, download_name=csv_filename)
    flash('Error generating CSV export.', 'danger')
    return redirect(url_for('history'))


@app.route('/api/prescription/<int:rx_id>/json')
@login_required
def get_prescription_json(rx_id):
    prescription = get_prescription_by_id(rx_id, session['user_id'])
    if not prescription:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(prescription)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
