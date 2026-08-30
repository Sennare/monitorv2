import time
import board
import digitalio
from PIL import Image
import adafruit_rgb_display.ili9341 as ili9341

# 1. Configurazione Pin (Aggiornata con D13 per il LED)
cs_pin = digitalio.DigitalInOut(board.D8)
dc_pin = digitalio.DigitalInOut(board.D24)
reset_pin = digitalio.DigitalInOut(board.D6)
led_pin = digitalio.DigitalInOut(board.D13)  # <-- Modificato a 13

# 2. Accendiamo il LED
led_pin.switch_to_output(value=True) 

# 3. Inizializziamo il bus SPI
spi = board.SPI()

# 4. Creazione display (Baudrate a 5MHz per sicurezza)
disp = ili9341.ILI9341(
    spi,
    rotation=90, 
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=64000000,
)

# 5. Invio immagine VERDE
print("Mostro la schermata verde...")
image_verde = Image.new("RGB", (320, 240), color="green")
disp.image(image_verde)

# 6. Attesa 5 secondi
print("Attendo 5 secondi...")
time.sleep(5)

# ---------------------------------------------------------
# 7. SEQUENZA DI SPEGNIMENTO
# ---------------------------------------------------------
print("Avvio sequenza di spegnimento...")

# A) Copriamo tutto con un'immagine NERA (cancella la memoria del display)
image_nera = Image.new("RGB", (320, 240), color="black")
disp.image(image_nera)

# B) Spegniamo il LED (Retroilluminazione)
led_pin.value = False 

# C) Mettiamo il display in Reset perenne (spegne la matrice LCD)
reset_pin.value = False 

print("Programma terminato.")