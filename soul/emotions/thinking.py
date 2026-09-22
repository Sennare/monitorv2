from .base_emotion import BaseEmotion


class Thinking:
    """Contemplative state activated through spontaneous pacing."""

    def __init__(self):
        self.emotion = BaseEmotion()

    def tick(self) -> None:
        pass

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
