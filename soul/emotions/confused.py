import random
from .base_emotion import BaseEmotion


class Confused:
    """
    Quirky confusion that experiences subtle organic wanderings.
    Maintains a subtle presence without remaining static at 0.
    """

    def __init__(self):
        self.emotion = BaseEmotion()

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        level = self.emotion.level
        if level < 5.0:
            step = random.uniform(-0.1, 0.5)
        elif level > 25.0:
            step = random.uniform(-0.8, 0.1)
        else:
            step = random.uniform(-0.5, 0.5)

        if step > 0:
            self.emotion.increase_level(step)
        else:
            self.emotion.decrease_level(-step)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
