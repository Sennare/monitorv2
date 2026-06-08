from enum import Enum


class Mood(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    CURIOUS = "curious"
    CONFUSED = "confused"
    THINKING = "thinking"

class EmotionStateManager:
    mood: Mood = Mood.NEUTRAL
    
    def set_mood(self, mood: Mood) -> None:
        self.mood = mood