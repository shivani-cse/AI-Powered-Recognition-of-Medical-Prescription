"""
Export utilities: PDF generation, CSV export, JSON export.
"""

import os
import csv
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_pdf_report(ocr_result, output_path):
    """Generate a professional PDF prescription report using FPDF."""
    try:
        from fpdf import FPDF

        class PrescriptionPDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 18)
                self.set_fill_color(30, 80, 140)
                self.set_text_color(255, 255, 255)
                self.cell(0, 14, 'Prescription Scanner', 0, 1, 'C', fill=True)
                self.set_font('Arial', 'I', 10)
                self.set_text_color(100, 100, 100)
                self.cell(0, 6, 'AI-Powered Medical Prescription Analysis Report', 0, 1, 'C')
                self.ln(4)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | Page {self.page_no()}', 0, 0, 'C')

        pdf = PrescriptionPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Patient Information Section
        patient = ocr_result.get('patient_info', {})
        pdf.set_font('Arial', 'B', 13)
        pdf.set_fill_color(240, 245, 255)
        pdf.set_text_color(30, 80, 140)
        pdf.cell(0, 10, 'Patient Information', 0, 1, 'L', fill=True)
        pdf.ln(2)

        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(50, 50, 50)
        fields = [
            ("Patient Name", patient.get("name") or "Not identified"),
            ("Age", patient.get("age") or "Not identified"),
            ("Date", patient.get("date") or datetime.now().strftime("%Y-%m-%d")),
            ("Prescribing Doctor", patient.get("doctor") or "Not identified"),
        ]
        for label, value in fields:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(55, 8, f"{label}:", 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 8, str(value), 0, 1)
        pdf.ln(4)

        # OCR Accuracy Section
        accuracy = ocr_result.get('accuracy_metrics', {})
        pdf.set_font('Arial', 'B', 13)
        pdf.set_fill_color(240, 245, 255)
        pdf.set_text_color(30, 80, 140)
        pdf.cell(0, 10, 'OCR Analysis Summary', 0, 1, 'L', fill=True)
        pdf.ln(2)

        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(50, 50, 50)
        accuracy_fields = [
            ("Overall Accuracy", f"{accuracy.get('overall_accuracy', 0)}%"),
            ("Character Accuracy", f"{accuracy.get('character_accuracy', 0)}%"),
            ("Word Accuracy", f"{accuracy.get('word_accuracy', 0)}%"),
            ("Medication Accuracy", f"{accuracy.get('medication_accuracy', 0)}%"),
            ("OCR Confidence", f"{ocr_result.get('ocr_confidence', 0)}%"),
        ]
        for label, value in accuracy_fields:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(65, 7, f"{label}:", 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 7, str(value), 0, 1)
        pdf.ln(4)

        # Medications Section
        medications = ocr_result.get('medications', [])
        pdf.set_font('Arial', 'B', 13)
        pdf.set_fill_color(240, 245, 255)
        pdf.set_text_color(30, 80, 140)
        pdf.cell(0, 10, f'Prescribed Medications ({len(medications)} found)', 0, 1, 'L', fill=True)
        pdf.ln(2)

        if medications:
            # Table header
            pdf.set_fill_color(30, 80, 140)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 9)
            col_widths = [48, 28, 42, 30, 28]
            headers = ['Medicine Name', 'Dosage', 'Frequency', 'Duration', 'Route']
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 9, header, 1, 0, 'C', fill=True)
            pdf.ln()

            # Table rows
            pdf.set_text_color(50, 50, 50)
            for idx, med in enumerate(medications):
                if idx % 2 == 0:
                    pdf.set_fill_color(248, 250, 255)
                else:
                    pdf.set_fill_color(255, 255, 255)

                pdf.set_font('Arial', 'B', 9)
                pdf.cell(col_widths[0], 8, str(med.get('name', ''))[:22], 1, 0, 'L', fill=True)
                pdf.set_font('Arial', '', 9)
                pdf.cell(col_widths[1], 8, str(med.get('dosage', ''))[:14], 1, 0, 'C', fill=True)
                pdf.cell(col_widths[2], 8, str(med.get('frequency', ''))[:20], 1, 0, 'C', fill=True)
                pdf.cell(col_widths[3], 8, str(med.get('duration', ''))[:14], 1, 0, 'C', fill=True)
                pdf.cell(col_widths[4], 8, str(med.get('route', ''))[:14], 1, 0, 'C', fill=True)
                pdf.ln()

            pdf.ln(4)

            # Detailed medication breakdown
            pdf.set_font('Arial', 'B', 13)
            pdf.set_fill_color(240, 245, 255)
            pdf.set_text_color(30, 80, 140)
            pdf.cell(0, 10, 'Detailed Medication Information', 0, 1, 'L', fill=True)
            pdf.ln(2)

            for idx, med in enumerate(medications, 1):
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(30, 80, 140)
                pdf.cell(0, 8, f"{idx}. {med.get('name', 'Unknown')}", 0, 1)
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(70, 70, 70)
                details = [
                    ("Dosage", med.get('dosage', 'As prescribed')),
                    ("Frequency", med.get('frequency', 'As directed')),
                    ("Duration", med.get('duration', 'As directed')),
                    ("Route", med.get('route', 'As directed')),
                    ("Category", med.get('category', 'Unknown').replace('_', ' ').title()),
                    ("Form", med.get('type', 'Unknown').title()),
                ]
                for label, value in details:
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(5, 6, '', 0, 0)
                    pdf.cell(50, 6, f"   {label}:", 0, 0)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(0, 6, str(value), 0, 1)
                pdf.ln(2)
        else:
            pdf.set_font('Arial', 'I', 11)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 10, 'No medications could be identified. Please review the raw text.', 0, 1, 'C')

        # Disclaimer
        pdf.ln(4)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(150, 150, 150)
        pdf.multi_cell(0, 5, 'DISCLAIMER: This report is generated by an AI system for reference purposes only. '
                             'Always consult a licensed pharmacist or physician before taking any medication. '
                             'The accuracy of OCR results may vary based on prescription image quality.')

        pdf.output(output_path)
        return True

    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return False


def export_to_csv(prescriptions, output_path):
    """Export prescription history to CSV."""
    try:
        fieldnames = ['scan_date', 'patient_name', 'patient_age', 'doctor',
                      'medicine_name', 'dosage', 'frequency', 'duration', 'route', 'category']

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for prescription in prescriptions:
                patient = prescription.get('patient_info', {})
                for med in prescription.get('medications', []):
                    writer.writerow({
                        'scan_date': prescription.get('scan_date', ''),
                        'patient_name': patient.get('name', ''),
                        'patient_age': patient.get('age', ''),
                        'doctor': patient.get('doctor', ''),
                        'medicine_name': med.get('name', ''),
                        'dosage': med.get('dosage', ''),
                        'frequency': med.get('frequency', ''),
                        'duration': med.get('duration', ''),
                        'route': med.get('route', ''),
                        'category': med.get('category', ''),
                    })
        return True
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return False
