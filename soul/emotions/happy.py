import random
from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class Happy:
    """
    Happiness is directly boosted by physical user knob interactions.
    Maintains a cheerful gentle baseline when someone is around,
    and gently recedes when left alone.
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
            # Warm dynamic baseline around 15-35%
            if level < 15.0:
                step = random.uniform(-0.1, 0.8)
            elif level > 40.0:
                step = random.uniform(-0.8, 0.1)
            else:
                step = random.uniform(-0.5, 0.5)

            if step > 0:
                self.emotion.increase_level(step)
            else:
                self.emotion.decrease_level(-step)
        else:
            # Gently recedes when alone
            self.emotion.decrease_level(0.4)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
