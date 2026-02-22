from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox, QApplication
from PySide6.QtCore import Qt, Signal
import subprocess
import os

class WizardWindow(QWidget):
    setup_complete = Signal()
    setup_skipped = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Updater - Initial Setup")
        self.setFixedSize(550, 400)
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(20)
        
        # Icon
        self.icon_label = QLabel("🛡️")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 64px;")
        self.layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel("Rootless Background Checks")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        self.layout.addWidget(self.title_label)
        
        # Description
        self.desc_label = QLabel(
            "To accurately check for Tumbleweed vendor conflicts in the background,\n"
            "this app needs to run 'sudo zypper dup --dry-run'.\n\n"
            "Normally, this requires your password every 4 hours.\n\n"
            "We can install a secure sudoers rule that allows ONLY this specific dry-run\n"
            "command to scan without asking for a password.\n"
            "(Actual updates still require your password)"
        )
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("font-size: 14px; color: #d4d4d4;")
        self.layout.addWidget(self.desc_label)
        
        # Buttons
        self.btn_layout = QHBoxLayout()
        
        self.skip_btn = QPushButton("Skip (Manual Checks Only)")
        self.skip_btn.setFixedSize(220, 45)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #333; }
        """)
        self.skip_btn.clicked.connect(self.on_skip)
        
        self.install_btn = QPushButton("Install Rule (Requires Root)")
        self.install_btn.setFixedSize(220, 45)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #2F80ED;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1A73E8; }
        """)
        self.install_btn.clicked.connect(self.on_install)
        
        self.btn_layout.addWidget(self.skip_btn)
        self.btn_layout.addWidget(self.install_btn)
        self.layout.addLayout(self.btn_layout)
        
        self._apply_dark_theme()

    def _apply_dark_theme(self):
        self.setStyleSheet("QWidget { background-color: #282828; }")
        
    def on_skip(self):
        self.setup_skipped.emit()
        self.close()
        
    def on_install(self):
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "install_sudoers.sh")
        
        try:
            # Change button text to show progress
            self.install_btn.setText("Installing...")
            self.install_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)
            QApplication.processEvents()
            
            # Run the bash script via pkexec so it has root to write to /etc/sudoers.d/
            subprocess.run(["pkexec", "bash", script_path], check=True)
            
            # Test if the rule actually works!
            self.install_btn.setText("Testing Rule...")
            QApplication.processEvents()
            
            # If the rule works, this command should succeed WITHOUT asking for a password.
            # -n tells sudo to fail immediately if a password is required, rather than waiting.
            test_cmd = ["sudo", "-n", "zypper", "--non-interactive", "dup", "--dry-run"]
            test_proc = subprocess.run(test_cmd, capture_output=True, text=True)
            
            if test_proc.returncode != 0:
                raise Exception(f"Rule installed, but test failed (Code {test_proc.returncode}).\n{test_proc.stderr}")

            self.setup_complete.emit()
            self.close()
            
        except subprocess.CalledProcessError as e:
            self._show_error("Failed to install the rule via pkexec.")
            self._reset_buttons()
        except Exception as e:
            self._show_error(str(e))
            self._reset_buttons()
            
    def _show_error(self, message):
        err = QMessageBox(self)
        err.setIcon(QMessageBox.Critical)
        err.setWindowTitle("Setup Failed")
        err.setText(message)
        err.exec()
        
    def _reset_buttons(self):
        self.install_btn.setText("Install Rule (Requires Root)")
        self.install_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
