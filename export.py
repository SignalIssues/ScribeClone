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
        margin = 15
        # Disable automatic page breaks so we can control exactly two screenshots per page
        pdf.set_auto_page_break(auto=False, margin=margin)
        pdf.set_margins(margin, margin, margin)

        page_width = pdf.w - 2 * margin
        page_height = pdf.h - 2 * margin
        # Rough amount of vertical space reserved for title and alerts for each step
        reserved_height = 40
        max_img_height = (page_height / 2) - reserved_height

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
                    with Image.open(step["filename"]) as img:
                        orig_w, orig_h = img.size
                    scale = min(page_width / orig_w, max_img_height / orig_h)
                    img_w = orig_w * scale
                    img_h = orig_h * scale
                    pdf.image(step["filename"], x=margin, w=img_w, h=img_h)
                    pdf.ln(img_h)

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
