import random
from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class Bored:
    """
    Boredom moves dynamically with a random walk.
    When alone, it randomly fluctuates while steadily drifting upwards.
    When someone is around, it dynamically decreases towards 0.
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
            # Arrival of someone significantly dispels boredom
            self.emotion.decrease_level(40)

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        if not self.someone_around:
            # Random walk with upward drift when left alone
            step = random.uniform(-0.6, 1.2)
            if step > 0:
                self.emotion.increase_level(step)
            else:
                self.emotion.decrease_level(-step)
        else:
            # Fluctuating decrease when someone is around
            step = random.uniform(0.4, 1.5)
            self.emotion.decrease_level(step)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
