import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QSystemTrayIcon
)
from PySide6.QtCore import Qt, QSize, QSettings, QPropertyAnimation, Property, QRect, QRectF
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from .advanced_window import AdvancedWindow
from i18n import get_text

class RotatingLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._angle = 0
        self.setFixedSize(120, 120) # Increased fixed size to prevent clipping
        self.animation = QPropertyAnimation(self, b"angle")
        self.animation.setDuration(2000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.setLoopCount(-1) # Infinite
        self.renderer = None
        self.mode = "standard" # "standard" (emoji) or "svg" (animated gear)

    @Property(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    def set_svg(self, svg_path):
        self.renderer = QSvgRenderer(svg_path)
        self.mode = "svg"
        self.setText("")
        self.setPixmap(QPixmap())
        self.update()

    def set_emoji(self, emoji):
        self.mode = "standard"
        self.setText(emoji)
        self.setPixmap(QPixmap())
        self.setStyleSheet("") # Clear any SVG specific styles or old font sizes
        self.stop_rotation()
        self.update()

    def start_rotation(self):
        if self.animation.state() != QPropertyAnimation.Running:
            self.animation.start()

    def stop_rotation(self):
        self.animation.stop()
        self._angle = 0
        self.update()

    def paintEvent(self, event):
        if self.mode == "svg" and self.renderer and self.renderer.isValid():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            # Center the gear within the 120x120 widget
            painter.translate(self.width() / 2, self.height() / 2)
            painter.rotate(self._angle)
            self.renderer.render(painter, QRectF(-45, -45, 90, 90))
            painter.end()
        else:
            # Let QLabel handle emoji/standard text naturally
            super().paintEvent(event)

class MainWindow(QMainWindow):
    def __init__(self, check_icon, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{get_text('title')} v0.1.6")
        self.setMinimumSize(500, 450) # Increased min height and allowed growth
        
        # Save a reference to the main app's icon for checking state
        self.check_icon = check_icon
        self.setWindowIcon(self.check_icon)
        
        # Central Widget & Layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Settings Gear (Absolute Positioned Overlay)
        self.settings_btn = QPushButton(self.central_widget)
        self.settings_btn.setFixedSize(32, 32)
        gear_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "settings_gear.svg")
        if os.path.exists(gear_path):
            self.settings_btn.setIcon(QIcon(gear_path))
            self.settings_btn.setIconSize(QSize(24, 24))
        self.settings_btn.setStyleSheet("background: transparent; border: none;")
        self.settings_btn.raise_()
        
        # --- Main Content Area (Perfect Centering) ---
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(40, 20, 40, 20)
        self.content_layout.setAlignment(Qt.AlignCenter)
        self.content_layout.setSpacing(20)
        
        self.layout.addStretch()
        self.layout.addWidget(self.content_container, alignment=Qt.AlignCenter)
        self.layout.addStretch()

        # Main Status Icon (placeholder text/icon)
        self.status_icon = RotatingLabel()
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.status_icon, alignment=Qt.AlignCenter)
        
        # Main Status Text
        self.status_label = QLabel(get_text("checking"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.status_label.setWordWrap(True)
        self.content_layout.addWidget(self.status_label)
        
        # Sub Status Text (e.g. details about updates)
        self.details_label = QLabel(get_text("wait_query"))
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("color: #ccc; font-size: 13px;")
        self.details_label.setWordWrap(True)
        self.details_label.setMinimumHeight(80) # Increased min height for wrap safety
        self.content_layout.addWidget(self.details_label)
        
        # Check for Updates Link (clickable text)
        self.refresh_link = QLabel()
        self.refresh_link.setAlignment(Qt.AlignCenter)
        self.refresh_link.setStyleSheet("color: #3498db; text-decoration: underline; font-size: 12px;")
        self.refresh_link.setCursor(Qt.PointingHandCursor)
        self.refresh_link.mousePressEvent = self._on_refresh_link_clicked
        self.content_layout.addWidget(self.refresh_link)
        
        # Update Button
        self.update_btn = QPushButton(get_text("update_all"))
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
        self.content_layout.addWidget(self.update_btn, alignment=Qt.AlignCenter)
        
        # Advanced Button (Initially hidden, shows conditionally)
        self.adv_btn = QPushButton(get_text("advanced"))
        self.adv_btn.setFixedSize(220, 30)
        self.adv_btn.setStyleSheet("color: #aaa; background: transparent; border: none; text-decoration: underline;")
        self.adv_btn.hide()
        self.content_layout.addWidget(self.adv_btn, alignment=Qt.AlignCenter)
        
        # Logs Button (Initially hidden, shows only during update)
        self.logs_btn = QPushButton(get_text("real_time_logs"))
        self.logs_btn.setFixedSize(180, 30)
        self.logs_btn.setStyleSheet("color: #3498db; background: transparent; border: none; text-decoration: underline; font-weight: bold;")
        self.logs_btn.hide()
        self.content_layout.addWidget(self.logs_btn, alignment=Qt.AlignCenter)
        
        # Progress Bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) 
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.hide()
        self.content_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        # Connect Windows
        self.advanced_window = AdvancedWindow()
        self.adv_btn.clicked.connect(self.show_advanced)
        self.logs_btn.clicked.connect(self.show_logs)
        
        # Apply Dark Theme palette base
        self._apply_dark_theme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep settings gear in top-right corner regardless of resizing
        self.settings_btn.move(self.width() - 42, 10)

    def _apply_dark_theme(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)
        
    def show_advanced(self):
        self.advanced_window.tabs.setCurrentIndex(0) # Select first tab
        self.advanced_window.show()
        
    def show_logs(self):
        self.advanced_window.tabs.setCurrentIndex(1) # Go directly to logs tab
        self.advanced_window.show()
        
    def _on_refresh_link_clicked(self, event):
        # We'll emit a signal or just call a method if we have a reference to the app
        # For simplicity, we can assume the parent or a global app object exists, 
        # but better to have a signal.
        if hasattr(self, 'refresh_requested_callback'):
            self.refresh_requested_callback()

    def _set_large_icon(self, emoji=""):
        self.status_icon.set_emoji(emoji)
        font = self.status_icon.font()
        font.setPixelSize(64)
        self.status_icon.setFont(font)

    def refresh_texts(self):
        self.setWindowTitle(f"{get_text('title')} v0.1.6")
        self.update_btn.setText(get_text("update_all"))
        self.adv_btn.setText(get_text("advanced"))
        self.logs_btn.setText(get_text("real_time_logs"))
        
        # Force refresh status if it's already set
        if hasattr(self, 'current_state'):
            self.set_status(self.current_state, updates_data=getattr(self, 'last_updates_data', None))

        self.advanced_window.refresh_texts()

    def set_status(self, state, details="", updates_data=None):
        self.current_state = state
        self.last_updates_data = updates_data
        
        if state == "checking":
            gear_svg = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "settings_gear.svg")
            self.status_icon.set_svg(gear_svg)
            self.status_icon.start_rotation()
            self.status_label.setText(get_text("checking"))
            self.status_label.setStyleSheet("color: white;")
            self.details_label.setText(get_text("wait_query"))
            self.update_btn.hide()
            self.adv_btn.hide()
            self.logs_btn.hide()
            self.progress_bar.hide()
            self.refresh_link.hide() # Hide link when clicked
            self.advanced_window.set_updating(True)
            
        elif state == "up_to_date":
            self.status_icon.stop_rotation()
            self._set_large_icon(emoji="🎉")
            self.status_label.setText(get_text("up_to_date"))
            self.status_label.setStyleSheet("color: #00C853;")
            
            settings = QSettings("SuseUpdater", "OpenSUSE_Tool")
            check_zyp = settings.value("check_zypper", True, type=bool)
            check_fp = settings.value("check_flatpak", True, type=bool)

            lines = []
            if check_zyp:
                lines.append(get_text("zypper_uptodate"))
            if check_fp:
                lines.append(get_text("flatpak_uptodate"))

            self.details_label.setText("<br>".join(lines))
            self.update_btn.hide()
            self.adv_btn.hide()
            self.logs_btn.hide()
            self.progress_bar.hide()
            self.refresh_link.setText(get_text("check_updates_link"))
            self.refresh_link.show()
            self.advanced_window.set_updating(False)
            
        elif state == "updates_ready":
            self.status_icon.stop_rotation()
            self._set_large_icon(emoji="📦")
            self.status_label.setText(get_text("updates_available_title"))
            self.status_label.setStyleSheet("color: #FFD740;")
            
            settings = QSettings("SuseUpdater", "OpenSUSE_Tool")
            check_zyp = settings.value("check_zypper", True, type=bool)
            check_fp = settings.value("check_flatpak", True, type=bool)

            z_up = (updates_data.get('zypper_updates', 0) > 0) if check_zyp else False
            fs_up_list = updates_data.get('flatpak_system_updates', []) if check_fp else []
            fu_up_list = updates_data.get('flatpak_user_updates', []) if check_fp else []
            has_flatpak_updates = (len(fs_up_list) + len(fu_up_list)) > 0
            
            z_text = get_text("zypper_updates") if z_up else get_text("zypper_uptodate")
            f_text = get_text("flatpak_updates") if has_flatpak_updates else get_text("flatpak_uptodate")
            
            lines = []
            if check_zyp:
                lines.append(z_text)
            if check_fp:
                lines.append(f_text)
                       
            self.details_label.setText("<br>".join(lines))
            self.update_btn.show()
            self.adv_btn.setVisible(has_flatpak_updates) # Only show if flatpaks have updates
            self.logs_btn.hide()
            self.refresh_link.hide()
            self.update_btn.setText(get_text("update_all"))
            self.update_btn.setEnabled(True)
            self.progress_bar.hide()
            self.advanced_window.set_updating(False)
            
        elif state == "conflicts":
            self.status_icon.stop_rotation()
            self._set_large_icon(emoji="⚠️")
            self.status_label.setText(get_text("conflicts_title"))
            self.status_label.setStyleSheet("color: #FFD740;")
            
            settings = QSettings("SuseUpdater", "OpenSUSE_Tool")
            check_zyp = settings.value("check_zypper", True, type=bool)
            check_fp = settings.value("check_flatpak", True, type=bool)

            z_up = "---" if check_zyp else get_text("zypper_uptodate")
            fs_up_list = updates_data.get('flatpak_system_updates', []) if check_fp else []
            fu_up_list = updates_data.get('flatpak_user_updates', []) if check_fp else []
            has_flatpak_updates = (len(fs_up_list) + len(fu_up_list)) > 0
            f_text = get_text("flatpak_updates") if has_flatpak_updates else get_text("flatpak_uptodate")

            lines = []
            if check_zyp:
                lines.append(f"<b>{get_text('os_update_zypper')}:</b> {z_up}")
            if check_fp:
                lines.append(f"<b>{get_text('apps_flatpaks')}:</b> {f_text}")

            self.details_label.setText(
                "<br>".join(lines) + "<br><br>" +
                get_text("conflicts_desc")
            )
            # Hide the big button so they don't force Zypper
            self.update_btn.hide()
            self.adv_btn.setVisible(has_flatpak_updates) 
            self.logs_btn.hide()
            self.progress_bar.hide()
            self.refresh_link.setText(get_text("check_updates_link"))
            self.refresh_link.show()
            self.advanced_window.set_updating(False)
            
        elif state == "updating":
            gear_svg = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "settings_gear.svg")
            self.status_icon.set_svg(gear_svg)
            self.status_icon.start_rotation()
            self.status_label.setText(get_text("updating_title"))
            self.status_label.setStyleSheet("color: white;")
            self.details_label.setText(get_text("applying_changes"))
            self.update_btn.setEnabled(False)
            self.adv_btn.hide()
            self.logs_btn.show()
            self.progress_bar.show()
            self.advanced_window.set_updating(True)

        # Update the advanced window raw logs just in case they open it
        if updates_data:
            combined_log = updates_data.get('zypper_output', '') + "\n" + updates_data.get('flatpak_output', '')
            self.advanced_window.set_log(combined_log)
