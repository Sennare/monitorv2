from dataclasses import dataclass
import threading


@dataclass
class EmotionConfig:
    max_level: int = 100
    cooldown_trigger_level: int = 100  # Starts cooldown only when reaching 100
    cooldown_recovery_level: int = 0   # Recovers from cooldown when decaying back to 0
    cooldown_decay_rate: int = 4       # Decay per second while in cooldown
    natural_decay_rate: int = 2        # Natural decay per second during normal state


class BaseEmotion:
    def __init__(self, config: EmotionConfig | None = None):
        self.config = config or EmotionConfig()
        self.level = 0
        self.on_cooldown = False
        self._lock = threading.Lock()

    def increase_level(self, amount: int = 10) -> None:
        """Increase the emotion level. Blocked if the emotion is currently cooling down."""
        with self._lock:
            if self.on_cooldown:
                return

            self.level = min(self.config.max_level, self.level + amount)
            if self.level >= self.config.cooldown_trigger_level:
                self.level = self.config.max_level
                self.on_cooldown = True

    def decrease_level(self, amount: int = 10) -> None:
        """Decrease the emotion level and clear cooldown if recovery threshold is met."""
        with self._lock:
            self.level = max(0, self.level - amount)
            if self.on_cooldown and self.level <= self.config.cooldown_recovery_level:
                self.on_cooldown = False

    def decay_tick(self) -> None:
        """Periodic decay step invoked by EmotionStateManager."""
        with self._lock:
            rate = self.config.cooldown_decay_rate if self.on_cooldown else self.config.natural_decay_rate
            self.level = max(0, self.level - rate)
            if self.on_cooldown and self.level <= self.config.cooldown_recovery_level:
                self.on_cooldown = False