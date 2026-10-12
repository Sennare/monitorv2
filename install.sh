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
# 1. System Dependencies Check & Installation
# ------------------------------------------------------------------------------
echo "==> Controllo dipendenze di sistema (apt)..."
SYS_PACKAGES=(
    "python3" "python3-venv" "python3-pip" "python3-dev" "build-essential"
    "swig" "libgpiod-dev" "i2c-tools" "python3-numpy" "python3-smbus"
    "python3-spidev" "python3-gpiozero" "python3-rpi-lgpio" "python3-lgpio"
    "fonts-dejavu-core"
)
MISSING_PACKAGES=()

for pkg in "${SYS_PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "==> Installazione pacchetti di sistema mancanti: ${MISSING_PACKAGES[*]}..."
    apt-get update
    apt-get install -y "${MISSING_PACKAGES[@]}"
fi

# ------------------------------------------------------------------------------
# 2. Virtual Environment Setup
# ------------------------------------------------------------------------------
VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
    # Clean up incomplete venv if present
    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
    fi

    # Check if a global legacy venv exists (e.g. ~/venv-monitor) as fallback
    if [ -f "$USER_HOME/venv-monitor/bin/python" ]; then
        echo "==> Trovato virtualenv esistente in $USER_HOME/venv-monitor"
        PYTHON_BIN="$USER_HOME/venv-monitor/bin/python"
    else
        echo "==> Creazione virtualenv in $VENV_DIR (con --system-site-packages)..."
        sudo -u "$ACTUAL_USER" python3 -m venv --system-site-packages "$VENV_DIR"
        PYTHON_BIN="$VENV_DIR/bin/python"
        
        echo "==> Aggiornamento pip & installazione dipendenze da requirements.txt..."
        if [ -f "$PROJECT_DIR/requirements.txt" ]; then
            sudo -u "$ACTUAL_USER" "$PYTHON_BIN" -m pip install --upgrade pip
            sudo -u "$ACTUAL_USER" "$PYTHON_BIN" -m pip install -r "$PROJECT_DIR/requirements.txt"
        fi
    fi
else
    echo "==> Trovato virtualenv esistente in $VENV_DIR"
    PYTHON_BIN="$VENV_DIR/bin/python"
fi

echo "  - Python binario utilizzato: $PYTHON_BIN"

# ------------------------------------------------------------------------------
# 3. Generate and Install Systemd Services
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
# 4. Enable and Start Services
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
