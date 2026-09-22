from .database import Database
from state import StateStore, EventType, AppState
import threading
import time

class Librian:
    def __init__(self) -> None:
        self.databse = Database()
        
        self.state_store = StateStore()
        self._unsub = self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)
        self.temperature = 0
        self.humidity = 0
        self.got_first_event = False

        self._stop_event = threading.Event()
        self._is_closed = False
        self._persist_thread = threading.Thread(target=self._persist_runner, daemon=True)
        self._persist_thread.start()

    def _on_env_changed(self, app_state: AppState) -> None:
        if self._stop_event.is_set():
            return
        if (app_state.temperature == 0 or app_state.humidity == 0):
            return
        self.got_first_event = True
        self.temperature = app_state.temperature
        self.humidity = app_state.humidity

    def _persist_runner(self) -> None:
        while not self._stop_event.is_set():
            if self._stop_event.wait(timeout=60 * 15):
                break
            if not self.got_first_event or self._stop_event.is_set():
                continue
            try:
                self.databse.save(
                    self.temperature,
                    self.humidity
                )
            except Exception:
                if not self._stop_event.is_set():
                    print(f"[librian] unable to persist temperature and humidity")

    def close(self) -> None:
        """Stops persist thread and unsubscribes from state store cleanly."""
        if self._is_closed:
            return
        self._is_closed = True
        self._stop_event.set()
        if hasattr(self, "_unsub") and self._unsub:
            try:
                self._unsub()
            except Exception:
                pass
        if (
            hasattr(self, "_persist_thread")
            and self._persist_thread.is_alive()
            and threading.current_thread() != self._persist_thread
        ):
            self._persist_thread.join(timeout=1.0)
