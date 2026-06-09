import smbus2
import time
import threading

class Lcd:
    """Gestione LCD 20x4 via I2C ottimizzata e non bloccante."""
    
    LCD_ADDR = 0x27
    LCD_WIDTH = 20
    LCD_HEIGHT = 4
    
    # Comandi LCD
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80
    
    # Flag
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_DISPLAYON = 0x04
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00
    
    LCD_LINE_ADDRESSES = [0x00, 0x40, 0x14, 0x54]
    
    def __init__(self, i2c_addr=LCD_ADDR, bus=1):
        self.bus = smbus2.SMBus(bus)
        self.addr = i2c_addr
        self.backlight = True
        self.display_on = True
        
        # Cache per evitare di riscrivere caratteri identici (ottimizzazione fondamentale)
        self._current_lines = [" " * self.LCD_WIDTH] * self.LCD_HEIGHT
        self._target_lines = [" " * self.LCD_WIDTH] * self.LCD_HEIGHT
        
        # Threading e sincronizzazione
        self._lock = threading.Lock()
        self._update_event = threading.Event()
        
        # Inizializzazione hardware (sincrona, avviene solo all'avvio)
        self._init()
        
        # Avvio del thread asincrono per la gestione dei testi
        self._worker_thread = threading.Thread(target=self._render_loop, daemon=True)
        self._worker_thread.start()
        
    def _send(self, data, mode=0):
        """Invia un byte riducendo al minimo i delay (gestiti dal bus I2C)."""
        backlight_bit = self.LCD_BACKLIGHT if self.backlight else 0
        
        # Bit alto / nibble alto
        high_nib = mode | (data & 0xF0) | backlight_bit
        self.bus.write_byte(self.addr, high_nib)
        self.bus.write_byte(self.addr, high_nib | 0x04)  # Enable HIGH
        self.bus.write_byte(self.addr, high_nib)         # Enable LOW
        
        # Bit basso / nibble basso
        low_nib = mode | ((data & 0x0F) << 4) | backlight_bit
        self.bus.write_byte(self.addr, low_nib)
        self.bus.write_byte(self.addr, low_nib | 0x04)   # Enable HIGH
        self.bus.write_byte(self.addr, low_nib)          # Enable LOW
        
        # Piccolo delay di sicurezza per l'esecuzione del comando interno dell'LCD
        time.sleep(0.00005) # 50 microsecondi (invece di 6 millisecondi!)

    def _init(self):
        """Sequenza di boot obbligatoria (eseguita una volta sola)."""
        time.sleep(0.1)
        self._send(0x33, 0)
        time.sleep(0.005)
        self._send(0x33, 0)
        time.sleep(0.001)
        self._send(0x32, 0)
        time.sleep(0.001)
        
        self._send(0x28, 0) # 4-bit, 2 linee
        self._send(0x0C, 0) # Display ON, Cursor OFF
        self._send(0x06, 0) # Entry mode increment
        self._send(0x01, 0) # Clear hardware iniziale
        time.sleep(0.003)

    def _set_cursor_immediate(self, col, row):
        address = self.LCD_LINE_ADDRESSES[row] + col
        self._send(0x80 | address, 0)

    def _render_loop(self):
        """Loop del thread in background: scrive sul display solo quando serve."""
        while True:
            self._update_event.wait()
            self._update_event.clear()
            
            # Copia locale dei dati per minimizzare il tempo di Lock
            with self._lock:
                lines_to_process = list(self._target_lines)
                
            if not self.display_on:
                continue

            for row in range(self.LCD_HEIGHT):
                target_text = lines_to_process[row]
                
                # Se la riga attuale è già uguale a quella da scrivere, saltala!
                if target_text == self._current_lines[row]:
                    continue
                
                # Scrittura della riga modificata
                self._set_cursor_immediate(0, row)
                for char in target_text:
                    self._send(ord(char), 1)
                
                # Aggiorna la cache
                self._current_lines[row] = target_text

    # -------------------------------------------------------------------------
    # API PUBBLICHE (Chiamate dal thread principale - Istantanee e Non-Bloccanti)
    # -------------------------------------------------------------------------

    def write_text(self, text, row=0):
        """Aggiorna in modo asincrono una singola riga (0-3)."""
        if row < 0 or row >= self.LCD_HEIGHT:
            return
        
        # Pulisce e formatta la stringa a 20 caratteri fissi
        formatted_text = text.ljust(self.LCD_WIDTH)[:self.LCD_WIDTH]
        
        with self._lock:
            self._target_lines[row] = formatted_text
        self._update_event.set()

    def write(self, line1="", line2="", line3="", line4=""):
        """Aggiorna in modo asincrono l'intero schermo (4 righe)."""
        lines = [line1, line2, line3, line4]
        
        with self._lock:
            for i, line in enumerate(lines):
                self._target_lines[i] = line.ljust(self.LCD_WIDTH)[:self.LCD_WIDTH]
                
        self._update_event.set()

    def clear(self):
        """Svuota lo schermo in modo intelligente (senza sfarfallio)."""
        self.write("", "", "", "")

    def set_backlight(self, state):
        """Accende o spegne la retroilluminazione istantaneamente."""
        self.backlight = state
        with self._lock:
            # Forza il refresh impostando la cache a stringhe vuote
            self._current_lines = [""] * self.LCD_HEIGHT 
        self._update_event.set()