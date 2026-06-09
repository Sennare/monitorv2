import random

from state import  Mood, SetMood, StateStore, EventType, AppState
import asyncio


class EmotionStateManager:
    def __init__(self):
        self.debug_mode = False
        self.mood: Mood = Mood.NEUTRAL
        self.state_store = StateStore()
        self.state_store.dispatch(SetMood(Mood.NEUTRAL))
        self.state_store.subscribe(EventType.KNOB.value, self._on_knob_pressed)
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)
        self.last_idle_mood = None
        self.idle_moods = [Mood.BORED, Mood.THINKING, Mood.CURIOUS]
        self.someone_around_lately = False
        self.cool_down_moods: list[Mood] = []
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
            Mood.LOOKING_AROUND: 0,
        }
    
    async def startWorker(self):
        while True:
            await asyncio.sleep(2)
            self.reduce_all_emotions_levels()
            idle_choice_moods = self.idle_moods.copy()
            if self.last_idle_mood in idle_choice_moods:
                idle_choice_moods.remove(self.last_idle_mood)
            random_mood = random.choice(idle_choice_moods)
            if random.random() < 0.5:
                self.increase_mood_level(random_mood, by=3)
            if self.debug_mode:
                self.debug_print_emotions_levels()
            self.reset_cooled_down()
            self.check_and_update_mood()

    def _on_knob_pressed(self, _):
        self.increase_mood_level(Mood.HAPPY, by=10)
    
    def _on_env_changed(self, app_state: AppState) -> None:
        if (app_state.temperature > 27):
            self.increase_mood_level(Mood.TOO_HOT, by=4)
            
        if app_state.someone_around and not self.someone_around_lately:
            self.increase_mood_level(Mood.LOOKING_AROUND, by=10)
            self.someone_around_lately = True
        if not app_state.someone_around:
            self.someone_around_lately = False

    def check_and_update_mood(self):
        # Determine the mood with the highest level
        new_mood = max(self.emotions_levels, key=self.emotions_levels.get) # type: ignore
        new_mood_level = self.emotions_levels[new_mood]
        if (new_mood_level < 6):
            new_mood = Mood.NEUTRAL
        if new_mood != self.mood:
            if new_mood in self.idle_moods:
                self.last_idle_mood = new_mood
            self.mood = new_mood
            self.state_store.dispatch(SetMood(self.mood))

    def reduce_all_emotions_levels(self, by: int = 1, except_mood: Mood | None = None):
        for mood in self.emotions_levels:
            if mood == None or mood != except_mood:
                self.emotions_levels[mood] = max(0, self.emotions_levels[mood] - by);
        #self.check_and_update_mood()

    def increase_mood_level(self, mood: Mood, by: int = 1):
        if (mood in self.cool_down_moods):
            return
        self.emotions_levels[mood] = min(10, self.emotions_levels[mood] + by)
        if (self.emotions_levels[mood] >= 10):
            self.cool_down_moods.append(mood)
        #self.check_and_update_mood()

    def reset_cooled_down(self) -> None:
        for mood in self.cool_down_moods:
            if self.emotions_levels[mood] <= 0:
                self.cool_down_moods.remove(mood)
    
    def debug_print_emotions_levels(self):
        print("Current emotion levels:")

        max_len = max(len(mood.value) for mood in self.emotions_levels) + 1

        for mood, level in self.emotions_levels.items():
            cooling_down = "*" if mood in self.cool_down_moods else " "
            label = f"{mood.value}{cooling_down}"
            print(
                f"  {label:<{max_len}} : "
                f"[{'#' * level}{' ' * (10 - level)}] {level}/10"
            )