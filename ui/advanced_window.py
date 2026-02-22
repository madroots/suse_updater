from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, QScrollArea, 
    QCheckBox, QPushButton, QHBoxLayout, QGroupBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from i18n import get_text

class AdvancedWindow(QWidget):
    update_selected = Signal(bool, list, list) # run_zypper, system_apps, user_apps

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(get_text("selective_updates"))
        self.resize(750, 600)
        
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # --- Tab 1: Selective Updates ---
        self.tab_flatpaks = QWidget()
        self.fp_layout = QVBoxLayout(self.tab_flatpaks)
        
        self.fp_info = QLabel(get_text("selective_updates") + ":")
        self.fp_info.setStyleSheet("padding: 5px; color: #ccc;")
        self.fp_layout.addWidget(self.fp_info)
        
        self.fp_scroll = QScrollArea()
        self.fp_scroll.setWidgetResizable(True)
        self.fp_scroll_content = QWidget()
        self.fp_scroll_layout = QVBoxLayout(self.fp_scroll_content)
        self.fp_scroll_layout.setAlignment(Qt.AlignTop)
        
        self.zypper_checkbox = None
        self.sys_checkboxes = {}
        self.usr_checkboxes = {}
        
        self.fp_scroll.setWidget(self.fp_scroll_content)
        self.fp_layout.addWidget(self.fp_scroll, stretch=1)
        
        self.update_btn = QPushButton(get_text("update_all"))
        self.update_btn.clicked.connect(self._on_update_clicked)
        self.update_btn.setEnabled(False)
        self.fp_layout.addWidget(self.update_btn)
        
        self.tabs.addTab(self.tab_flatpaks, get_text("selective_updates"))
        
        # --- Tab 2: Raw Logs ---
        self.tab_logs = QWidget()
        self.log_layout = QVBoxLayout(self.tab_logs)
        
        self.log_label = QLabel(get_text("raw_logs") + ":")
        self.log_layout.addWidget(self.log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #d4d4d4;
                font-family: monospace;
                font-size: 13px;
                padding: 10px;
                border: 1px solid #444;
            }
        """)
        self.log_layout.addWidget(self.log_area, stretch=1)
        
        self.logs_tab_index = self.tabs.addTab(self.tab_logs, get_text("raw_logs"))
        
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #282828; color: white; }
            QTabWidget::pane { border: 1px solid #444; background: #2f2f2f; }
            QTabBar::tab { background: #333; color: #aaa; padding: 10px 20px; border: 1px solid #444; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px;}
            QTabBar::tab:selected { background: #2f2f2f; color: white; border-top: 2px solid #2F80ED; }
            QScrollArea { border: 1px solid #444; background: #1a1a1a; }
            QPushButton { background-color: #2F80ED; border-radius: 4px; padding: 8px; font-weight: bold; font-size: 14px;}
            QPushButton:hover { background-color: #1A73E8; }
            QPushButton:disabled { background-color: #444; color: #888; }
            QCheckBox { font-size: 14px; padding: 5px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
        
    def populate_updates(self, has_zypper, system_apps, user_apps):
        # Clear existing
        for i in reversed(range(self.fp_scroll_layout.count())): 
            self.fp_scroll_layout.itemAt(i).widget().setParent(None)
            
        self.zypper_checkbox = None
        self.sys_checkboxes.clear()
        self.usr_checkboxes.clear()
        
        if not has_zypper and not system_apps and not user_apps:
            self.fp_scroll_layout.addWidget(QLabel(get_text("no_updates")))
            self.update_btn.setEnabled(False)
            return

        self.update_btn.setEnabled(True)
        
        if has_zypper:
            self.fp_scroll_layout.addWidget(QLabel(f"<b>{get_text('os_update_zypper')}:</b>"))
            self.zypper_checkbox = QCheckBox("OpenSUSE System Packages") # Packages names themselves aren't usually translated
            self.zypper_checkbox.setChecked(True)
            self.fp_scroll_layout.addWidget(self.zypper_checkbox)
            self.fp_scroll_layout.addWidget(QLabel("")) # Spacing
            
        if system_apps:
            self.fp_scroll_layout.addWidget(QLabel(f"<b>System {get_text('apps_flatpaks')}:</b>"))
            for app in system_apps:
                cb = QCheckBox(app)
                cb.setChecked(True)
                self.sys_checkboxes[app] = cb
                self.fp_scroll_layout.addWidget(cb)
            self.fp_scroll_layout.addWidget(QLabel("")) # Spacing
                
        if user_apps:
            self.fp_scroll_layout.addWidget(QLabel(f"<b>User {get_text('apps_flatpaks')}:</b>"))
            for app in user_apps:
                cb = QCheckBox(app)
                cb.setChecked(True)
                self.usr_checkboxes[app] = cb
                self.fp_scroll_layout.addWidget(cb)
                
    def set_updating(self, is_updating):
        self.update_btn.setEnabled(not is_updating)
        if self.zypper_checkbox: self.zypper_checkbox.setEnabled(not is_updating)
        for cb in self.sys_checkboxes.values(): cb.setEnabled(not is_updating)
        for cb in self.usr_checkboxes.values(): cb.setEnabled(not is_updating)
                
    def set_log(self, text):
        self.log_area.setPlainText(text)
        
    def append_log(self, text):
        self.log_area.append(text)

    def refresh_texts(self):
        self.setWindowTitle(get_text("selective_updates"))
        self.fp_info.setText(get_text("selective_updates") + ":")
        self.update_btn.setText(get_text("update_all"))
        self.tabs.setTabText(0, get_text("selective_updates"))
        self.tabs.setTabText(1, get_text("raw_logs"))
        self.log_label.setText(get_text("raw_logs") + ":")

    def _on_update_clicked(self):
        run_zyp = self.zypper_checkbox.isChecked() if self.zypper_checkbox else False
        selected_sys = [app for app, cb in self.sys_checkboxes.items() if cb.isChecked()]
        selected_usr = [app for app, cb in self.usr_checkboxes.items() if cb.isChecked()]
        self.update_selected.emit(run_zyp, selected_sys, selected_usr)
