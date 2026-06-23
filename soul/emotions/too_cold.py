from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class TooCold:
    def __init__(self):
        self.emotion = BaseEmotion()
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        if app_state.temperature < 15:
            self.emotion.increase_level(4)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
