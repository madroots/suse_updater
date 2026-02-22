from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QSystemTrayIcon
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QPixmap
from .advanced_window import AdvancedWindow

class MainWindow(QMainWindow):
    def __init__(self, check_icon, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Updater")
        self.setFixedSize(500, 350)
        
        # Save a reference to the main app's icon for checking state
        self.check_icon = check_icon
        self.setWindowIcon(self.check_icon)
        
        # Central Widget & Layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(20)
        
        # Main Status Icon (placeholder text/icon)
        self.status_icon = QLabel()
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_icon)
        
        # Main Status Text
        self.status_label = QLabel("Checking for updates...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.layout.addWidget(self.status_label)
        
        # Sub Status Text (e.g. details about updates)
        self.details_label = QLabel("Please wait.")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("color: #777;")
        self.layout.addWidget(self.details_label)
        
        # Update Button
        self.update_btn = QPushButton("Update Now")
        self.update_btn.setFixedSize(200, 50)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2F80ED;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1A73E8;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)
        self.update_btn.hide()
        self.layout.addWidget(self.update_btn, alignment=Qt.AlignCenter)
        
        # Advanced Button
        self.adv_btn = QPushButton("Advanced")
        self.adv_btn.setFixedSize(100, 30)
        self.adv_btn.setStyleSheet("color: #aaa; background: transparent; border: none;")
        self.layout.addWidget(self.adv_btn, alignment=Qt.AlignCenter)
        
        # Progress Bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate spinning
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        # Connect Advanced
        self.advanced_window = AdvancedWindow()
        self.adv_btn.clicked.connect(self.show_advanced)
        
        # Apply Dark Theme palette base
        self._apply_dark_theme()

    def _apply_dark_theme(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)
        
    def show_advanced(self):
        self.advanced_window.show()
        
    def _set_large_icon(self, qicon=None, emoji=""):
        if qicon:
            pixmap = qicon.pixmap(80, 80)
            self.status_icon.setPixmap(pixmap)
            self.status_icon.setText("")
        else:
            self.status_icon.setPixmap(QPixmap())
            self.status_icon.setText(emoji)
            self.status_icon.setStyleSheet("font-size: 64px;")

    def set_status(self, state, details="", updates_data=None):
        if state == "checking":
            self._set_large_icon(qicon=self.check_icon)
            self.status_label.setText("Checking for updates...")
            self.status_label.setStyleSheet("color: white;")
            self.details_label.setText("Please wait while we query the repositories.")
            self.update_btn.hide()
            self.progress_bar.hide()
            self.advanced_window.set_updating(True)
            
        elif state == "up_to_date":
            self._set_large_icon(emoji="🎉")
            self.status_label.setText("Your system is fully up to date!")
            self.status_label.setStyleSheet("color: #00C853;")
            
            # Explicitly state nothing to do
            self.details_label.setText("Zypper: Up to date\nFlatpaks: Up to date")
            self.update_btn.hide()
            self.progress_bar.hide()
            self.advanced_window.set_updating(False)
            
        elif state == "updates_ready":
            self._set_large_icon(emoji="📦")
            self.status_label.setText("Updates are available.")
            self.status_label.setStyleSheet("color: #FFD740;")
            
            z_up = updates_data.get('zypper_updates', 0) > 0
            fs_up = len(updates_data.get('flatpak_system_updates', []))
            fu_up = len(updates_data.get('flatpak_user_updates', []))
            
            z_text = "Updates Available" if z_up else "Up to date"
            f_text = f"{fs_up + fu_up} apps need updating" if (fs_up + fu_up) > 0 else "Up to date"
            
            sub_text = f"<b>OS Update (Zypper):</b> {z_text}<br>" \
                       f"<b>Apps (Flatpak):</b> {f_text}"
                       
            self.details_label.setText(sub_text)
            self.update_btn.show()
            self.update_btn.setText("Update All Now")
            self.update_btn.setEnabled(True)
            self.progress_bar.hide()
            self.advanced_window.set_updating(False)
            
        elif state == "conflicts":
            self._set_large_icon(emoji="⚠️")
            self.status_label.setText("Vendor Change / Conflicts Detected")
            self.status_label.setStyleSheet("color: #FF5252;")
            
            z_up = "CONFLICTING"
            fs_up = len(updates_data.get('flatpak_system_updates', []))
            fu_up = len(updates_data.get('flatpak_user_updates', []))
            f_text = f"{fs_up + fu_up} apps need updating" if (fs_up + fu_up) > 0 else "Up to date"

            self.details_label.setText(
                f"<b>OS Update (Zypper):</b> {z_up}<br>"
                f"<b>Apps (Flatpak):</b> {f_text}<br><br>"
                "Don't worry! This is normal on Tumbleweed.<br>"
                "Wait until tomorrow for maintainers to fix the dependencies.<br>"
                "<i>You can still update Flatpaks via the Advanced tab.</i>"
            )
            # Hide the big button so they don't force Zypper
            self.update_btn.hide()
            self.progress_bar.hide()
            self.advanced_window.set_updating(False)
            
        elif state == "updating":
            self._set_large_icon(emoji="⚙️")
            self.status_label.setText("Updating System...")
            self.status_label.setStyleSheet("color: white;")
            self.details_label.setText("Applying changes. This may take a while.\nCheck Advanced logs for details.")
            self.update_btn.setEnabled(False)
            self.progress_bar.show()
            self.advanced_window.set_updating(True)

        # Update the advanced window raw logs just in case they open it
        if updates_data:
            combined_log = updates_data.get('zypper_output', '') + "\n" + updates_data.get('flatpak_output', '')
            self.advanced_window.set_log(combined_log)
