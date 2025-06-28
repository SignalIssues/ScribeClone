import os
import sys
import threading

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QMessageBox, QScrollArea, QLineEdit, QHBoxLayout, QFrame,
    QInputDialog, QTextEdit, QFileDialog
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer

import recorder
import settings
from export import export_to_pdf
from project_io import save_project, load_project
from .dialogs import SettingsDialog

ALERT_STYLES = {
    "Alert": "background-color: #f44336; color: white; border-radius: 5px; padding: 8px; font-weight: bold;",
    "Warning": "background-color: #ffeb3b; color: black; border-radius: 5px; padding: 8px; font-weight: bold;",
    "Note": "background-color: #2196f3; color: white; border-radius: 5px; padding: 8px; font-weight: bold;",
    "Tip": "background-color: #757575; color: white; border-radius: 5px; padding: 8px; font-weight: bold;",
}


class ScribeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.capture_thread = None
        self.recording_thread = None
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_status)
        self.recording_time = 0
        self.step_data = []

        self.setWindowTitle("Local Scribe Tool")
        self.setGeometry(100, 100, 400, 200)

        self.init_main_ui()

    def init_main_ui(self):
        layout = self.layout() or QVBoxLayout()
        if self.layout() is None:
            self.setLayout(layout)
        else:
            self.clear_layout(layout)

        title = QLabel("\U0001f4f8 Local Scribe Recorder")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        self.status_label = QLabel("Click 'Start Recording' then click around your screen to capture steps")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.record_button = QPushButton("\U0001f534 Start Recording")
        self.record_button.clicked.connect(self.start_recording)
        self.record_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }"
        )
        layout.addWidget(self.record_button)

        self.stop_button = QPushButton("\u23f9\ufe0f Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }"
        )
        layout.addWidget(self.stop_button)

        load_button = QPushButton("\U0001f4c1 Load Existing Project")
        load_button.clicked.connect(self.load_project_dialog)
        layout.addWidget(load_button)

        settings_button = QPushButton("\u2699\ufe0f Settings")
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)

    # Recording control
    def start_recording(self):
        self.capture_thread = recorder.CaptureThread(settings.current_settings)
        self.capture_thread.start()
        self.recording_time = 0
        self.status_label.setText("\U0001f534 Recording... Click anywhere to capture steps")
        self.record_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.recording_thread = threading.Thread(target=recorder.start_recording, daemon=True)
        self.recording_thread.start()

        self.recording_timer.start(1000)

    def update_recording_status(self):
        self.recording_time += 1
        self.status_label.setText(f"\U0001f534 Recording... ({self.recording_time}s) Click to capture steps")

    def stop_recording(self):
        recorder.stop_recording()
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread = None
        self.recording_timer.stop()
        self.status_label.setText("Recording stopped. Loading editor...")
        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QTimer.singleShot(500, self.show_editor)

    # Editor UI
    def show_editor(self):
        self.clear_layout()
        self.setWindowTitle("Step Editor")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        self.step_data = []
        folder = recorder.SCREENSHOT_DIR
        if folder.exists():
            filenames = sorted(f.name for f in folder.glob("*.png"))
            for name in filenames:
                step_widget = self.create_step_widget(str(folder / name))
                scroll_layout.addWidget(step_widget)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)

        layout = self.layout()
        layout.addWidget(QLabel("\U0001f4dd Edit your captured steps:"))
        layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        export_btn = QPushButton("\U0001f4c4 Export PDF")
        export_btn.clicked.connect(self.export_pdf)
        button_layout.addWidget(export_btn)

        save_btn = QPushButton("\U0001f4be Save Project")
        save_btn.clicked.connect(self.save_project)
        button_layout.addWidget(save_btn)

        new_btn = QPushButton("\U0001f195 New Recording")
        new_btn.clicked.connect(self.new_recording)
        button_layout.addWidget(new_btn)

        layout.addLayout(button_layout)

    def create_step_widget(self, image_path):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; margin: 5px; padding: 10px; }")

        layout = QVBoxLayout()
        title_input = QLineEdit()
        title_input.setPlaceholderText(f"Step description for {os.path.basename(image_path)}")
        layout.addWidget(title_input)

        alert_above_btn = QPushButton("\u26a0\ufe0f Add Alert Above Image")
        alert_above_btn.clicked.connect(lambda checked=False, _l=layout: self.add_alert_dialog(_l, "above"))
        layout.addWidget(alert_above_btn)

        label = QLabel()
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaledToWidth(500, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        alert_below_btn = QPushButton("\u26a0\ufe0f Add Alert Below Image")
        alert_below_btn.clicked.connect(lambda checked=False, _l=layout: self.add_alert_dialog(_l, "below"))
        layout.addWidget(alert_below_btn)

        frame.setLayout(layout)
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
            self, "Select Alert Type", "Choose alert type:", list(ALERT_STYLES.keys()), 0, False
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

        if position == "above":
            parent_layout.insertWidget(2, alert_widget)
        else:
            parent_layout.addWidget(alert_widget)

        for step in self.step_data:
            if step["layout"] == parent_layout:
                alert_data = {"type": alert_type, "text": text, "widget": alert_widget}
                if position == "above":
                    step["alerts_above"].append(alert_data)
                else:
                    step["alerts_below"].append(alert_data)
                break

    # Export/Save/Load helpers
    def export_pdf(self):
        try:
            default_name = "scribe_export.pdf"
            if settings.current_settings["export_path"]:
                default_path = os.path.join(settings.current_settings["export_path"], default_name)
            else:
                default_path = default_name
            file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", default_path, "PDF files (*.pdf)")
            if not file_path:
                return
            for step in self.step_data:
                step["title"] = step["title_widget"].text()
                for alert in step["alerts_above"]:
                    alert["text"] = alert["widget"].toPlainText()
                for alert in step["alerts_below"]:
                    alert["text"] = alert["widget"].toPlainText()
            export_to_pdf(self.step_data, file_path)
            QMessageBox.information(self, "Export Complete", f"PDF exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{e}")

    def save_project(self):
        try:
            for step in self.step_data:
                step["title"] = step["title_widget"].text()
                for alert in step["alerts_above"]:
                    alert["text"] = alert["widget"].toPlainText()
                for alert in step["alerts_below"]:
                    alert["text"] = alert["widget"].toPlainText()
            save_project(self.step_data, "scribe_project.zip")
            QMessageBox.information(self, "Project Saved", "Project saved as 'scribe_project.zip'")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save project:\n{e}")

    def load_project_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Zip files (*.zip)")
        if file_path:
            try:
                self.step_data = load_project(file_path, extract_to=str(recorder.SCREENSHOT_DIR))
                self.show_loaded_editor()
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load project:\n{e}")

    def show_loaded_editor(self):
        self.clear_layout()
        self.setWindowTitle("Loaded Project Editor")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        for step in self.step_data:
            step_widget = self.create_loaded_step_widget(step)
            scroll_layout.addWidget(step_widget)
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)

        layout = self.layout()
        layout.addWidget(QLabel("\U0001f4dd Editing loaded project:"))
        layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        export_btn = QPushButton("\U0001f4c4 Export PDF")
        export_btn.clicked.connect(self.export_pdf)
        button_layout.addWidget(export_btn)

        save_btn = QPushButton("\U0001f4be Save Project")
        save_btn.clicked.connect(self.save_project)
        button_layout.addWidget(save_btn)

        new_btn = QPushButton("\U0001f195 New Recording")
        new_btn.clicked.connect(self.new_recording)
        button_layout.addWidget(new_btn)

        layout.addLayout(button_layout)

    def create_loaded_step_widget(self, step_data):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; margin: 5px; padding: 10px; }")

        layout = QVBoxLayout()
        title_input = QLineEdit()
        title_input.setText(step_data.get("title", ""))
        title_input.setPlaceholderText("Step description")
        layout.addWidget(title_input)
        step_data["title_widget"] = title_input

        for alert in step_data.get("alerts_above", []):
            alert_widget = QTextEdit()
            alert_widget.setPlainText(alert["text"])
            alert_widget.setStyleSheet(ALERT_STYLES[alert["type"]])
            alert_widget.setMaximumHeight(80)
            layout.addWidget(alert_widget)
            alert["widget"] = alert_widget

        label = QLabel()
        if os.path.exists(step_data["filename"]):
            pixmap = QPixmap(step_data["filename"]).scaledToWidth(500, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

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
        folder = recorder.SCREENSHOT_DIR
        if folder.exists():
            for file in folder.glob("*.png"):
                file.unlink()

        self.step_data = []
        recorder.screenshot_count = 0

        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread = None

        recorder.clear_click_queue()

        self.setWindowTitle("Local Scribe Tool")
        self.init_main_ui()
        self.adjustSize()

    def show_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            settings.current_settings = dlg.get_settings()
            settings.save_settings(settings.current_settings)

    # Utility
    def clear_layout(self, layout=None):
        if layout is None:
            layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
        if layout.parent() is None:
            layout.deleteLater()


def run_gui():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ScribeApp()
    window.show()
    sys.exit(app.exec_())

