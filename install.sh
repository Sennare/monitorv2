#!/usr/bin/env bash
set -e

# ==============================================================================
# Remote Monitor - Installer script for systemd services & environment
# ==============================================================================

# Ensure script is run with root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Errore: Esegui questo script con sudo:"
    echo "  sudo ./install.sh"
    exit 1
fi

# Detect actual non-root user who invoked sudo
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    # If logged in directly as root, try finding the owner of the project directory
    ACTUAL_USER=$(stat -c '%U' "$(dirname "$0")")
fi

USER_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

echo "==> Configurazione Remote Monitor"
echo "  - Cartella progetto: $PROJECT_DIR"
echo "  - Utente di esecuzione: $ACTUAL_USER (Home: $USER_HOME)"

# ------------------------------------------------------------------------------
# 1. Virtual Environment Setup
# ------------------------------------------------------------------------------
# Check if a python virtual environment already exists in the project or specify custom path
VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    # Check if a global legacy venv exists (e.g. ~/venv-monitor) as a fallback
    if [ -f "$USER_HOME/venv-monitor/bin/python" ]; then
        echo "==> Trovato virtualenv esistente in $USER_HOME/venv-monitor"
        PYTHON_BIN="$USER_HOME/venv-monitor/bin/python"
    else
        echo "==> Creazione virtualenv in $VENV_DIR..."
        sudo -u "$ACTUAL_USER" python3 -m venv "$VENV_DIR"
        PYTHON_BIN="$VENV_DIR/bin/python"
        
        echo "==> Installazione dipendenze da requirements.txt..."
        if [ -f "$PROJECT_DIR/requirements.txt" ]; then
            sudo -u "$ACTUAL_USER" "$PYTHON_BIN" -m pip install --upgrade pip
            sudo -u "$ACTUAL_USER" "$PYTHON_BIN" -m pip install -r "$PROJECT_DIR/requirements.txt"
        fi
    fi
else
    echo "==> Trovato virtualenv in $VENV_DIR"
    PYTHON_BIN="$VENV_DIR/bin/python"
fi

echo "  - Python binario utilizzato: $PYTHON_BIN"

# ------------------------------------------------------------------------------
# 2. Generate and Install Systemd Services
# ------------------------------------------------------------------------------
TEMPLATE_DIR="$PROJECT_DIR/scripts/services"
TARGET_DIR="/etc/systemd/system"

echo "==> Generazione file di servizio systemd..."

generate_service() {
    local template="$1"
    local output="$2"

    sed \
        -e "s|{{USER}}|$ACTUAL_USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        -e "s|{{PYTHON_BIN}}|$PYTHON_BIN|g" \
        "$template" > "$output"

    chmod 644 "$output"
}

generate_service "$TEMPLATE_DIR/monitor.service.template" "$TARGET_DIR/monitor.service"
echo "  - Installato: $TARGET_DIR/monitor.service"

generate_service "$TEMPLATE_DIR/dashboard.service.template" "$TARGET_DIR/dashboard.service"
echo "  - Installato: $TARGET_DIR/dashboard.service"

# ------------------------------------------------------------------------------
# 3. Enable and Start Services
# ------------------------------------------------------------------------------
echo "==> Ricarica configurazione systemd e avvio servizi..."
systemctl daemon-reload

systemctl enable monitor.service
systemctl enable dashboard.service

echo "==> Avvio servizi..."
systemctl restart monitor.service
systemctl restart dashboard.service

echo ""
echo "=============================================================================="
echo "  Installazione completata con successo!"
echo "  I servizi 'monitor.service' e 'dashboard.service' sono attivi e si avvieranno"
echo "  automaticamente ad ogni accensione del Raspberry Pi."
echo ""
echo "  Comandi utili:"
echo "    - Stato monitor:    sudo systemctl status monitor.service"
echo "    - Stato dashboard:  sudo systemctl status dashboard.service"
echo "    - Log monitor:      sudo journalctl -u monitor.service -f"
echo "    - Log dashboard:    sudo journalctl -u dashboard.service -f"
echo "    - Disinstallazione: sudo ./uninstall.sh"
echo "=============================================================================="
