import subprocess
import logging
from PySide6.QtCore import QThread, Signal

class UpdaterRunner(QThread):
    update_progress = Signal(str)
    update_finished = Signal(bool, str) # success, log_output
    
    def __init__(self, run_zypper=True, flatpak_system_apps=[], flatpak_user_apps=[], parent=None):
        super().__init__(parent)
        self.run_zypper = run_zypper
        self.flatpak_system_apps = flatpak_system_apps
        self.flatpak_user_apps = flatpak_user_apps
        self.logger = logging.getLogger("UpdaterRunner")
        
    def run(self):
        full_log = ""
        success = True
        
        try:
            if self.run_zypper:
                self.update_progress.emit("Running zypper dup (requires root password)...")
                # Need to use pkexec for standard privilege escalation in GUI
                cmd = ["pkexec", "zypper", "--non-interactive", "dup"]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        full_log += line
                        self.update_progress.emit(f"Zypper: {line.strip()}")
                        
                proc.wait()
                if proc.returncode != 0:
                    success = False
                    full_log += f"\nZypper failed with return code {proc.returncode}\n"
            
            if self.flatpak_system_apps:
                self.update_progress.emit(f"Updating {len(self.flatpak_system_apps)} system flatpaks...")
                cmd = ["pkexec", "flatpak", "update", "-y", "--system"] + self.flatpak_system_apps
                # System flatpak requires polkit authentication correctly bypassed by flatpak normally, but via subprocess stdout piping, it often fails (Error: Deploy not allowed for user). So we use pkexec.
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        full_log += line
                        self.update_progress.emit(f"Flatpak (System): {line.strip()}")
                proc.wait()
                if proc.returncode != 0:
                    success = False
            
            if self.flatpak_user_apps:
                self.update_progress.emit(f"Updating {len(self.flatpak_user_apps)} user flatpaks...")
                cmd = ["flatpak", "update", "-y", "--user"] + self.flatpak_user_apps
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        full_log += line
                        self.update_progress.emit(f"Flatpak (User): {line.strip()}")
                proc.wait()
                if proc.returncode != 0:
                    success = False

        except Exception as e:
            self.logger.error(f"Error during update execution: {e}")
            full_log += f"\nException: {e}"
            success = False
            
        self.update_progress.emit("Done.")
        self.update_finished.emit(success, full_log)
