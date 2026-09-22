import random
from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class Sad:
    """
    Occasional loneliness or sadness when left alone for extended periods.
    Fluctuates dynamically with slow upward drift when alone, and recedes when someone arrives.
    """

    def __init__(self):
        self.emotion = BaseEmotion()
        self.someone_around = False
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        was_someone_around = self.someone_around
        self.someone_around = app_state.someone_around
        if not was_someone_around and self.someone_around:
            # Presence relieves sadness
            self.emotion.decrease_level(40)

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        if not self.someone_around:
            # Slow gentle drift upward when alone
            step = random.uniform(-0.5, 0.9)
            if step > 0:
                self.emotion.increase_level(step)
            else:
                self.emotion.decrease_level(-step)
        else:
            # Recedes when company is present
            step = random.uniform(0.5, 1.5)
            self.emotion.decrease_level(step)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
