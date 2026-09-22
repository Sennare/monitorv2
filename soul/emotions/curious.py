import random
from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class Curious:
    """
    Curiosity is stimulated by presence and wanders dynamically.
    Higher curiosity when someone is around, subtle baseline when alone.
    """

    def __init__(self):
        self.emotion = BaseEmotion()
        self.someone_around = False
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        self.someone_around = app_state.someone_around

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        level = self.emotion.level
        if self.someone_around:
            # Active wandering around 30-65%
            if level < 30.0:
                step = random.uniform(-0.2, 1.2)
            elif level > 65.0:
                step = random.uniform(-1.2, 0.2)
            else:
                step = random.uniform(-0.8, 0.8)
        else:
            # Quieter wandering around 5-20%
            if level < 5.0:
                step = random.uniform(-0.1, 0.5)
            elif level > 20.0:
                step = random.uniform(-0.8, 0.1)
            else:
                step = random.uniform(-0.4, 0.4)

        if step > 0:
            self.emotion.increase_level(step)
        else:
            self.emotion.decrease_level(-step)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
