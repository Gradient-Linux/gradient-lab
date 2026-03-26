#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESTDIR="${1:-/}"
ETC_DIR="${DESTDIR%/}/etc/gradient"
SERVICE_DIR="${DESTDIR%/}/etc/systemd/system"

install -d -m 0755 "$ETC_DIR" "$SERVICE_DIR"
install -m 0644 "$ROOT_DIR/jupyterhub_config.py" "$ETC_DIR/jupyterhub_config.py"
install -m 0644 "$ROOT_DIR/jupyter_server_config.py" "$ETC_DIR/jupyter_server_config.py"
install -m 0644 "$ROOT_DIR/scripts/gradient-lab.service" "$SERVICE_DIR/gradient-lab.service"

if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install -e "$ROOT_DIR"
fi

cat <<EOF
Installed gradient-lab configuration to:
  $ETC_DIR/jupyterhub_config.py
  $ETC_DIR/jupyter_server_config.py
  $SERVICE_DIR/gradient-lab.service
EOF
