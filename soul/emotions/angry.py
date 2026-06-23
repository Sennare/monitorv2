from .base_emotion import BaseEmotion


class Angry:
    def __init__(self):
        self.emotion = BaseEmotion()

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
