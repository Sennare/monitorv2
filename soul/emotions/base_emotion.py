from dataclasses import dataclass
import threading
import time

@dataclass
class EmotionConfig:
    automatic_cooldown_enabled: bool = True
    automatic_cooldown_threshold: int = 90
    automatic_cooldown_rate: int = 2
    max_level:int = 100


class BaseEmotion:
    def __init__(self, config: EmotionConfig = EmotionConfig()):
        self.config = config
        self.level = 0
        self.on_cooldown = False
        
        # Questo lock ci servirà per capire se il task precedente sta ancora girando
        self._task_lock = threading.Lock()

        self._core_thread = threading.Thread(target=self._core_loop, daemon=True)
        self._core_thread.start()

    def _heavy_task(self):
        if self.on_cooldown:
            self.level -= self.config.automatic_cooldown_rate
            return

        if (self.config.automatic_cooldown_enabled 
            and self.level >= self.config.automatic_cooldown_threshold):
            self.on_cooldown = True

    def increase_level(self, amount: int = 10):
        if (self.on_cooldown):
            return
        if (self.level + amount > self.config.max_level):
            self.level = self.config.max_level
            return
        self.level += amount
    
    def decrease_level(self, amount: int = 10):
        if (self.level < amount):
            self.level = 0
            return;
        self.level -= amount

    def _core_loop(self):
        INTERVAL = 1.0  # I tuoi 30 secondi precisi
        next_run = time.time() + INTERVAL

        while True:
            # 1. TEMPISTICA PRECISA
            # Calcoliamo quanto manca al prossimo "rintocco" esatto dei 30s.
            # Questo elimina la deriva temporale causata dal tempo di esecuzione del codice interno.
            sleep_time = next_run - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Impostiamo già il millisecondo esatto in cui dovrà scattare il PROSSIMO ciclo
            next_run += INTERVAL

            # 2. GESTIONE DEL CONFLITTO (Evitiamo accumuli sulla CPU/RAM)
            # .acquire(blocking=False) prova a prendere il lock. 
            # Se è libero lo prende (True), se è già occupato ritorna False IMMEDIATAMENTE senza aspettare.
            if self._task_lock.acquire(blocking=False):
                # Il ciclo precedente è finito (o è il primo). 
                # Spediamo il lavoro pesante su un thread separato così il core_loop torna subito a dormire.
                worker = threading.Thread(target=self._wrapped_heavy_task, daemon=True)
                worker.start()
            else:
                # CONFLITTO DETECTED: Il worker precedente sta ancora lavorando dopo 30 secondi.
                # Saltiamo questo giro. In questo modo non accumulerai MAI thread infiniti.
                self._handle_conflict()

    def _wrapped_heavy_task(self):
        """Wrapper per essere sicuri che il lock venga rilasciato anche in caso di errori"""
        try:
            self._heavy_task()
        except Exception as e:
            print(error_logger := f"Errore durante l'esecuzione: {e}")
        finally:
            # Rilascia il lock: il prossimo ciclo da 30s potrà partire regolarmente
            self._task_lock.release()

    def _handle_conflict(self):
        """Cosa fare se il sistema è ancora occupato dal ciclo precedente"""
        print("⚠️ [Warning] Il ciclo precedente è ancora attivo. Salto questo turno per evitare sovraccarichi.")