from state import Mood, SetMood, StateStore
import asyncio

from .emotions.looking_around import LookingAround
from .emotions.happy import Happy
from .emotions.too_hot import TooHot
from .emotions.too_cold import TooCold
from .emotions.bored import Bored
from .emotions.thinking import Thinking
from .emotions.curious import Curious
from .emotions.confused import Confused
from .emotions.sad import Sad
from .emotions.angry import Angry
from .emotions.neutral import Neutral


class EmotionStateManager:
    def __init__(self):
        self.debug_mode = False
        self.mood: Mood = Mood.NEUTRAL
        self.state_store = StateStore()
        self.state_store.dispatch(SetMood(Mood.NEUTRAL))

        # instantiate one class per emotion; each class wraps a `BaseEmotion`
        self.emotion_instances = {
            Mood.NEUTRAL: Neutral(),
            Mood.HAPPY: Happy(),
            Mood.SAD: Sad(),
            Mood.ANGRY: Angry(),
            Mood.CURIOUS: Curious(),
            Mood.CONFUSED: Confused(),
            Mood.THINKING: Thinking(),
            Mood.TOO_COLD: TooCold(),
            Mood.TOO_HOT: TooHot(),
            Mood.BORED: Bored(),
            Mood.LOOKING_AROUND: LookingAround(),
        }

    async def startWorker(self):
        while True:
            await asyncio.sleep(2)
            # apply gentle decay to all emotions
            for inst in self.emotion_instances.values():
                try:
                    inst.get_emotion().decrease_level(1)
                except Exception:
                    pass

            if self.debug_mode:
                self.debug_print_emotions_levels()

            self.check_and_update_mood()

    def check_and_update_mood(self):
        # collect levels
        levels = {mood: inst.get_emotion().level for mood, inst in self.emotion_instances.items()}
        new_mood = max(levels, key=levels.get)  # type: ignore
        new_mood_level = levels[new_mood]
        if new_mood_level < 60:
            new_mood = Mood.NEUTRAL
        if new_mood != self.mood:
            self.mood = new_mood
            self.state_store.dispatch(SetMood(self.mood))

    def debug_print_emotions_levels(self):
        print("Current emotion levels:")
        max_len = max(len(m.value) for m in self.emotion_instances) + 1
        
        for mood, inst in self.emotion_instances.items():
            level = inst.get_emotion().level  # Valore da 0 a 100
            
            # Calcoliamo quanti blocchi da 10 sono completamente pieni
            full_blocks = level // 10
            remainder = level % 10
            
            # Scegliamo il carattere per il valore intermedio in base al resto
            if remainder >= 7:
                intermediate = "▓"  # Densità alta
            elif remainder >= 4:
                intermediate = "▒"  # Densità media
            elif remainder >= 1:
                intermediate = "░"  # Densità bassa
            else:
                intermediate = ""   # Nessun blocco intermedio
                
            # Calcoliamo gli spazi vuoti rimanenti per garantire sempre 10 caratteri totali
            empty_blocks = 10 - full_blocks - (1 if intermediate else 0)
            
            # Componiamo la barra visiva
            bar = "█" * full_blocks + intermediate + " " * empty_blocks
            
            cooling_down = "*" if inst.get_emotion().on_cooldown else " "
            label = f"{mood.value}{cooling_down}"
            print(f"  {label:<{max_len}} : [{bar}] {level}/100")