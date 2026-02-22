import subprocess
import logging
from PySide6.QtCore import QThread, Signal

class UpdateChecker(QThread):
    updates_found = Signal(dict)
    check_finished = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, check_zypper=True, check_flatpak=True, parent=None):
        super().__init__(parent)
        self.check_zypper = check_zypper
        self.check_flatpak = check_flatpak
        self.logger = logging.getLogger("UpdateChecker")
        
    def run(self):
        try:
            results = {
                "zypper_updates": 0,
                "zypper_conflict": False,
                "zypper_output": "",
                "flatpak_system_updates": [],
                "flatpak_user_updates": [],
                "flatpak_output": ""
            }
            
            # 1. Zypper Check
            if self.check_zypper:
                self.logger.info("Running zypper dry-run...")
                # We assume the sudoers rule is installed to allow password-less execution
                zypper_cmd = ["sudo", "-n", "zypper", "--non-interactive", "dup", "--dry-run"]
                process_zypper = subprocess.run(zypper_cmd, capture_output=True, text=True)
                zypper_out = process_zypper.stdout + "\n" + process_zypper.stderr
                results["zypper_output"] = zypper_out
                
                # Check for generic conflicts/problems
                if "Problem:" in zypper_out or "depend" in zypper_out.lower() or process_zypper.returncode != 0:
                    if "Nothing to do" not in zypper_out:
                        self.logger.warning("Zypper conflict or problem detected.")
                        results["zypper_conflict"] = True
                
                # Count updates
                if "Nothing to do." not in zypper_out and "upgraded" in zypper_out:
                    results["zypper_updates"] = 1
                
            if self.check_flatpak:
                # 2. Flatpak Check (System)
                self.logger.info("Running flatpak system check...")
                fp_sys = subprocess.run(["flatpak", "remote-ls", "--updates", "--system", "--columns=app,name"], capture_output=True, text=True)
                results["flatpak_output"] += "System Flatpaks:\n" + fp_sys.stdout + "\n"
                sys_lines = [line.strip() for line in fp_sys.stdout.strip().split('\n') if line.strip() and not line.startswith("Application ID")]
                results["flatpak_system_updates"] = [line.split('\t')[0].split(' ')[0] for line in sys_lines if line] # robust split for app_id
                    
                # 3. Flatpak Check (User)
                self.logger.info("Running flatpak user check...")
                fp_user = subprocess.run(["flatpak", "remote-ls", "--updates", "--user", "--columns=app,name"], capture_output=True, text=True)
                results["flatpak_output"] += "User Flatpaks:\n" + fp_user.stdout + "\n"
                usr_lines = [line.strip() for line in fp_user.stdout.strip().split('\n') if line.strip() and not line.startswith("Application ID")]
                results["flatpak_user_updates"] = [line.split('\t')[0].split(' ')[0] for line in usr_lines if line]
                
            self.updates_found.emit(results)
            
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
            self.error_occurred.emit(str(e))
            
        finally:
            self.check_finished.emit()
