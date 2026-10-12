# Remote Monitor

Sistema di monitoraggio ambientale e companion robotico per Raspberry Pi con sensori AHT10/AHT20, display OLED SSD1306 e LCD TFT ILI9341, pulsante rotativo e web dashboard FastAPI.

Per l'architettura completa del sistema, consultare [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Installazione Rapida dei Servizi Systemd

Il progetto è predisposto per essere installato in qualsiasi cartella e su qualsiasi utente del Raspberry Pi senza dover modificare manualmente i percorsi o i file di configurazione.

### 1. Requisiti di Sistema (Raspberry Pi OS / Debian)
Assicurarsi che Python 3 e venv siano installati:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 2. Installazione ed Avvio Automatico
Entra nella cartella del progetto ed esegui lo script di installazione:
```bash
cd /percorso/del/tuo/remote-monitor
sudo ./install.sh
```

Lo script si occuperà automaticamente di:
1. Rilevare l'utente corrente e la cartella del progetto.
2. Rilevare o creare un virtual environment `.venv` locale e installare le dipendenze da `requirements.txt`.
3. Compilare i file di servizio con i percorsi corretti e installarli in `/etc/systemd/system/`.
4. Ricaricare systemd e abilitare l'avvio automatico al boot per:
   - `monitor.service` (l'applicazione principale di sensori e display)
   - `dashboard.service` (la web dashboard FastAPI sulla porta 8000)
5. Avviare immediatamente entrambi i servizi.

---

## Gestione dei Servizi

### Verifica dello Stato
```bash
sudo systemctl status monitor.service
sudo systemctl status dashboard.service
```

### Lettura dei Log in Tempo Reale
```bash
sudo journalctl -u monitor.service -f
sudo journalctl -u dashboard.service -f
```

### Riavvio o Arresto
```bash
sudo systemctl restart monitor.service
sudo systemctl restart dashboard.service
```

---

## Disinstallazione

Per fermare e rimuovere completamente i servizi:
```bash
sudo ./uninstall.sh
```
