from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class Bored:
    """Boredom is experienced when alone and instantly cleared when someone arrives."""

    def __init__(self):
        self.emotion = BaseEmotion()
        self.someone_around = False
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        self.someone_around = app_state.someone_around
        if self.someone_around:
            # Arrival of someone clears boredom immediately
            self.emotion.decrease_level(100)

    def tick(self) -> None:
        pass

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
