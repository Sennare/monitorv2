from .base_emotion import BaseEmotion


class Confused:
    """Quirky confusion activated through spontaneous pacing."""

    def __init__(self):
        self.emotion = BaseEmotion()

    def tick(self) -> None:
        pass

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
