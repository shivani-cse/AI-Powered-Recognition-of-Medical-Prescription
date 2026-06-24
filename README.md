# 🩺 AI-Powered Medical Prescription OCR System

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![PaddleOCR](https://img.shields.io/badge/OCR-PaddleOCR-green)
![OpenCV](https://img.shields.io/badge/Image%20Processing-OpenCV-red)
![License](https://img.shields.io/badge/License-MIT-yellow)


# Prescription Scanner

AI-powered system that recognizes and digitizes handwritten medical prescriptions using **OCR, Computer Vision, Machine Learning, and Natural Language Processing (NLP)**.

This project helps convert unclear handwritten prescriptions into structured digital information such as medicine names, dosage, frequency, duration, and medical instructions.

The main goal is to reduce prescription reading errors, improve processing speed, and support healthcare professionals with AI-assisted prescription analysis.

---

# 📋 Project Overview

The system combines:

- Advanced image preprocessing
- Handwriting optimized OCR recognition
- Medical dictionary matching
- NLP-based medical information extraction
- Prescription report generation
- Data export functionality

---




## Upload Prescription

![Upload](screenshots/upload.png)


## Extracted Prescription Result

![Result](screenshots/result.png)


## Generated Report

![Report](screenshots/report.png)


---

# 🔍 Core Features


## 🖼️ Advanced Image Preprocessing

- Adaptive thresholding
- OTSU + Gaussian thresholding
- CLAHE contrast enhancement
- Noise reduction
- Image sharpening
- Deskew and rotation correction
- Morphological character enhancement
- Multiple image preprocessing techniques for OCR improvement


---

## 🔎 OCR Recognition System

- PaddleOCR integration
- SVTR_LCNet OCR algorithm
- Handwritten text extraction
- Multiple OCR processing passes
- Confidence score evaluation
- Text cleaning and duplicate removal


---

## 💊 Medical Dictionary Integration

- Supports 200+ medicines
- Tablet and capsule recognition
- Injection and syrup recognition
- Indian brand name support
- Fuzzy matching using Levenshtein distance
- Medicine frequency detection

Supported frequency:

```
OD
BD
TDS
QID
SOS
```

Route detection:

```
PO
IM
IV
SC
SL
```


---

## 🧠 NLP Processing

- Medicine name extraction
- Dosage extraction
- Frequency detection
- Duration extraction
- Medical instruction analysis
- Patient information extraction


---

## 🤖 Training System

- Perceptual hash (pHash) similarity
- Hamming distance comparison
- Prescription sample tracking
- Continuous improvement support


---

## 📤 Export Features

- PDF prescription report generation
- CSV export
- JSON structured data


---

# 🛠️ Technologies Used


## AI / Machine Learning

- PaddleOCR
- SVTR_LCNet
- PyTorch
- SpaCy NLP
- Fuzzy Matching Algorithm


## Computer Vision

- OpenCV


## Backend

- Python
- Flask


## Database

- SQLite


## Frontend

- HTML
- CSS
- JavaScript
- Bootstrap


---

# 🚀 Getting Started


## Prerequisites

- Python 3.8+
- pip package manager


---

# Installation


Clone repository:

```bash
git clone https://github.com/shivani-cse/AI-Powered-Recognition-of-Medical-Prescription.git
```

Go inside project:

```bash
cd AI-Powered-Recognition-of-Medical-Prescription
```


Create virtual environment:

```bash
python -m venv venv
```


Activate environment:

### Windows

```bash
venv\Scripts\activate
```


### Linux / Mac

```bash
source venv/bin/activate
```


Install dependencies:

```bash
pip install -r requirements.txt
```


Install SpaCy model:

```bash
python -m spacy download en_core_web_sm
```


Run application:

```bash
python run.py
```


Open browser:

```
http://127.0.0.1:5000
```


---

# 💻 Usage


1. Upload handwritten prescription image
2. Image preprocessing improves image quality
3. OCR extracts handwritten text
4. NLP processes medical information
5. Medicine details are identified
6. Digital prescription report is generated


---




---

# 📊 Performance Metrics


The system evaluates:

- Character accuracy
- Word accuracy
- Medicine recognition accuracy
- OCR confidence score


---

# 🔮 Future Enhancements

- Mobile application
- Cloud deployment
- Multi-language support
- Hospital management integration
- Improved deep learning models
- Electronic Health Record integration


---

# ⚠️ Disclaimer

This project is developed as an assistive healthcare tool.

OCR accuracy depends on handwriting quality and image conditions. Medical information should always be verified by healthcare professionals.


---

# 🤝 Contributing

Contributions are welcome.

Feel free to submit issues or pull requests.


---

# 🙏 Acknowledgements

- PaddleOCR for OCR technology
- OpenCV for image processing
- Flask for backend framework
- SpaCy for NLP processing


---

# 📄 License

This project is licensed under the MIT License.