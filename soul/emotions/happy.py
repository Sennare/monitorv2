from .base_emotion import BaseEmotion


class Happy:
    """Happiness is directly boosted by physical user knob interactions."""

    def __init__(self):
        self.emotion = BaseEmotion()

    def _on_knob_interacted(self, _) -> None:
        self.emotion.increase_level(60)

    def tick(self) -> None:
        pass

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
