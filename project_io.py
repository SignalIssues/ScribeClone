from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QMessageBox, QScrollArea, QLineEdit, QHBoxLayout, QFrame,
    QListWidget, QListWidgetItem, QInputDialog, QTextEdit, QFileDialog, QDialog
    )
import os 
import json
import zipfile

def save_project_dialog(self):
    path, _ = QFileDialog.getSaveFileName(self, "Save Project", "*.zip", "Zip files (*.zip)")
    if not path:
        return
    save_project(self.step_data, path)

def save_project(steps, output_path):
    try:
        manifest = {
            "version": "1.0",
            "steps": []
        }
        
        for step in steps:
            step_data = {
                "filename": os.path.basename(step["filename"]),
                "title": step.get("title", ""),
                "alerts_above": step.get("alerts_above", []),
                "alerts_below": step.get("alerts_below", [])
            }
            manifest["steps"].append(step_data)

        with zipfile.ZipFile(output_path, 'w') as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            for step in steps:
                if os.path.exists(step["filename"]):
                    zf.write(step["filename"], os.path.basename(step["filename"]))
        
        print(f"Project saved to {output_path}")
    except Exception as e:
        print(f"Error saving project: {e}")
        raise

def load_project(self):
    path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Zip files (*.zip)")
    if not path:
        return
    # clear old screenshots
    for f in SCREENSHOT_DIR.glob("*.png"):
        f.unlink()
    steps = load_project(path, extract_to=str(SCREENSHOT_DIR))
    self.step_data = steps
    self.show_loaded_editor()