import random

from state import  Mood, SetMood, StateStore
import asyncio


class EmotionStateManager:
    def __init__(self):
        self.debug_mode = False
        self.mood: Mood = Mood.NEUTRAL
        self.state_store = StateStore()
        self.state_store.dispatch(SetMood(Mood.NEUTRAL))
        self.emotions_levels = {
            Mood.NEUTRAL: 10,
            Mood.HAPPY: 0,
            Mood.SAD: 0,
            Mood.ANGRY: 0,
            Mood.CURIOUS: 0,
            Mood.CONFUSED: 0,
            Mood.THINKING: 0,
            Mood.TOO_COLD: 0,
            Mood.TOO_HOT: 0,
            Mood.BORED: 0,
        }
    
    async def startWorker(self):
        while True:
            await asyncio.sleep(2)
            self.increase_mood_level(Mood.BORED)
            if self.debug_mode:
                self.debug_print_emotions_levels()

    def check_and_update_mood(self):
        # Determine the mood with the highest level
        new_mood = max(self.emotions_levels, key=self.emotions_levels.get)
        if new_mood != self.mood:
            self.mood = new_mood
            self.state_store.dispatch(SetMood(self.mood))

    def reduce_all_emotions_levels(self, except_mood: Mood):
        for mood in self.emotions_levels:
            if mood != except_mood:
                self.emotions_levels[mood] = max(0, self.emotions_levels[mood] - 1);
        self.check_and_update_mood()

    def increase_mood_level(self, mood: Mood):
        self.reduce_all_emotions_levels(except_mood=mood)
        self.emotions_levels[mood] = min(10, self.emotions_levels[mood] + 2)
        self.check_and_update_mood()
    
    def debug_print_emotions_levels(self):
        print("Current emotion levels:")
        for mood, level in self.emotions_levels.items():
            print(f"  {mood.value}: [{'#' * level}{' ' * (10 - level)}] {level}/10")