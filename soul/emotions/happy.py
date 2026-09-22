from .base_emotion import BaseEmotion
from state import StateStore, EventType


class Happy:
    """Happiness is directly boosted by physical user knob interactions."""

    def __init__(self):
        self.emotion = BaseEmotion()
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.KNOB.value, self._on_knob_interacted)

    def _on_knob_interacted(self, _) -> None:
        self.emotion.increase_level(35)

    def tick(self) -> None:
        pass

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
