from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class LookingAround:
    """Triggered with high priority once when someone newly enters the room."""

    def __init__(self):
        self.emotion = BaseEmotion()
        self.someone_around_lately = False
        self.someone_around = False

        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        self.someone_around = app_state.someone_around
        if self.someone_around and not self.someone_around_lately:
            self.someone_around_lately = True
            # Strong awareness surge upon arrival
            self.emotion.increase_level(80)
        elif not self.someone_around:
            self.someone_around_lately = False

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        if self.someone_around:
            import random
            if random.random() < 0.04:
                # Periodic quick glance / scan around the room
                self.emotion.increase_level(20)
            else:
                self.emotion.decrease_level(0.8)
        else:
            self.emotion.decrease_level(1.2)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion