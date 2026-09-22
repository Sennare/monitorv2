from .base_emotion import BaseEmotion


class Neutral:
    """Default baseline resting state."""

    def __init__(self):
        self.emotion = BaseEmotion()

    def tick(self) -> None:
        pass

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
