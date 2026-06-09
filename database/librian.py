from .database import Database
from state import StateStore, EventType, AppState
import threading
import time

class Librian:
    def __init__(self) -> None:
        self.databse = Database()
        
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)
        self.temperature = 0
        self.humidity = 0
        self.got_first_event = False

        self._persist_thread = threading.Thread(target=self._persist_runner, daemon=True)
        self._persist_thread.start()

    def _on_env_changed(self, app_state: AppState) -> None:
        if (app_state.temperature == 0 or app_state.humidity == 0):
            return
        self.got_first_event = True
        self.temperature = app_state.temperature
        self.humidity = app_state.humidity

    def _persist_runner(self) -> None:
        while True:
            time.sleep(10)
            if not self.got_first_event:
                continue
            try:
                self.databse.save(
                    self.temperature,
                    self.humidity
                )
            except Exception:
                print(f"[librian] unable to persist temperature and humidity")
