import smbus2
import time


class Lcd:
    """Gestione LCD 20x4 via I2C (compatibile HW-061)."""
    
    # Indirizzo I2C (0x27 o 0x3F, verificare con i2cdetect)
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
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00
    
    # Modalità 4-bit per 20x4
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x28  # Per 20x4, usiamo 2 linee ma con 4 righe (gestite via DDRAM)
    LCD_5x8DOTS = 0x00
    
    # Indirizzi DDRAM per 20x4
    LCD_LINE_ADDRESSES = [0x00, 0x40, 0x14, 0x54]
    
    def __init__(self, i2c_addr=LCD_ADDR, bus=1):
        """Inizializza il display con sequenza compatibile Arduino."""
        self.bus = smbus2.SMBus(bus)
        self.addr = i2c_addr
        self.backlight = True
        self.display_on = True
        
        # Sequenza di inizializzazione per 20x4
        self._init()
        
    def _send(self, data, mode=0):
        """Invia un byte al display (mode=0: comando, mode=1: dato)."""
        # Bit alto/nibble alto
        high_nib = mode | (data & 0xF0) | (self.LCD_BACKLIGHT if self.backlight else 0)
        self.bus.write_byte(self.addr, high_nib)
        time.sleep(0.001)
        self.bus.write_byte(self.addr, high_nib | 0x04)
        time.sleep(0.001)
        self.bus.write_byte(self.addr, high_nib)
        time.sleep(0.001)
        
        # Bit basso/nibble basso
        low_nib = mode | ((data & 0x0F) << 4) | (self.LCD_BACKLIGHT if self.backlight else 0)
        self.bus.write_byte(self.addr, low_nib)
        time.sleep(0.001)
        self.bus.write_byte(self.addr, low_nib | 0x04)
        time.sleep(0.001)
        self.bus.write_byte(self.addr, low_nib)
        time.sleep(0.001)
        
    def _init(self):
        """Sequenza di inizializzazione per 20x4."""
        time.sleep(0.1)
        
        # Sequenza di reset (3 volte)
        self._send(0x33, 0)
        time.sleep(0.01)
        self._send(0x33, 0)
        time.sleep(0.01)
        self._send(0x32, 0)
        time.sleep(0.01)
        
        # Imposta 4-bit, 2 linee, 5x8 font
        self._send(0x28, 0)
        time.sleep(0.01)
        
        # Imposta contrasto massimo
        self._send(0x70 | 0x0F, 0)
        time.sleep(0.01)
        
        # Spegni display
        self._send(0x08, 0)
        time.sleep(0.01)
        
        # Cancella display
        self._send(0x01, 0)
        time.sleep(0.02)
        
        # Modalità entry: increment, no shift
        self._send(0x06, 0)
        time.sleep(0.01)
        
        # Accendi display
        self._send(0x0C, 0)
        time.sleep(0.01)
        
    def clear(self):
        """Cancella il display."""
        self._send(0x01, 0)
        time.sleep(0.02)
        
    def set_backlight(self, state):
        """Accende/spegne la retroilluminazione."""
        self.backlight = state
        self._send(0x00, 0)  # Aggiorna lo stato
        
    def set_cursor(self, col, row):
        """Imposta la posizione del cursore (0-19, 0-3)."""
        if row < 0 or row >= self.LCD_HEIGHT:
            return
        if col < 0 or col >= self.LCD_WIDTH:
            return
        address = self.LCD_LINE_ADDRESSES[row] + col
        self._send(0x80 | address, 0)
        
    def write_text(self, text, row=0):
        """Scrive testo su una riga specifica (0-3)."""
        if not self.display_on:
            return
        
        text = text.ljust(self.LCD_WIDTH)[:self.LCD_WIDTH]
        self.set_cursor(0, row)
        for char in text:
            self._send(ord(char), 1)
        
    def write(self, line1="", line2="", line3="", line4=""):
        """Scrive testo su tutte e 4 le righe."""
        self.clear()
        self.write_text(line1, 0)
        self.write_text(line2, 1)
        self.write_text(line3, 2)
        self.write_text(line4, 3)
