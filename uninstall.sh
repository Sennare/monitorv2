#!/usr/bin/env bash
set -e

# ==============================================================================
# Remote Monitor - Uninstaller script for systemd services
# ==============================================================================

if [ "$EUID" -ne 0 ]; then
    echo "Errore: Esegui questo script con sudo:"
    echo "  sudo ./uninstall.sh"
    exit 1
fi

echo "==> Arresto e disabilitazione servizi..."
systemctl stop monitor.service 2>/dev/null || true
systemctl stop dashboard.service 2>/dev/null || true

systemctl disable monitor.service 2>/dev/null || true
systemctl disable dashboard.service 2>/dev/null || true

echo "==> Rimozione file di servizio da /etc/systemd/system/..."
rm -f /etc/systemd/system/monitor.service
rm -f /etc/systemd/system/dashboard.service

systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true

echo "=============================================================================="
echo "  Disinstallazione completata con successo."
echo "  I servizi 'monitor.service' e 'dashboard.service' sono stati rimossi."
echo "=============================================================================="
