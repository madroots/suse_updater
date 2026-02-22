#!/bin/bash
SUDOERS_FILE="/etc/sudoers.d/suse-updater"
echo "ALL ALL=(root) NOPASSWD: /usr/bin/zypper --non-interactive dup --dry-run" > "$SUDOERS_FILE"
chmod 440 "$SUDOERS_FILE"
