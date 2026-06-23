from .base_emotion import BaseEmotion


class Confused:
    def __init__(self):
        self.emotion = BaseEmotion()

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
