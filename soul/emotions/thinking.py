import random
from .base_emotion import BaseEmotion


class Thinking:
    """
    Contemplative state that wanders dynamically over time.
    Exhibits gentle waves and fluctuations reflecting computational contemplation.
    """

    def __init__(self):
        self.emotion = BaseEmotion()

    def tick(self) -> None:
        """Called every second by EmotionStateManager."""
        level = self.emotion.level
        if level < 15.0:
            step = random.uniform(-0.3, 1.0)
        elif level > 55.0:
            step = random.uniform(-1.2, 0.3)
        else:
            step = random.uniform(-0.8, 0.8)

        if step > 0:
            self.emotion.increase_level(step)
        else:
            self.emotion.decrease_level(-step)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
