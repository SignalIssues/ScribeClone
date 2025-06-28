# gui.py - Enhanced version with fixes
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QMessageBox, QScrollArea, QLineEdit, QHBoxLayout, QFrame,
    QListWidget, QListWidgetItem, QInputDialog, QTextEdit, QFileDialog, QDialog
    )
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QEventLoop
from pathlib import Path
import os
import sys
import threading
import time
from pynput import mouse
from mss import mss
from PIL import Image, ImageDraw
import json
import zipfile
from fpdf import FPDF
from export import export_to_pdf
from project_io import save_project, load_project

# Alert styles - Updated colors
ALERT_STYLES = {
    "Alert": "background-color: #f44336; color: white; border-radius: 5px; padding: 8px; font-weight: bold;",
    "Warning": "background-color: #ffeb3b; color: black; border-radius: 5px; padding: 8px; font-weight: bold;",
    "Note": "background-color: #2196f3; color: white; border-radius: 5px; padding: 8px; font-weight: bold;",
    "Tip": "background-color: #757575; color: white; border-radius: 5px; padding: 8px; font-weight: bold;"
}



# Settings
DEFAULT_SETTINGS = {
    "highlight_size": 40,
    "highlight_color": (255, 0, 0, 128),  # Red with 50% transparency
    "export_path": os.path.expanduser("~/Documents")
}

# Recorder functionality
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

screenshot_count = 0
mouse_listener = None
is_recording = False
current_settings = DEFAULT_SETTINGS.copy()

def find_monitor(monitors, x, y):
    for m in monitors:
        x0,y0,x1,y1 = m["left"], m["top"], m["left"]+m["width"], m["top"]+m["height"]
        if x0 <= x < x1 and y0 <= y < y1:
            return m
    return monitors[1]  # fallback

def qcolor_to_argb_hex(r,g,b,a):
    return f"#{a:02X}{r:02X}{g:02X}{b:02X}"

def draw_ring(img, x, y, radius, color):
    overlay = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    # outer circle
    d.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
    # inner cut-out for hollow ring
    inner = radius - 5
    d.ellipse((x-inner, y-inner, x+inner, y+inner), fill=(0,0,0,0))
    return Image.alpha_composite(img.convert("RGBA"), overlay)

def capture_click(x, y):
    global screenshot_count, current_settings
    try:
        with mss() as sct:
            mon = find_monitor(sct.monitors, x, y)
            shot = sct.grab(mon)
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # Add click indicator with settings
            draw = ImageDraw.Draw(img)
            radius = current_settings["highlight_size"] // 2
            color = current_settings["highlight_color"]
            
            # Create transparent overlay
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Draw circle with transparency
            overlay_draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=color,
                outline=color[:3] + (255,),  # Full opacity for outline
                width=3
            )
            
            # Composite the overlay onto the image
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            img = img.convert('RGB')

            filename = f"{SCREENSHOT_DIR}/step_{screenshot_count:03d}.png"
            img.save(filename)
            print(f"[+] Screenshot saved: {filename}")
            screenshot_count += 1
    except Exception as e:
        print(f"Error capturing screenshot: {e}")

def on_click(x, y, button, pressed):
    global is_recording
    if pressed and is_recording and button == mouse.Button.left:
        capture_click(x, y)

def start_recording():
    global mouse_listener, is_recording, screenshot_count
    screenshot_count = 0
    is_recording = True
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    print("[*] Recording started. Click around to capture steps!")

def stop_recording():
    global mouse_listener, is_recording
    is_recording = False
    if mouse_listener:
        mouse_listener.stop()
        mouse_listener = None
        print("[*] Recording stopped.")





class CaptureThread(QThread):
    screenshot_taken = pyqtSignal(str)  # emit filename when done

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self._running = True

    def run(self):
        with mss() as sct:
            while self._running:
                # blocking wait for click events… or poll a queue populated by mouse.Listener
                x, y = wait_for_click()  
                filename = capture_click_to_file(x, y, self.settings)
                self.screenshot_taken.emit(filename)

    def stop(self):
        self._running = False
        self.wait()



class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QFormLayout()
        
        # Highlight size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 100)
        self.size_spin.setValue(current_settings["highlight_size"])
        self.size_spin.setSuffix("px")
        layout.addRow("Highlight Size:", self.size_spin)
        
        # Highlight color
        self.color_button = QPushButton()
        color = current_settings["highlight_color"]
        self.color_button.setStyleSheet(f"background-color: rgba({color[0]}, {color[1]}, {color[2]}, {color[3]/255.0}); min-height: 30px;")
        self.color_button.setText("Click to change color")
        self.color_button.clicked.connect(self.choose_color)
        layout.addRow("Highlight Color:", self.color_button)
        
        # Export path
        export_layout = QHBoxLayout()
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setText(current_settings["export_path"])
        self.export_path_edit.setPlaceholderText("Choose default export folder...")
        export_layout.addWidget(self.export_path_edit)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_export_path)
        export_layout.addWidget(browse_button)
        
        layout.addRow("Default Export Path:", export_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
        
        self.current_color = color
    
    def qcolor_to_argb_hex(r,g,b,a):
        return f"#{a:02X}{r:02X}{g:02X}{b:02X}"

    def choose_color(self):
        hexcol = qcolor_to_argb_hex(color.red(), color.green(), color.blue(), 128)
        self.color_button.setStyleSheet(f"background-color: {hexcol}; min-height:30px;")

        color = QColorDialog.getColor()
        if color.isValid():
            # Convert to RGBA with 50% transparency
            self.current_color = (color.red(), color.green(), color.blue(), 128)
            self.color_button.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 0.5); min-height: 30px;")
    
    def browse_export_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Export Folder")
        if folder:
            self.export_path_edit.setText(folder)
    
    def get_settings(self):
        return {
            "highlight_size": self.size_spin.value(),
            "highlight_color": self.current_color,
            "export_path": self.export_path_edit.text()
        }

class ScribeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.screenshot_count = 0
        self.mouse_listener = None
        self.is_recording = False
        self.current_settings = DEFAULT_SETTINGS.copy()
        self.setWindowTitle("Local Scribe Tool")
        self.setGeometry(100, 100, 400, 200)
        self.step_data = []
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_status)
        self.recording_time = 0
        
        self.init_main_ui()

    def init_main_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("📸 Local Scribe Recorder")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Instructions
        self.status_label = QLabel("Click 'Start Recording' then click around your screen to capture steps")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Buttons
        self.record_button = QPushButton("🔴 Start Recording")
        self.record_button.clicked.connect(self.start_recording)
        self.record_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.record_button)

        self.stop_button = QPushButton("⏹️ Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(self.stop_button)

        # Load project button
        load_button = QPushButton("📁 Load Existing Project")
        load_button.clicked.connect(self.load_project_dialog)
        layout.addWidget(load_button)

        # Settings button
        settings_button = QPushButton("⚙️ Settings")
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)

        self.setLayout(layout)



    def start_recording(self):
        self.capture_thread = CaptureThread(self.current_settings)
        #self.capture_thread.screenshot_taken.connect(self.on_new_screenshot)
        self.capture_thread.start()
        self.recording_time = 0
        self.status_label.setText("🔴 Recording... Click anywhere to capture steps")
        self.record_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Start recording in thread
        self.recording_thread = threading.Thread(target=start_recording)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # Start timer for UI updates
        self.recording_timer.start(1000)

    def update_recording_status(self):
        self.recording_time += 1
        self.status_label.setText(f"🔴 Recording... ({self.recording_time}s) Click to capture steps")

    def stop_recording(self):
        stop_recording()
        self.recording_timer.stop()
        self.status_label.setText("Recording stopped. Loading editor...")
        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Wait a moment then show editor
        QTimer.singleShot(500, self.show_editor)

    def show_editor(self):
        # Clear current layout
        self.clear_layout()

        self.setWindowTitle("Step Editor")
        
        # Create scroll area for steps
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Load screenshots and create step data
        self.step_data = []
        screenshot_folder = "screenshots"
        
        if os.path.exists(screenshot_folder):
            filenames = sorted([f for f in os.listdir(screenshot_folder) if f.endswith('.png')])
            
            for filename in filenames:
                step_widget = self.create_step_widget(os.path.join(screenshot_folder, filename))
                scroll_layout.addWidget(step_widget)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        
        # Main layout
        # Reuse existing layout instead of creating new one
        layout = self.layout()
        layout.addWidget(QLabel("📝 Edit your captured steps:"))
        layout.addWidget(scroll)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📄 Export PDF")
        export_btn.clicked.connect(self.export_pdf)
        button_layout.addWidget(export_btn)
        
        save_btn = QPushButton("💾 Save Project")
        save_btn.clicked.connect(self.save_project)
        button_layout.addWidget(save_btn)
        
        new_btn = QPushButton("🆕 New Recording")
        new_btn.clicked.connect(self.new_recording)
        button_layout.addWidget(new_btn)
        
        layout.addLayout(button_layout)

    def create_step_widget(self, image_path):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; margin: 5px; padding: 10px; }")
        
        layout = QVBoxLayout()
        
        # Title input
        title_input = QLineEdit()
        title_input.setPlaceholderText(f"Step description for {os.path.basename(image_path)}")
        layout.addWidget(title_input)
        
        # Alert above button
        alert_above_btn = QPushButton("⚠️ Add Alert Above Image")
        alert_above_btn.clicked.connect(
            lambda _l=layout: self.add_alert_dialog(_l, "above")
            )
        layout.addWidget(alert_above_btn)
        
        # Image
        label = QLabel()
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaledToWidth(500, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Alert below button
        alert_below_btn = QPushButton("⚠️ Add Alert Below Image")
        alert_below_btn.clicked.connect(lambda: self.add_alert_dialog(layout, "below"))
        layout.addWidget(alert_below_btn)
        
        frame.setLayout(layout)
        
        # Store step data
        step_data = {
            "filename": image_path,
            "title_widget": title_input,
            "layout": layout,
            "alerts_above": [],
            "alerts_below": []
        }
        self.step_data.append(step_data)
        
        return frame

    def add_alert_dialog(self, parent_layout, position):
        alert_type, ok = QInputDialog.getItem(
            self, "Select Alert Type", "Choose alert type:", 
            list(ALERT_STYLES.keys()), 0, False
        )
        
        if ok and alert_type:
            self.add_alert_box(alert_type, "", parent_layout, position)

    def add_alert_box(self, alert_type, text, parent_layout, position):
        alert_widget = QTextEdit()
        alert_widget.setPlaceholderText(f"Enter {alert_type.lower()} text here...")
        if text:
            alert_widget.setPlainText(text)
        alert_widget.setStyleSheet(ALERT_STYLES[alert_type])
        alert_widget.setMaximumHeight(80)
        
        # Find the right position to insert
        if position == "above":
            # Insert after title, before image
            parent_layout.insertWidget(2, alert_widget)
        else:
            # Add at the end
            parent_layout.addWidget(alert_widget)
        
        # Update step data
        for step in self.step_data:
            if step["layout"] == parent_layout:
                alert_data = {"type": alert_type, "text": text, "widget": alert_widget}
                if position == "above":
                    step["alerts_above"].append(alert_data)
                else:
                    step["alerts_below"].append(alert_data)
                break

    def export_pdf(self):
        try:
            # Get export location
            default_name = "scribe_export.pdf"
            if current_settings["export_path"]:
                default_path = os.path.join(current_settings["export_path"], default_name)
            else:
                default_path = default_name
                
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export PDF", default_path, "PDF files (*.pdf)"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Update step data with current values
            for step in self.step_data:
                step["title"] = step["title_widget"].text()
                
                # Update alert texts
                for alert in step["alerts_above"]:
                    alert["text"] = alert["widget"].toPlainText()
                for alert in step["alerts_below"]:
                    alert["text"] = alert["widget"].toPlainText()
            
            export_to_pdf(self.step_data, file_path)
            QMessageBox.information(self, "Export Complete", f"PDF exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")

    def save_project(self):
        try:
            # Update step data
            for step in self.step_data:
                step["title"] = step["title_widget"].text()
                
                # Update alert texts
                for alert in step["alerts_above"]:
                    alert["text"] = alert["widget"].toPlainText()
                for alert in step["alerts_below"]:
                    alert["text"] = alert["widget"].toPlainText()
            
            save_project(self.step_data, "scribe_project.zip")
            QMessageBox.information(self, "Project Saved", "Project saved as 'scribe_project.zip'")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save project:\n{str(e)}")

    def load_project_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "Zip files (*.zip)"
        )
        
        if file_path:
            try:
                self.step_data = load_project(file_path)
                self.show_loaded_editor()
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load project:\n{str(e)}")

    def show_loaded_editor(self):
        # Similar to show_editor but for loaded data
        self.clear_layout()

        self.setWindowTitle("Loaded Project Editor")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Create widgets for loaded steps
        for step in self.step_data:
            step_widget = self.create_loaded_step_widget(step)
            scroll_layout.addWidget(step_widget)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        
        # Reuse existing layout
        layout = self.layout()
        layout.addWidget(QLabel("📝 Editing loaded project:"))
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        export_btn = QPushButton("📄 Export PDF")
        export_btn.clicked.connect(self.export_pdf)
        button_layout.addWidget(export_btn)
        
        save_btn = QPushButton("💾 Save Project")
        save_btn.clicked.connect(self.save_project)
        button_layout.addWidget(save_btn)
        
        new_btn = QPushButton("🆕 New Recording")
        new_btn.clicked.connect(self.new_recording)
        button_layout.addWidget(new_btn)
        
        layout.addLayout(button_layout)

    def create_loaded_step_widget(self, step_data):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; margin: 5px; padding: 10px; }")
        
        layout = QVBoxLayout()
        
        # Title
        title_input = QLineEdit()
        title_input.setText(step_data.get("title", ""))
        title_input.setPlaceholderText("Step description")
        layout.addWidget(title_input)
        step_data["title_widget"] = title_input
        
        # Alerts above
        for alert in step_data.get("alerts_above", []):
            alert_widget = QTextEdit()
            alert_widget.setPlainText(alert["text"])
            alert_widget.setStyleSheet(ALERT_STYLES[alert["type"]])
            alert_widget.setMaximumHeight(80)
            layout.addWidget(alert_widget)
            alert["widget"] = alert_widget
        
        # Image
        label = QLabel()
        if os.path.exists(step_data["filename"]):
            pixmap = QPixmap(step_data["filename"]).scaledToWidth(500, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Alerts below
        for alert in step_data.get("alerts_below", []):
            alert_widget = QTextEdit()
            alert_widget.setPlainText(alert["text"])
            alert_widget.setStyleSheet(ALERT_STYLES[alert["type"]])
            alert_widget.setMaximumHeight(80)
            layout.addWidget(alert_widget)
            alert["widget"] = alert_widget
        
        frame.setLayout(layout)
        step_data["layout"] = layout
        
        return frame

    def new_recording(self):
        # Clear screenshots folder
        screenshot_folder = "screenshots"
        if os.path.exists(screenshot_folder):
            for file in os.listdir(screenshot_folder):
                if file.endswith('.png'):
                    os.remove(os.path.join(screenshot_folder, file))

        # Reset step data and screenshot count
        self.step_data = []
        global screenshot_count
        screenshot_count = 0

        # Detach and delete existing layout so we can reinitialize UI
        old_layout = self.layout()
        if old_layout:
            old_layout.setParent(None)
            old_layout.deleteLater()

        # Restore main UI
        self.setWindowTitle("Local Scribe Tool")
        self.resize(400, 200)
        self.init_main_ui()

    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_() == QDialog.Accepted:
            global current_settings
            current_settings = settings_dialog.get_settings()

    def clear_layout(self, layout=None):
        if layout is None:
            layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
            elif child_layout := item.layout():
                self.clear_layout(child_layout)
        # finally remove the layout itself if top‐level
        if layout.parent() is None:
            layout.deleteLater()

    def clear_child_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_child_layout(child.layout())

def run_gui():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    window = ScribeApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_gui()