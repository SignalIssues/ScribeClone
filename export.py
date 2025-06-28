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

        def text_height(step):
            """Return the vertical space used by the title and alerts for a step."""
            height = 10  # title height
            height += 5  # spacing after title
            height += len(step.get("alerts_above", [])) * (8 + 2)
            height += len(step.get("alerts_below", [])) * (8 + 2)
            height += 5  # spacing after the step block
            return height

        def add_step(step, idx, max_image_height):
            """Render a single step using the provided maximum image height."""
            pdf.set_font("Arial", "B", 16)
            title = step.get("title", f"Step {idx + 1}")
            pdf.cell(0, 10, title, ln=True)
            pdf.ln(5)

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

            if os.path.exists(step["filename"]):
                with Image.open(step["filename"]) as img:
                    orig_w, orig_h = img.size
                scale = page_width / orig_w
                if max_image_height > 0:
                    scale = min(scale, max_image_height / orig_h)
                img_w = orig_w * scale
                img_h = orig_h * scale
                pdf.image(step["filename"], x=margin, w=img_w, h=img_h)
                pdf.ln(img_h)

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

        # Process steps two at a time so each page contains up to two screenshots
        i = 0
        while i < len(steps):
            pdf.add_page()

            step = steps[i]
            max_height = max((page_height / 2) - text_height(step), 0)
            add_step(step, i, max_height)
            i += 1

            if i >= len(steps):
                break

            step = steps[i]
            remaining = page_height - (pdf.get_y() - margin)
            max_height = remaining - text_height(step)
            if max_height < 0:
                pdf.add_page()
                max_height = max((page_height / 2) - text_height(step), 0)
            add_step(step, i, max_height)
            i += 1

        pdf.output(output_path)
        print(f"PDF exported to {output_path}")
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        raise
