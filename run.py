#!/usr/bin/env python3
"""
Prescription Scanner - Startup Script
Run this file to start the application.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import init_db
from app import app

if __name__ == '__main__':
    print("=" * 55)
    print("  Prescription Scanner - AI Medical OCR System")
    print("=" * 55)
    print("  Initializing database...")
    init_db()
    print("  Database ready.")
    print("  Starting server at http://127.0.0.1:5000")
    print("  Press CTRL+C to stop.")
    print("=" * 55)
    app.run(debug=False, host='0.0.0.0', port=5000)
