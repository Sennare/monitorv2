from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class TooHot:
    """Discomfort triggered when ambient temperature exceeds 27°C."""

    def __init__(self):
        self.emotion = BaseEmotion()
        self.current_temp = 0.0
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        self.current_temp = app_state.temperature

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        if self.current_temp > 27.0:
            self.emotion.increase_level(6)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
