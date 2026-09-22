from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class TooHot:
    """
    Discomfort triggered when ambient temperature exceeds 26°C.
    Scales smoothly: at 27°C increases slowly, at 30°C faster, at 35°C much faster.
    When at or below 26°C, gently cools down back to 0.
    """

    def __init__(self):
        self.emotion = BaseEmotion()
        self.current_temp = 0.0
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        self.current_temp = app_state.temperature

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        if self.current_temp > 26.0:
            # Scaled rate: 27°C -> +0.25/s, 30°C -> +1.0/s, 35°C -> +2.25/s
            rate = (self.current_temp - 26.0) * 0.25
            self.emotion.increase_level(rate)
        else:
            # Below heat threshold: slowly recedes back to 0
            self.emotion.decrease_level(0.4)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
