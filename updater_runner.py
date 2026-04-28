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
            from PySide6.QtCore import QSettings
            settings = QSettings("SuseUpdater", "OpenSUSE_Tool")
            passwordless = settings.value("passwordless_updates", False, type=bool)

            if not passwordless:
                # We build a single script to execute all root commands so it prompts for password only once
                script = "set -e\n"
                if self.run_zypper:
                    script += "echo '___REF___'\n"
                    script += "zypper --non-interactive ref\n"
                    script += "echo '___DUP___'\n"
                    script += "zypper --non-interactive dup\n"
                if self.flatpak_system_apps:
                    apps = " ".join(self.flatpak_system_apps)
                    script += "echo '___FLATPAK___'\n"
                    script += f"flatpak update -y --system {apps}\n"
                    
                if self.run_zypper or self.flatpak_system_apps:
                    self.update_progress.emit("Requesting privileges and starting system updates...")
                    cmd = ["pkexec", "sh", "-c", script]
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in iter(proc.stdout.readline, ''):
                        if line:
                            clean_line = line.strip()
                            if clean_line == "___REF___":
                                self.update_progress.emit("Refreshing repositories (zypper ref)...")
                            elif clean_line == "___DUP___":
                                self.update_progress.emit("Running zypper dup (system upgrade)...")
                            elif clean_line == "___FLATPAK___":
                                self.update_progress.emit(f"Updating {len(self.flatpak_system_apps)} system flatpaks...")
                            else:
                                full_log += line
                                self.update_progress.emit(f"System: {clean_line}")
                    proc.wait()
                    if proc.returncode != 0:
                        success = False
                        full_log += f"\nSystem update failed with return code {proc.returncode}\n"
            else:
                # Passwordless: we use sudo -n for each command separately
                if self.run_zypper:
                    self.update_progress.emit("Refreshing repositories (zypper ref)...")
                    ref_cmd = ["sudo", "-n", "zypper", "--non-interactive", "ref"]
                    ref_proc = subprocess.Popen(ref_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in iter(ref_proc.stdout.readline, ''):
                        if line:
                            full_log += line
                            self.update_progress.emit(f"Zypper Ref: {line.strip()}")
                    ref_proc.wait()
                    if ref_proc.returncode != 0: success = False
                    
                    self.update_progress.emit("Running zypper dup (system upgrade)...")
                    dup_cmd = ["sudo", "-n", "zypper", "--non-interactive", "dup"]
                    dup_proc = subprocess.Popen(dup_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in iter(dup_proc.stdout.readline, ''):
                        if line:
                            full_log += line
                            self.update_progress.emit(f"Zypper Dup: {line.strip()}")
                    dup_proc.wait()
                    if dup_proc.returncode != 0: success = False
                
                if self.flatpak_system_apps:
                    self.update_progress.emit(f"Updating {len(self.flatpak_system_apps)} system flatpaks...")
                    fp_cmd = ["sudo", "-n", "flatpak", "update", "-y", "--system"] + self.flatpak_system_apps
                    fp_proc = subprocess.Popen(fp_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in iter(fp_proc.stdout.readline, ''):
                        if line:
                            full_log += line
                            self.update_progress.emit(f"Flatpak (System): {line.strip()}")
                    fp_proc.wait()
                    if fp_proc.returncode != 0: success = False

            # User flatpaks always run separately without root
            if self.flatpak_user_apps:
                self.update_progress.emit(f"Updating {len(self.flatpak_user_apps)} user flatpaks...")
                usr_cmd = ["flatpak", "update", "-y", "--user"] + self.flatpak_user_apps
                usr_proc = subprocess.Popen(usr_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in iter(usr_proc.stdout.readline, ''):
                    if line:
                        full_log += line
                        self.update_progress.emit(f"Flatpak (User): {line.strip()}")
                usr_proc.wait()
                if usr_proc.returncode != 0:
                    success = False

        except Exception as e:
            self.logger.error(f"Error during update execution: {e}")
            full_log += f"\nException: {e}"
            success = False
            
        self.update_progress.emit("Done.")
        self.update_finished.emit(success, full_log)
