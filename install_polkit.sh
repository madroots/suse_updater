#!/bin/bash
RULES_FILE="/etc/polkit-1/rules.d/99-suse-updater.rules"
cat << 'RULE_EOF' > "$RULES_FILE"
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.policykit.exec") {
        var cmd = action.lookup("program");
        var args = action.lookup("command_line");
        if (cmd == "/usr/bin/zypper" && args != null && args.indexOf("dup --dry-run") != -1) {
            return polkit.Result.YES;
        }
    }
});
RULE_EOF
chmod 644 "$RULES_FILE"

# Restart polkit to ensure rules are flushed and re-read immediately!
systemctl restart polkit.service
