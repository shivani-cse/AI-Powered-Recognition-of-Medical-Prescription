"""
Training Module: Perceptual hash-based similarity detection.
pHash is stored as TEXT in SQLite to avoid integer overflow.
"""

import os
import json
import hashlib
import logging
import sqlite3
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_DB = os.path.join(BASE_DIR, 'instance', 'training.db')


def phash(image_path, hash_size=8):
    """Compute perceptual hash — returned as a plain Python int."""
    try:
        img = Image.open(image_path).convert('L').resize(
            (hash_size, hash_size), Image.LANCZOS)
        pixels = np.array(img).flatten()
        avg = float(pixels.mean())
        bits = ''.join('1' if float(p) > avg else '0' for p in pixels)
        return int(bits, 2)          # plain Python int, not numpy
    except Exception as e:
        logger.error(f"Phash error: {e}")
        return None


def hamming_distance(hash1, hash2):
    if hash1 is None or hash2 is None:
        return 64
    return bin(int(hash1) ^ int(hash2)).count('1')


def init_training_db():
    os.makedirs(os.path.dirname(TRAINING_DB), exist_ok=True)
    conn = sqlite3.connect(TRAINING_DB)
    c = conn.cursor()
    # Store phash as TEXT to avoid SQLite INTEGER overflow for large hashes
    c.execute('''CREATE TABLE IF NOT EXISTS training_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_hash TEXT UNIQUE,
        phash TEXT,
        medications TEXT,
        raw_text TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()


def find_similar_training_sample(image_path, threshold=10):
    """Find similar training samples using perceptual hash (Hamming distance)."""
    init_training_db()
    new_hash = phash(image_path)
    if new_hash is None:
        return None

    conn = sqlite3.connect(TRAINING_DB)
    c = conn.cursor()
    c.execute('SELECT id, phash, medications, raw_text FROM training_samples WHERE verified=1')
    rows = c.fetchall()
    conn.close()

    best_match = None
    min_distance = threshold + 1

    for row in rows:
        try:
            stored_hash = int(row[1]) if row[1] else None
            dist = hamming_distance(new_hash, stored_hash)
            if dist < min_distance:
                min_distance = dist
                best_match = {
                    'id': int(row[0]),
                    'medications': json.loads(row[2]) if row[2] else [],
                    'raw_text': row[3] or '',
                    'similarity': round((1 - dist / 64) * 100, 1)
                }
        except Exception:
            continue

    return best_match


def save_training_sample(image_path, ocr_result, verified=False):
    """Save OCR result as a training sample. phash stored as TEXT string."""
    init_training_db()
    try:
        with open(image_path, 'rb') as f:
            image_hash = hashlib.md5(f.read()).hexdigest()

        phash_val = phash(image_path)
        # Store as string to avoid any integer size issues in SQLite
        phash_str = str(phash_val) if phash_val is not None else None

        medications_json = json.dumps(ocr_result.get('medications', []))
        raw_text = ocr_result.get('raw_text', '')

        conn = sqlite3.connect(TRAINING_DB)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO training_samples
                     (image_hash, phash, medications, raw_text, verified)
                     VALUES (?, ?, ?, ?, ?)''',
                  (image_hash, phash_str, medications_json, raw_text, int(verified)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Training save error: {e}")
        return False


def get_training_stats():
    init_training_db()
    conn = sqlite3.connect(TRAINING_DB)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM training_samples')
    total = int(c.fetchone()[0])
    c.execute('SELECT COUNT(*) FROM training_samples WHERE verified=1')
    verified = int(c.fetchone()[0])
    conn.close()
    return {"total_samples": total, "verified_samples": verified}
