
# Prescription Scanner
## AI-Powered Medical Handwritten Prescription Recognition System

---

## Project Structure

```
prescription_scanner/
├── app.py                          # Main Flask application
├── models.py                       # SQLite database models
├── run.py                          # Startup script
├── requirements.txt                # Python dependencies
├── instance/
│   ├── prescriptions.db            # Main database (auto-created)
│   └── training.db                 # Training data database (auto-created)
├── static/
│   ├── css/style.css               # Main stylesheet
│   ├── js/main.js                  # Frontend JavaScript
│   ├── uploads/                    # Uploaded prescription images
│   ├── preprocessed/               # Preprocessed image variants
│   └── exports/                    # PDF and CSV exports
├── templates/
│   ├── base.html                   # Base layout with navbar
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── forgot_password.html        # Forgot password
│   ├── reset_password.html         # Password reset
│   ├── dashboard.html              # User dashboard
│   ├── scan.html                   # Prescription scanner
│   ├── history.html                # Scan history
│   └── view_prescription.html     # Prescription detail view
├── utils/
│   ├── __init__.py
│   ├── image_preprocessor.py       # OpenCV image enhancement pipeline
│   ├── ocr_engine.py               # PaddleOCR + NLP processing
│   ├── medical_dictionary.py       # 200+ medication database
│   ├── training_module.py          # Perceptual hash training system
│   └── export_utils.py             # PDF and CSV export
└── training_data/
    └── images/                     # Place training images here
```

---

## Setup Instructions

### Step 1 — Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** PaddleOCR and PaddlePaddle may take several minutes to install.
> GPU acceleration requires the appropriate CUDA-enabled paddlepaddle build.

### Step 3 — Install SpaCy English Model

```bash
python -m spacy download en_core_web_sm
```

### Step 4 — Run the Application

```bash
python run.py
```

Open your browser and navigate to: **http://127.0.0.1:5000**

---

## Features

### Image Preprocessing Pipeline
- Adaptive thresholding (OTSU + Gaussian)
- CLAHE contrast enhancement
- Fast non-local means denoising
- Deskew / rotation correction
- Morphological character enhancement
- Sharpening for fine text
- 5 preprocessed variants per image

### OCR Engine
- PaddleOCR with SVTR_LCNet algorithm
- Multi-pass OCR across all preprocessed variants
- Confidence scoring per recognition
- Merged and deduplicated text output

### Medical Dictionary
- 200+ medications including:
  - Tablets and capsules
  - Injections (antibiotics, corticosteroids, vitamins, etc.)
  - Syrups (paediatric and adult)
  - Inhalers and topicals
- Indian brand name aliases included
- Fuzzy matching via FuzzyWuzzy (Levenshtein distance)
- Frequency terms: OD, BD, TDS, QID, SOS, etc.
- Route of administration: PO, IM, IV, SC, SL, etc.

### NLP Processing
- Drug name extraction with multi-word matching
- Dosage extraction (mg, mcg, ml, etc.)
- Frequency detection (abbreviations + natural language)
- Duration extraction
- Route of administration identification
- Patient info extraction (name, age, date, doctor)

### Accuracy Metrics
- Character accuracy
- Word accuracy
- Medication accuracy
- Overall accuracy
- Per-prescription OCR confidence

### Training System
- Perceptual hash (pHash) for image similarity
- Hamming distance similarity scoring
- Progressive learning database
- Verified sample tracking

### Export Options
- PDF report (FPDF): patient info, medications table, detailed breakdown
- CSV export of full scan history
- JSON API endpoint per prescription

### Authentication
- User registration with role selection (Patient / Pharmacist / Doctor)
- Secure password hashing (Werkzeug)
- Password strength indicator
- Forgot password with token-based reset
- Session management

---

## Adding Training Data

Place prescription images in: `training_data/images/`

The system automatically saves each scanned prescription as a training sample. Verified samples improve future recognition through perceptual hash matching.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | auto-generated | Flask session secret key |

For production, set:
```bash
export SECRET_KEY="your-strong-secret-key-here"
```

---

## Supported Image Formats

PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

**Best results with:**
- Clear, well-lit images
- Minimum 300 DPI scans
- Non-blurry captures
- Good contrast between ink and paper

---

## Database

SQLite databases are auto-created in the `instance/` directory on first run.
- `prescriptions.db` — users and prescription data
- `training.db` — training samples

---

## Notes

- This system is for reference purposes only.
- Always consult a licensed pharmacist or physician before acting on OCR results.
- OCR accuracy depends heavily on prescription image quality.
- The system is optimized for Indian market medications and brand names.
