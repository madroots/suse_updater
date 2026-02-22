import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QPushButton, QGroupBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QSettings, Signal
from i18n import get_text

class SettingsWindow(QWidget):
    settings_changed = Signal()
    trigger_wizard = Signal()
    trigger_logs = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(get_text("settings_title"))
        self.resize(450, 500)
        
        self.settings = QSettings("SuseUpdater", "OpenSUSE_Tool")
        
        self.layout = QVBoxLayout(self)
        
        # --- Update Engines Group ---
        self.engines_group = QGroupBox(get_text("engines_group"))
        self.engines_layout = QVBoxLayout(self.engines_group)
        
        self.zypper_cb = QCheckBox(get_text("check_zypper_label"))
        self.flatpak_cb = QCheckBox(get_text("check_flatpak_label"))
        
        # Load values (default to true)
        self.zypper_cb.setChecked(self.settings.value("check_zypper", True, type=bool))
        self.flatpak_cb.setChecked(self.settings.value("check_flatpak", True, type=bool))
        
        self.engines_layout.addWidget(self.zypper_cb)
        self.engines_layout.addWidget(self.flatpak_cb)
        
        self.layout.addWidget(self.engines_group)
        
        # --- System Group ---
        self.sys_group = QGroupBox(get_text("sys_behavior"))
        self.sys_layout = QVBoxLayout(self.sys_group)
        
        self.autostart_cb = QCheckBox(get_text("autostart"))
        self.autostart_cb.setChecked(self.is_autostart_enabled())
        self.sys_layout.addWidget(self.autostart_cb)
        
        # Language Picker
        self.lang_layout = QHBoxLayout()
        self.lang_label = QLabel(f"{get_text('language')}:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Slovenčina"])
        current_lang = self.settings.value("language", "en")
        self.lang_combo.setCurrentIndex(1 if current_lang == "sk" else 0)
        self.lang_layout.addWidget(self.lang_label)
        self.lang_layout.addWidget(self.lang_combo)
        self.sys_layout.addLayout(self.lang_layout)
        
        # --- Advanced Group ---
        self.adv_group = QGroupBox(get_text("adv_utilities"))
        self.adv_layout = QVBoxLayout(self.adv_group)
        
        self.logs_btn = QPushButton(get_text("open_logs"))
        self.logs_btn.clicked.connect(self._on_logs_clicked)
        self.adv_layout.addWidget(self.logs_btn)
        
        self.sudoers_btn = QPushButton(get_text("reinstall_sudoers"))
        self.sudoers_btn.clicked.connect(self._on_sudoers_clicked)
        self.adv_layout.addWidget(self.sudoers_btn)
        
        self.remove_btn = QPushButton(get_text("remove_sudoers"))
        self.remove_btn.setStyleSheet("""
            QPushButton { background-color: #aa2222; }
            QPushButton:hover { background-color: #ff3333; }
        """)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.adv_layout.addWidget(self.remove_btn)
        
        self.layout.addWidget(self.sys_group)
        self.layout.addWidget(self.adv_group)
        
        self.layout.addStretch()
        
        # --- Action Buttons ---
        self.btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(get_text("save"))
        self.save_btn.clicked.connect(self.save)
        
        self.cancel_btn = QPushButton(get_text("cancel"))
        self.cancel_btn.clicked.connect(self.close)
        
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.cancel_btn)
        self.btn_layout.addWidget(self.save_btn)
        
        self.layout.addLayout(self.btn_layout)
        
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #282828; color: white; }
            QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 15px; padding: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QCheckBox { font-size: 14px; padding: 5px 0; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QComboBox { background: #333; color: white; border: 1px solid #555; border-radius: 4px; padding: 3px; }
            QComboBox::drop-down { border: none; }
            QPushButton { background-color: #444; border-radius: 4px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #555; }
        """)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #2F80ED; border-radius: 4px; padding: 8px 16px; font-weight: bold;}
            QPushButton:hover { background-color: #1A73E8; }
        """)
        
    def _on_sudoers_clicked(self):
        self.trigger_wizard.emit()
        self.close()

    def _on_logs_clicked(self):
        self.trigger_logs.emit()
        self.close()
        
    def _on_remove_clicked(self):
        reply = QMessageBox.question(
            self, get_text("remove_confirm_title"),
            get_text("remove_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            import subprocess
            subprocess.run(["pkexec", "rm", "-f", "/etc/sudoers.d/suse-updater"])
            self.zypper_cb.setChecked(False) # Turn off the check so the script doesn't loop fail
            self.save()

    def get_autostart_path(self):
        return os.path.expanduser("~/.config/autostart/suse-updater.desktop")

    def is_autostart_enabled(self):
        return os.path.exists(self.get_autostart_path())

    def toggle_autostart(self, enable):
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_file = self.get_autostart_path()
        
        if enable:
            os.makedirs(autostart_dir, exist_ok=True)
            
            # Detect if running as AppImage (e.g., via Gear Lever)
            appimage_path = os.getenv("APPIMAGE")
            if appimage_path:
                exec_cmd = f"\"{appimage_path}\""
                icon = "system-software-update"
            else:
                # If running from source (development)
                venv_python = os.path.abspath(sys.executable)
                main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
                exec_cmd = f"{venv_python} {main_script}"
                
                # Try to use our generated SVG
                icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "tray_green.svg"))
                icon = icon_path if os.path.exists(icon_path) else "system-software-update"
                
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=SUSE Updater
Comment=Background system updater
Exec={exec_cmd}
Icon={icon}
Terminal=false
Categories=System;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""
            with open(desktop_file, "w") as f:
                f.write(desktop_content)
        else:
            if os.path.exists(desktop_file):
                os.remove(desktop_file)

    def save(self):
        lang = "sk" if self.lang_combo.currentIndex() == 1 else "en"
        self.settings.setValue("language", lang)
        self.settings.setValue("check_zypper", self.zypper_cb.isChecked())
        self.settings.setValue("check_flatpak", self.flatpak_cb.isChecked())
        self.toggle_autostart(self.autostart_cb.isChecked())
        
        self.refresh_texts()
        self.settings_changed.emit()
        self.close()

    def refresh_texts(self):
        self.setWindowTitle(get_text("settings_title"))
        self.engines_group.setTitle(get_text("engines_group"))
        self.zypper_cb.setText(get_text("check_zypper_label"))
        self.flatpak_cb.setText(get_text("check_flatpak_label"))
        self.sys_group.setTitle(get_text("sys_behavior"))
        self.autostart_cb.setText(get_text("autostart"))
        self.lang_label.setText(f"{get_text('language')}:")
        self.adv_group.setTitle(get_text("adv_utilities"))
        self.logs_btn.setText(get_text("open_logs"))
        self.sudoers_btn.setText(get_text("reinstall_sudoers"))
        self.remove_btn.setText(get_text("remove_sudoers"))
        self.save_btn.setText(get_text("save"))
        self.cancel_btn.setText(get_text("cancel"))
