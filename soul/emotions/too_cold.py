from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class TooCold:
    """
    Discomfort triggered when ambient temperature falls below 18°C.
    Scales smoothly: at 17°C increases slowly, at 14°C faster, at 10°C much faster.
    When at or above 18°C, gently warms up back to 0.
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
        if 0.0 < self.current_temp < 18.0:
            # Scaled rate: 17°C -> +0.25/s, 14°C -> +1.0/s, 10°C -> +2.0/s
            rate = (18.0 - self.current_temp) * 0.25
            self.emotion.increase_level(rate)
        else:
            # Comfortable or warm: slowly recedes back to 0
            self.emotion.decrease_level(0.4)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
