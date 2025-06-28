from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton,
    QHBoxLayout, QColorDialog, QLineEdit, QFileDialog
)
from PyQt5.QtGui import QColor

from settings import current_settings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(400, 300)

        layout = QFormLayout(self)

        # Highlight size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 100)
        self.size_spin.setValue(current_settings["highlight_size"])
        self.size_spin.setSuffix("px")
        layout.addRow("Highlight Size:", self.size_spin)

        # Highlight color
        self.color_button = QPushButton()
        color = current_settings["highlight_color"]
        self.color_button.setStyleSheet(
            f"background-color: rgba({color[0]}, {color[1]}, {color[2]}, {color[3]/255.0}); min-height: 30px;"
        )
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

        self.current_color = color

    def choose_color(self):
        initial = QColor(*self.current_color[:3])
        chosen = QColorDialog.getColor(initial, self, "Choose Highlight Color")
        if chosen.isValid():
            self.current_color = (
                chosen.red(),
                chosen.green(),
                chosen.blue(),
                128,
            )
            self.color_button.setStyleSheet(
                f"background-color: rgba({chosen.red()}, {chosen.green()}, {chosen.blue()}, 0.5); min-height: 30px;"
            )

    def browse_export_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Export Folder")
        if folder:
            self.export_path_edit.setText(folder)

    def get_settings(self):
        return {
            "highlight_size": self.size_spin.value(),
            "highlight_color": self.current_color,
            "export_path": self.export_path_edit.text(),
        }
