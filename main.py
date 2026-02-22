import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QTimer

from ui.main_window import MainWindow
from ui.wizard_window import WizardWindow
from update_checker import UpdateChecker
from updater_runner import UpdaterRunner

logging.basicConfig(level=logging.INFO)

class UpdateApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # We don't want the app to close if the main window is closed (keeps tray running)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Load asset paths
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
        self.icon_green = QIcon(os.path.join(self.assets_dir, "tray_green.svg"))
        self.icon_yellow = QIcon(os.path.join(self.assets_dir, "tray_yellow.svg"))
        self.icon_red = QIcon(os.path.join(self.assets_dir, "tray_red.svg"))
        
        self.main_window = MainWindow(self.icon_green)
        
        # Tray setup
        self.tray = QSystemTrayIcon(self.icon_green, self.app)
        self.tray_menu = QMenu()
        
        self.action_show = self.tray_menu.addAction("Show Status")
        self.action_show.triggered.connect(self.main_window.show)
        
        self.action_check = self.tray_menu.addAction("Check for Updates")
        self.action_check.triggered.connect(self.start_check)
        
        self.action_quit = self.tray_menu.addAction("Quit")
        self.action_quit.triggered.connect(self.app.quit)
        
        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()
        
        self.tray.activated.connect(self.tray_activated)
        
        # Connect update buttons
        self.main_window.update_btn.clicked.connect(self.run_updates)
        self.main_window.advanced_window.update_selected.connect(self.run_custom_updates)

        
        # Check rule installation on startup by actually testing the command
        # This is because regular users don't have permission to ls or read /etc/sudoers.d/
        import subprocess
        try:
            test_cmd = ["sudo", "-n", "zypper", "--non-interactive", "dup", "--dry-run"]
            test_proc = subprocess.run(test_cmd, capture_output=True, text=True)
            if test_proc.returncode == 0:
                self.setup_complete()
            else:
                self.run_wizard()
        except FileNotFoundError:
            self.run_wizard()
            
    def run_wizard(self):
        logging.info("Polkit rule not found. Showing wizard.")
        self.wizard = WizardWindow()
        self.wizard.setup_complete.connect(self.setup_complete)
        self.wizard.setup_skipped.connect(self.setup_skipped)
        self.wizard.show()
        
    def setup_complete(self):
        logging.info("Polkit rule is installed. Enabling automatic background checks.")
        # Start automatic checks
        self.start_check()
        self.timer = QTimer()
        self.timer.timeout.connect(self.start_check)
        self.timer.start(14400000) # Every 4 hours
        
    def setup_skipped(self):
        logging.info("Wizard skipped. Checks will remain manual.")
        self.main_window.set_status("up_to_date")
        self._update_tray_icon("green")
        # No timer started!

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
                
    def start_check(self):
        self.main_window.set_status("checking")
        self.checker = UpdateChecker()
        self.checker.updates_found.connect(self.process_check_results)
        self.checker.start()
        
    def process_check_results(self, results):
        has_zypper_updates = results.get("zypper_updates", 0) > 0
        sys_flatpaks = results.get("flatpak_system_updates", [])
        usr_flatpaks = results.get("flatpak_user_updates", [])
        has_flatpak_updates = len(sys_flatpaks) > 0 or len(usr_flatpaks) > 0
        has_conflict = results.get("zypper_conflict", False)
        
        # Populate UI checkboxes
        self.main_window.advanced_window.populate_updates(has_zypper_updates, sys_flatpaks, usr_flatpaks)
        
        if has_conflict:
            self.main_window.set_status("conflicts", updates_data=results)
            self._update_tray_icon("red")
            self.tray.showMessage("Update Issue", "Vendor conflict detected. Suggest waiting!", QSystemTrayIcon.Warning)
        elif has_zypper_updates or has_flatpak_updates:
            self.main_window.set_status("updates_ready", updates_data=results)
            self._update_tray_icon("yellow")
            self.tray.showMessage("Updates Available", "Click to review and apply updates.", QSystemTrayIcon.Information)
        else:
            self.main_window.set_status("up_to_date")
            self._update_tray_icon("green")
            
        self.last_results = results

    def _update_tray_icon(self, color):
        if color == "red":
            self.tray.setIcon(self.icon_red)
        elif color == "yellow":
            self.tray.setIcon(self.icon_yellow)
        else:
            self.tray.setIcon(self.icon_green)
        
    def run_updates(self):
        self.main_window.set_status("updating")
        
        run_zyp = self.last_results.get("zypper_updates", 0) > 0
        sys_apps = self.last_results.get("flatpak_system_updates", [])
        usr_apps = self.last_results.get("flatpak_user_updates", [])
        
        self.runner = UpdaterRunner(run_zyp, sys_apps, usr_apps)
        self.runner.update_progress.connect(self.main_window.advanced_window.append_log)
        self.runner.update_finished.connect(self.on_update_finished)
        self.runner.start()
        
    def run_custom_updates(self, run_zyp, sys_apps, usr_apps):
        self.main_window.set_status("updating")
        self.main_window.advanced_window.append_log(f"\n--- RUNNING SELECTIVE UPDATES ---\n")
        
        # Run specific selections
        self.runner = UpdaterRunner(run_zypper=run_zyp, flatpak_system_apps=sys_apps, flatpak_user_apps=usr_apps)
        self.runner.update_progress.connect(self.main_window.advanced_window.append_log)
        self.runner.update_finished.connect(self.on_update_finished)
        self.runner.start()
        
    def on_update_finished(self, success, logs):
        if success:
            self.main_window.advanced_window.append_log("\n--- UPDATES COMPLETED SUCCESSFULLY ---")
            # Re-check to ensure we are up to date
            self.start_check()
        else:
            self.main_window.advanced_window.append_log("\n--- ERRORS OCCURRED DURING UPDATE ---")
            self.main_window.set_status("checking") # Temp reset
            self.main_window.status_label.setText("Update Failed.")
            self.main_window.status_icon.setText("❌")
            self.main_window.details_label.setText("Check Advanced log.")
            self.main_window.progress_bar.hide()
        
    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = UpdateApp()
    app.run()
