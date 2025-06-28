# exporter.py
from fpdf import FPDF
import os
from PIL import Image
import json
import zipfile

# Export functionality
# Alert colors for PDF export
ALERT_PDF_COLORS = {
    "Alert": (244, 67, 54),      # Red
    "Warning": (255, 235, 59),   # Yellow
    "Note": (33, 150, 243),      # Blue
    "Tip": (117, 117, 117)       # Grey
}

def export_to_pdf(steps, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_auto_page_break(True, margin=15)

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    for step in steps:
        pdf.cell(0, 10, step["title"], ln=True)
        pdf.ln(5)
        if os.path.exists(step["filename"]):
            pdf.image(step["filename"], x=pdf.l_margin, w=page_w)
            pdf.ln(5)
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for i, step in enumerate(steps):
            pdf.add_page()
            
            # Add title
            pdf.set_font("Arial", "B", 16)
            title = step.get("title", f"Step {i+1}")
            pdf.cell(0, 10, title, ln=True)
            pdf.ln(5)
            
            # Add alerts above image
            for alert in step.get("alerts_above", []):
                pdf.set_font("Arial", "B", 12)
                alert_type = alert['type']
                color = ALERT_PDF_COLORS.get(alert_type, (128, 128, 128))
                pdf.set_fill_color(color[0], color[1], color[2])
                pdf.set_text_color(255, 255, 255)  # White text
                if alert_type == "Warning":
                    pdf.set_text_color(0, 0, 0)  # Black text for yellow background
                pdf.cell(0, 8, f"{alert['type']}: {alert['text']}", ln=True, fill=True)
                pdf.set_text_color(0, 0, 0)  # Reset to black
                pdf.ln(2)
            
            # Add image if it exists
            if os.path.exists(step["filename"]):
                # Calculate image size to fit page
                img_width = 180  # Max width for A4
                pdf.image(step["filename"], x=15, w=img_width)
                pdf.ln(img_width * 0.75)  # Approximate height
            
            # Add alerts below image
            for alert in step.get("alerts_below", []):
                pdf.set_font("Arial", "B", 12)
                alert_type = alert['type']
                color = ALERT_PDF_COLORS.get(alert_type, (128, 128, 128))
                pdf.set_fill_color(color[0], color[1], color[2])
                pdf.set_text_color(255, 255, 255)  # White text
                if alert_type == "Warning":
                    pdf.set_text_color(0, 0, 0)  # Black text for yellow background
                pdf.cell(0, 8, f"{alert['type']}: {alert['text']}", ln=True, fill=True)
                pdf.set_text_color(0, 0, 0)  # Reset to black
                pdf.ln(2)

        pdf.output(output_path)
        print(f"PDF exported to {output_path}")
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        raise