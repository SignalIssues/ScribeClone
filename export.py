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
    """Export the recorded steps to a PDF with two screenshots per page."""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Process steps two at a time so each page contains up to two screenshots
        for page_start in range(0, len(steps), 2):
            pdf.add_page()

            # Add up to two steps on the current page
            for offset in range(2):
                idx = page_start + offset
                if idx >= len(steps):
                    break
                step = steps[idx]

                # Add title
                pdf.set_font("Arial", "B", 16)
                title = step.get("title", f"Step {idx + 1}")
                pdf.cell(0, 10, title, ln=True)
                pdf.ln(5)

                # Add alerts above image
                for alert in step.get("alerts_above", []):
                    pdf.set_font("Arial", "B", 12)
                    alert_type = alert['type']
                    color = ALERT_PDF_COLORS.get(alert_type, (128, 128, 128))
                    pdf.set_fill_color(color[0], color[1], color[2])
                    pdf.set_text_color(255, 255, 255)
                    if alert_type == "Warning":
                        pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 8, f"{alert['type']}: {alert['text']}", ln=True, fill=True)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(2)

                # Add image if it exists
                if os.path.exists(step["filename"]):
                    img_width = 180  # Max width for A4
                    pdf.image(step["filename"], x=15, w=img_width)
                    pdf.ln(img_width * 0.75)

                # Add alerts below image
                for alert in step.get("alerts_below", []):
                    pdf.set_font("Arial", "B", 12)
                    alert_type = alert['type']
                    color = ALERT_PDF_COLORS.get(alert_type, (128, 128, 128))
                    pdf.set_fill_color(color[0], color[1], color[2])
                    pdf.set_text_color(255, 255, 255)
                    if alert_type == "Warning":
                        pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 8, f"{alert['type']}: {alert['text']}", ln=True, fill=True)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(2)

                pdf.ln(5)

        pdf.output(output_path)
        print(f"PDF exported to {output_path}")
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        raise
