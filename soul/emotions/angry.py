from .base_emotion import BaseEmotion, EmotionConfig


class Angry:
    """
    Anger is strictly input-driven (e.g. entering the Settings view).
    Does not fluctuate spontaneously or autonomously.
    When triggered, it decays steadily until reaching 0.
    """

    def __init__(self):
        # Decays steadily during cooldown (and natural fallback if not on cooldown)
        self.emotion = BaseEmotion(EmotionConfig(cooldown_decay_rate=2.0, natural_decay_rate=1.0))

    def tick(self) -> None:
        """Angry does not autonomously drift or tick."""
        pass

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
