from dataclasses import dataclass
import threading


@dataclass
class EmotionConfig:
    max_level: float = 100.0
    cooldown_trigger_level: float = 100.0  # Starts cooldown only when reaching 100
    cooldown_recovery_level: float = 0.0   # Recovers from cooldown when decaying back to 0
    cooldown_decay_rate: float = 2.0       # Decay per second while in cooldown (50s from 100 to 0)
    natural_decay_rate: float = 0.0        # Natural decay per second during normal state


class BaseEmotion:
    def __init__(self, config: EmotionConfig | None = None):
        self.config = config or EmotionConfig()
        self.level: float = 0.0
        self.on_cooldown = False
        self._lock = threading.Lock()

    def increase_level(self, amount: float = 10.0) -> None:
        """Increase the emotion level. Blocked if the emotion is currently cooling down."""
        with self._lock:
            if self.on_cooldown:
                return

            self.level = min(float(self.config.max_level), float(self.level + amount))
            if self.level >= self.config.cooldown_trigger_level:
                self.level = float(self.config.max_level)
                self.on_cooldown = True

    def decrease_level(self, amount: float = 10.0) -> None:
        """Decrease the emotion level and clear cooldown if recovery threshold is met."""
        with self._lock:
            self.level = max(0.0, float(self.level - amount))
            if self.on_cooldown and self.level <= self.config.cooldown_recovery_level:
                self.level = 0.0
                self.on_cooldown = False

    def decay_tick(self) -> None:
        """Periodic decay step invoked by EmotionStateManager."""
        with self._lock:
            rate = self.config.cooldown_decay_rate if self.on_cooldown else self.config.natural_decay_rate
            if rate > 0.0:
                self.level = max(0.0, float(self.level - rate))
                if self.on_cooldown and self.level <= self.config.cooldown_recovery_level:
                    self.level = 0.0
                    self.on_cooldown = False