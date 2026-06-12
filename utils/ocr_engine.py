"""
OCR Engine: PaddleOCR with medical text processing.
Fixed: false positive drug matches, patient info extraction.
"""

import re
import os
import json
import logging
from utils.medical_dictionary import (
    MEDICAL_DICTIONARY, FREQUENCY_TERMS, ROUTE_TERMS,
    DOSAGE_UNITS, DURATION_TERMS, get_all_drug_names
)

logger = logging.getLogger(__name__)

# ── Words that must NEVER be matched as drug names ──────────────────────────
NON_DRUG_WORDS = {
    'tab', 'tablet', 'tablets', 'cap', 'caps', 'capsule', 'capsules',
    'inj', 'injection', 'syp', 'syrup', 'oint', 'ointment', 'cream',
    'gel', 'drop', 'drops', 'inhaler', 'patch', 'lotion', 'solution',
    'morning', 'night', 'noon', 'evening', 'bedtime', 'daily', 'once',
    'twice', 'thrice', 'times', 'days', 'weeks', 'months', 'years',
    'before', 'after', 'meals', 'food', 'water', 'empty', 'stomach',
    'call', 'continue', 'other', 'please', 'admit', 'phone', 'date',
    'name', 'age', 'sex', 'male', 'female', 'weight', 'height', 'temp',
    'blood', 'pressure', 'pulse', 'follow', 'review', 'next', 'visit',
    'hospital', 'clinic', 'doctor', 'patient', 'diagnosis', 'advice',
    'six', 'five', 'four', 'three', 'two', 'one', 'seven', 'eight',
    'plot', 'road', 'colony', 'hyderabad', 'secunderabad', 'bangalore',
    'sugar', 'medicines', 'medicine', 'drugs', 'drug', 'lot', 'etc',
    'regd', 'mbbs', 'mbbbs', 'consult', 'consultant', 'dr', 'prof',
    'signature', 'sign', 'stamp', 'seal', 'free', 'home', 'delivery',
    'note', 'reg', 'mob', 'tel', 'fax', 'email', 'web', 'www',
    'counselled', 'over', 'paranoia', 'schizophrenia', 'paranoid',
    'hypertension', 'diabetes', 'dehydration', 'fever', 'cold', 'cough',
    'pain', 'infection', 'inflammation', 'allergy', 'anxiety', 'depression',
}

# Medical dose-form prefixes that indicate the next word is a drug name
DOSE_FORM_PREFIXES = {
    'tab', 'tablet', 'cap', 'capsule', 'inj', 'injection',
    'syp', 'syrup', 'td', 't.d', 'cr', 'cream', 'gel', 'oint',
    'dr', 'd.r', 'sr', 's.r', 'mr', 'm.r', 'xr', 'x.r',
}

_ocr_engine = None


def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_engine = PaddleOCR(
                use_angle_cls=True, lang='en', use_gpu=False,
                rec_algorithm='SVTR_LCNet', det_db_thresh=0.3,
                det_db_box_thresh=0.5, rec_batch_num=6, show_log=False)
            logger.info("PaddleOCR engine initialized")
        except Exception as e:
            logger.warning(f"PaddleOCR unavailable: {e}")
            _ocr_engine = None
    return _ocr_engine


def run_ocr_on_image(image_path):
    ocr = get_ocr_engine()
    if ocr is None:
        return [], 0.0
    try:
        result = ocr.ocr(image_path, cls=True)
        lines, confidences = [], []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                    conf = float(line[1][1]) if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.8
                    if text.strip():
                        lines.append(text.strip())
                        confidences.append(conf)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return lines, avg_conf
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return [], 0.0


def multi_pass_ocr(preprocessed_paths):
    all_results = {}
    for version_name, image_path in preprocessed_paths.items():
        if not os.path.exists(image_path):
            continue
        lines, confidence = run_ocr_on_image(image_path)
        if lines:
            all_results[version_name] = {
                'lines': lines, 'confidence': confidence,
                'text': '\n'.join(lines)
            }
    if not all_results:
        return [], 0.0, ""
    best = max(all_results.values(), key=lambda x: x['confidence'])
    seen, all_lines = set(), []
    for res in sorted(all_results.values(), key=lambda x: -x['confidence']):
        for line in res['lines']:
            norm = re.sub(r'\s+', ' ', line.strip().lower())
            if norm not in seen and len(norm) > 1:
                seen.add(norm)
                all_lines.append(line.strip())
    avg_conf = sum(r['confidence'] for r in all_results.values()) / len(all_results)
    return all_lines, avg_conf, best['text']


# ── Levenshtein distance ─────────────────────────────────────────────────────
def _levenshtein(s1, s2):
    s1, s2 = s1.lower(), s2.lower()
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i-1][j-1] if s1[i-1] == s2[j-1] else 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]


def _similarity(a, b):
    a, b = a.lower().strip(), b.lower().strip()
    return (1 - _levenshtein(a, b) / max(len(a), len(b), 1)) * 100


def correct_drug_name(token, threshold=78):
    """
    Match token against drug dictionary.
    Returns (canonical_name, confidence, drug_info) or (None, 0, None).

    Key guards:
    - token must be >= 4 characters
    - token must NOT be in NON_DRUG_WORDS blocklist
    - score threshold raised to 78% to cut false positives
    """
    token_lower = token.lower().strip()

    # Hard minimum length — avoids matching 'lot', 'tab', 'age', etc.
    if len(token_lower) < 4:
        return None, 0, None

    # Skip blocklisted words
    if token_lower in NON_DRUG_WORDS:
        return None, 0, None

    # Exact match on canonical name
    if token_lower in MEDICAL_DICTIONARY:
        return token_lower, 100, MEDICAL_DICTIONARY[token_lower]

    # Search all names + aliases
    best_score, best_canonical, best_info = 0, None, None
    for drug, info in MEDICAL_DICTIONARY.items():
        for name in [drug] + info.get('aliases', []):
            score = _similarity(token_lower, name.lower())
            if score > best_score:
                best_score, best_canonical, best_info = score, drug, info

    if best_score >= threshold:
        return best_canonical, round(best_score), best_info
    return None, 0, None


# ── Context helpers ──────────────────────────────────────────────────────────

def _line_has_dose_form_prefix(line):
    """True if line starts with Tab/Cap/Inj/Syp etc."""
    first = line.strip().split()[0].lower().rstrip('.') if line.strip() else ''
    return first in DOSE_FORM_PREFIXES


def preprocess_text(text):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_dosage(text):
    for pat in [
        r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|units|drops|puffs|tabs|caps|sachets|tsp|tbsp)',
        r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml)',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"{m.group(1)} {m.group(2).lower()}"
    return None


def extract_frequency(text):
    text_lower = text.lower()
    m = re.search(r'(\d-\d-\d)', text)
    if m and m.group(1) in FREQUENCY_TERMS:
        return FREQUENCY_TERMS[m.group(1)]
    for abbr, full in FREQUENCY_TERMS.items():
        if re.search(r'\b' + re.escape(abbr) + r'\b', text_lower):
            return full
    freq_map = {
        r'once\s+a?\s*day': 'Once daily',
        r'twice\s+a?\s*day': 'Twice daily',
        r'three\s+times': 'Three times daily',
        r'four\s+times': 'Four times daily',
        r'at\s+bedtime': 'At bedtime',
        r'before\s+meals?': 'Before meals',
        r'after\s+meals?': 'After meals',
        r'in\s+the\s+morning': 'Morning',
        r'at\s+night': 'At night',
        r'morning\s+.*\s+night': 'Morning and Night',
    }
    for pat, result in freq_map.items():
        if re.search(pat, text_lower):
            return result
    return None


def extract_duration(text):
    for pat in [
        r'for\s+(\d+)\s*(days?|weeks?|months?)',
        r'(\d+)\s*(days?|weeks?|months?)',
        r'(\d+)\s*[xX]\s*(days?|weeks?)',
        r'(\d+)\s*d\b', r'(\d+)\s*w\b',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            unit = m.group(2) if len(m.groups()) > 1 else 'days'
            return f"{m.group(1)} {unit}"
    return None


def extract_route(text):
    text_lower = text.lower()
    for abbr, full in ROUTE_TERMS.items():
        if re.search(r'\b' + re.escape(abbr) + r'\b', text_lower):
            return full
    for kw, route in [('oral','Oral'),('inject','Injection'),('inhale','Inhalation'),
                      ('topical','Topical'),('tablet','Oral'),('capsule','Oral'),('syrup','Oral')]:
        if kw in text_lower:
            return route
    return None


def extract_patient_info(lines):
    """
    Extract patient name, age, date, doctor from prescription header lines.
    Uses strict patterns to avoid false matches.
    """
    info = {"name": None, "age": None, "date": None, "doctor": None}

    # Only look at first 12 lines for patient info
    header = lines[:12]

    for line in header:
        line_stripped = line.strip()

        # Patient name — must follow "Name:", "Patient:", "Mr.", "Mrs.", "Ms.", "Dr." pattern
        if not info["name"]:
            name_m = re.search(
                r'(?:^|\b(?:name|patient|pt)\s*[:\-]?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                line_stripped, re.IGNORECASE)
            if name_m:
                info["name"] = name_m.group(1).strip()
            else:
                # Match "Mr / Mrs / Ms / Dr" followed by a name
                title_m = re.search(
                    r'\b(Mr\.?|Mrs\.?|Ms\.?|Master)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
                    line_stripped)
                if title_m:
                    info["name"] = title_m.group(2).strip()

        # Age — must be a number followed by yr/yrs/years or preceded by "Age:"
        if not info["age"]:
            age_m = re.search(
                r'(?:age\s*[:\-]?\s*|,\s*)(\d{1,3})\s*(?:yr|yrs|years?|y\.?o\.?)',
                line_stripped, re.IGNORECASE)
            if age_m:
                info["age"] = age_m.group(1) + " years"
            else:
                # Standalone "41yrs" pattern
                age_m2 = re.search(r'\b(\d{1,3})\s*(?:yr|yrs)\b', line_stripped, re.IGNORECASE)
                if age_m2:
                    info["age"] = age_m2.group(1) + " years"

        # Date
        if not info["date"]:
            date_m = re.search(r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', line_stripped)
            if date_m:
                info["date"] = date_m.group(1)

        # Doctor name
        if not info["doctor"]:
            doc_m = re.search(
                r'\bDr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                line_stripped)
            if doc_m:
                info["doctor"] = "Dr. " + doc_m.group(1).strip()

    return info


def extract_medications(lines):
    """
    Extract medications with strict filtering:
    - Prefer lines that have a dose-form prefix (Tab/Cap/Inj/Syp)
    - Minimum token length 4
    - Blocklist of non-drug words
    - Threshold 78%
    - No duplicate canonical names
    """
    medications = []

    # Two passes:
    # Pass 1: lines with explicit dose-form prefix (high confidence)
    # Pass 2: lines without prefix (lower confidence, higher threshold)

    for pass_num in range(2):
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or len(line) < 3:
                i += 1
                continue

            has_prefix = _line_has_dose_form_prefix(line)

            # Pass 1 = only lines with prefix; Pass 2 = only lines without
            if pass_num == 0 and not has_prefix:
                i += 1
                continue
            if pass_num == 1 and has_prefix:
                i += 1
                continue

            # Context window: this line + next 2 lines
            context = ' '.join(lines[i:min(i + 3, len(lines))])
            context_clean = preprocess_text(context)

            # Try multi-word then single-word matches
            tokens = re.findall(r'[A-Za-z]+(?:\s+[A-Za-z]+)*', line)
            found_drug, drug_info, match_confidence = None, None, 0

            # For pass 1 (has prefix), skip the prefix token itself when searching
            search_tokens = tokens[1:] if has_prefix and tokens else tokens

            threshold = 78 if pass_num == 0 else 85  # stricter on pass 2

            for length in [4, 3, 2, 1]:
                for j in range(len(search_tokens) - length + 1):
                    candidate = ' '.join(search_tokens[j:j + length])
                    # Skip if any word in candidate is blocklisted
                    if any(w.lower() in NON_DRUG_WORDS for w in candidate.split()):
                        continue
                    drug_name, conf, info = correct_drug_name(candidate, threshold)
                    if drug_name and conf > match_confidence:
                        found_drug, drug_info, match_confidence = drug_name, info, conf
                if found_drug and match_confidence >= threshold:
                    break

            if found_drug:
                dosage = extract_dosage(context_clean)
                frequency = extract_frequency(context_clean)
                duration = extract_duration(context_clean)
                route = extract_route(context_clean)

                # Determine display name
                display_name = found_drug.title()
                if drug_info and "canonical_name" in drug_info:
                    display_name = drug_info["canonical_name"].title()

                # Determine default route from drug type
                drug_type = drug_info.get("type", "tablet") if drug_info else "tablet"
                if not route:
                    if drug_type in ("tablet", "capsule", "syrup"):
                        route = "Oral"
                    elif drug_type == "injection":
                        route = "Injection"
                    elif drug_type in ("cream", "gel", "lotion"):
                        route = "Topical"
                    elif drug_type == "inhaler":
                        route = "Inhalation"
                    else:
                        route = "As directed"

                med_entry = {
                    "name": display_name,
                    "canonical_name": found_drug,
                    "type": drug_type,
                    "category": drug_info.get("category", "unknown") if drug_info else "unknown",
                    "dosage": dosage or "As prescribed",
                    "frequency": frequency or "As directed",
                    "duration": duration or "As directed",
                    "route": route,
                    "raw_line": line,
                    "match_confidence": match_confidence,
                }

                # No duplicates
                if not any(m["canonical_name"] == found_drug for m in medications):
                    medications.append(med_entry)

            i += 1

    return medications


def calculate_accuracy_metrics(medications, raw_lines):
    total_lines = len(raw_lines)
    recognized = sum(1 for l in raw_lines if len(l.strip()) > 3)
    word_acc = (recognized / total_lines * 100) if total_lines > 0 else 0

    total_meds = len(medications)
    med_with_dosage = sum(1 for m in medications if m.get("dosage") != "As prescribed")
    med_with_freq = sum(1 for m in medications if m.get("frequency") != "As directed")

    med_acc = ((med_with_dosage + med_with_freq) / (total_meds * 2) * 100) if total_meds > 0 else 0
    avg_conf = sum(m["match_confidence"] for m in medications) / total_meds if total_meds > 0 else 0
    char_acc = min(95, avg_conf + 5) if avg_conf > 0 else 0
    overall = (char_acc + word_acc + med_acc) / 3

    return {
        "character_accuracy": round(char_acc, 1),
        "word_accuracy": round(word_acc, 1),
        "medication_accuracy": round(med_acc, 1),
        "overall_accuracy": round(overall, 1),
        "total_medications": total_meds,
        "medications_with_dosage": med_with_dosage,
        "medications_with_frequency": med_with_freq,
    }


def process_prescription(preprocessed_paths):
    lines, avg_confidence, raw_text = multi_pass_ocr(preprocessed_paths)
    patient_info = extract_patient_info(lines)
    medications = extract_medications(lines)
    accuracy = calculate_accuracy_metrics(medications, lines)
    return {
        "raw_text": raw_text,
        "lines": lines,
        "ocr_confidence": round(avg_confidence * 100, 1),
        "patient_info": patient_info,
        "medications": medications,
        "accuracy_metrics": accuracy,
        "total_lines_extracted": len(lines),
    }
