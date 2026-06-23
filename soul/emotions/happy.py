from .base_emotion import BaseEmotion
from state import StateStore, EventType


class Happy:
    def __init__(self):
        self.emotion = BaseEmotion()
        self.state_store = StateStore()
        self.state_store.subscribe(EventType.KNOB.value, self._on_knob_pressed)

    def _on_knob_pressed(self, _):
        self.emotion.increase_level(10)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
