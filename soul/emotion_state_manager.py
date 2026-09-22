import random
from state import Mood, SetMood, StateStore, EventType
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
    THRESHOLD = 50          # Level threshold required to display an active emotion
    MIN_IDLE_SECONDS = 35   # Minimum guaranteed Idle time (in seconds) between spontaneous emotions

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

        # Subscribe to emotion boost events (from navigation / user actions)
        self._unsub_boost = self.state_store.subscribe(EventType.EMOTION_BOOST.value, self._on_boost_emotion)
        self._unsub_knob = self.state_store.subscribe(EventType.KNOB.value, self._on_knob_interacted)

        # Tracks consecutive seconds spent in Idle state
        self._idle_seconds = 0

    def close(self) -> None:
        """Clean up subscribers."""
        if hasattr(self, "_unsub_boost") and self._unsub_boost:
            try:
                self._unsub_boost()
            except Exception:
                pass
        if hasattr(self, "_unsub_knob") and self._unsub_knob:
            try:
                self._unsub_knob()
            except Exception:
                pass

    def _on_knob_interacted(self, payload) -> None:
        """Physical knob rotation or press stimulates Happy emotion immediately."""
        # When expressing an explicit negative/alert emotion (like Angry in Settings), do not override with Happy
        if self.mood == Mood.ANGRY:
            return
        inst = self.emotion_instances.get(Mood.HAPPY)
        if inst:
            emotion_obj = inst.get_emotion()
            emotion_obj.on_cooldown = False
            emotion_obj.increase_level(60)
            self.check_and_update_mood(preferred_mood=Mood.HAPPY)

    def _on_boost_emotion(self, payload) -> None:
        """Handle explicit emotion boost requests from navigation or interactions."""
        if not payload:
            return
        mood, amount = payload
        inst = self.emotion_instances.get(mood)
        if inst:
            emotion_obj = inst.get_emotion()
            emotion_obj.on_cooldown = False
            emotion_obj.increase_level(amount)
            # When an emotion is explicitly boosted (e.g. Settings -> Angry, Sensors -> Curious),
            # ensure it takes focus over lingering passive emotions (like knob happiness)
            for other_mood, other_inst in self.emotion_instances.items():
                if other_mood != mood and other_mood != Mood.NEUTRAL:
                    other_emo = other_inst.get_emotion()
                    if other_emo.level >= emotion_obj.level:
                        other_emo.level = max(0, emotion_obj.level - 10)
            print(f"[emotion] Boosted emotion {mood.value} by {amount} (new level: {emotion_obj.level})")
            self.check_and_update_mood(preferred_mood=mood)

    async def startWorker(self):
        try:
            while True:
                await asyncio.sleep(1.0)

                # 1. Apply decay tick (handles normal decay and cooldown recovery to 0)
                for inst in self.emotion_instances.values():
                    try:
                        inst.get_emotion().decay_tick()
                    except Exception as e:
                        print(f"[emotion] Error during decay: {e}")

                # 2. Trigger any continuous hardware-reactive ticks (e.g. ambient temperature)
                for inst in self.emotion_instances.values():
                    if hasattr(inst, "tick"):
                        try:
                            inst.tick()
                        except Exception as e:
                            print(f"[emotion] Error during tick: {e}")

                # 3. Evaluate and update dominant mood
                self.check_and_update_mood()

                # 4. Handle spontaneous emotion pacing (~1 emotion per minute)
                if self.mood == Mood.NEUTRAL:
                    self._idle_seconds += 1

                    # After staying idle for at least MIN_IDLE_SECONDS, roll probability for an emotion
                    # Average trigger window happens around ~45-65 seconds (roughly 1 minute)
                    if self._idle_seconds >= self.MIN_IDLE_SECONDS:
                        if random.random() < 0.05 or self._idle_seconds >= 70:
                            self._trigger_spontaneous_emotion()
                            self._idle_seconds = 0
                            self.check_and_update_mood()
                else:
                    self._idle_seconds = 0

                if self.debug_mode:
                    self.debug_print_emotions_levels()
        except asyncio.CancelledError:
            pass

    def _trigger_spontaneous_emotion(self) -> None:
        """Picks and triggers a spontaneous emotion roughly once per minute."""
        someone_around = self.state_store.state.someone_around

        if someone_around:
            # When someone is around, Curiosity is the dominant spontaneous emotion (60%),
            # followed by Thinking (20%), Confused (10%), or Happy (10%)
            candidates = [
                (Mood.CURIOUS, 0.60),
                (Mood.THINKING, 0.20),
                (Mood.CONFUSED, 0.10),
                (Mood.HAPPY, 0.10),
            ]
        else:
            # When alone, Thinking (40%), Bored (30%), Sad (15%), or Confused (15%)
            candidates = [
                (Mood.THINKING, 0.40),
                (Mood.BORED, 0.30),
                (Mood.SAD, 0.15),
                (Mood.CONFUSED, 0.15),
            ]

        moods, weights = zip(*candidates)
        chosen_mood = random.choices(moods, weights=weights)[0]

        inst = self.emotion_instances.get(chosen_mood)
        if inst and not inst.get_emotion().on_cooldown:
            print(f"[emotion] Spontaneous activation (~1/min): {chosen_mood.value} (someone_around={someone_around})")
            inst.get_emotion().increase_level(100)

    def check_and_update_mood(self, preferred_mood: Mood | None = None):
        # Filter non-neutral emotions to find highest stimulus
        non_neutral_levels = {
            mood: inst.get_emotion().level
            for mood, inst in self.emotion_instances.items()
            if mood != Mood.NEUTRAL
        }

        if not non_neutral_levels:
            new_mood = Mood.NEUTRAL
        else:
            max_level = max(non_neutral_levels.values())
            if max_level < self.THRESHOLD:
                new_mood = Mood.NEUTRAL
            elif (
                preferred_mood is not None
                and preferred_mood in non_neutral_levels
                and non_neutral_levels[preferred_mood] >= self.THRESHOLD
                and non_neutral_levels[preferred_mood] >= max_level
            ):
                new_mood = preferred_mood
            else:
                highest_mood = max(non_neutral_levels, key=non_neutral_levels.get)  # type: ignore
                new_mood = highest_mood

        if new_mood != self.mood:
            print(f"[emotion] Mood changed: {self.mood.value} -> {new_mood.value}")
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