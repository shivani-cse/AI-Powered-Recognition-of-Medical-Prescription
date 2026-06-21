# Prescription Scanner  
## AI-Powered Medical Handwritten Prescription Recognition System

---

## 📌 Overview

Prescription Scanner is an AI-powered web application designed to recognize and digitize handwritten medical prescriptions. The system uses Artificial Intelligence, Optical Character Recognition (OCR), and Natural Language Processing (NLP) techniques to extract important prescription information such as medicine names, dosage details, frequency, and instructions.

The main aim of this project is to reduce errors caused by unclear handwriting, save time in prescription processing, and convert handwritten medical data into a structured digital format.

---

# 🚀 Features

## Image Preprocessing Pipeline

- Adaptive thresholding (OTSU + Gaussian)
- CLAHE contrast enhancement
- Noise reduction
- Deskew and rotation correction
- Morphological character enhancement
- Image sharpening
- Multiple image variants for better OCR accuracy

## OCR Engine

- PaddleOCR with SVTR_LCNet algorithm
- Handwritten text extraction
- Multi-pass OCR processing
- Confidence-based recognition
- Text merging and duplicate removal

## Medical Dictionary

- Supports 200+ medications
- Tablet and capsule recognition
- Injection and syrup recognition
- Indian brand name support
- Fuzzy matching using Levenshtein distance
- Medicine frequency detection (OD, BD, TDS, QID, SOS)
- Route detection (PO, IM, IV, SC, SL)

## NLP Processing

- Medicine name extraction
- Dosage extraction
- Frequency detection
- Duration extraction
- Medical instruction analysis
- Patient information extraction

## Accuracy Metrics

- Character accuracy
- Word accuracy
- Medicine recognition accuracy
- Overall OCR confidence score

## Training System

- Perceptual hash (pHash) image similarity
- Hamming distance comparison
- Progressive learning database
- Verified sample tracking

## Export Options

- PDF prescription report generation
- CSV export
- JSON API support

## Authentication

- User registration and login
- Role-based access
- Secure password hashing
- Password reset functionality
- Session management

---

# 🛠️ Technologies Used

### Backend
- Python
- Flask

### AI / ML
- PaddleOCR
- SVTR_LCNet OCR Algorithm
- SpaCy NLP
- Fuzzy Matching Algorithm

### Image Processing
- OpenCV

### Database
- SQLite

### Frontend
- HTML
- CSS
- JavaScript

---

# ⚙️ Working Process

1. User uploads handwritten prescription image
2. Image preprocessing improves image quality
3. OCR extracts handwritten text
4. NLP processes extracted information
5. Medicine names and dosage are identified
6. Results are displayed in structured format
7. Prescription report can be generated

---

# 📂 Project Modules

## Image Preprocessing

Improves prescription image quality using resizing, noise removal, thresholding, and enhancement techniques.

## OCR Processing

Uses PaddleOCR to convert handwritten prescription images into machine-readable text.

## Text Processing

Uses NLP techniques to identify medicine names, dosage details, and medical instructions.

## Medicine Recognition

Uses fuzzy matching algorithms to correct spelling variations and improve medicine identification accuracy.

## Result Display

Displays extracted prescription information through the Flask web interface.

---

# 📦 Installation

## Clone Repository

```bash
git clone <repository-url>
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Install SpaCy Model

```bash
python -m spacy download en_core_web_sm
```

## Run Application

```bash
python run.py
```

Open browser:

```
http://127.0.0.1:5000
```

---

# 📁 Adding Training Data

Place prescription images inside:

```
training_data/images/
```

The system stores scanned prescriptions as training samples to improve future recognition.

---

# 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| SECRET_KEY | Flask session security key |

Example:

```bash
export SECRET_KEY="your-secret-key"
```

---

# 🗄️ Database

SQLite database is automatically created.

Stored data:

- User information
- Prescription records
- Extracted text
- Training samples

Database files:

```
prescriptions.db
training.db
```

---

# 🖼️ Supported Image Formats

Supported:

- PNG
- JPG
- JPEG
- GIF
- BMP
- TIFF
- WEBP

Best results:

- Clear image
- Good lighting
- High resolution
- Proper contrast

---

# ✅ Advantages

- Reduces errors caused by unclear handwriting
- Saves time in prescription processing
- Improves accuracy using AI and OCR
- Converts handwritten prescriptions into digital format
- Supports easy storage and retrieval
- Helps healthcare professionals access information quickly

---

# 🔮 Future Enhancements

- Mobile application development
- Cloud deployment
- Multi-language support
- Integration with hospital management systems
- Improved deep learning models
- Electronic Health Record integration

---

# ⚠️ Notes

- OCR accuracy depends on image quality.
- Results should be verified by healthcare professionals.
- This system is developed as an assistive healthcare tool.

---

