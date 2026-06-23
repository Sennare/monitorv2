import threading
import random
import time

from .base_emotion import BaseEmotion


class Thinking:
    def __init__(self):
        self.emotion = BaseEmotion()
        self._thread = threading.Thread(target=self._runner, daemon=True)
        self._thread.start()

    def _runner(self):
        while True:
            time.sleep(1)

            # Recuperiamo il livello attuale (assumo ci sia un attributo o metodo simile)
            current_level = self.emotion.level

            # Calcoliamo la probabilità: es. a livello 0 è 0.05 (5%), a livello 100 è 1.0 (100%)
            # Usiamo max() per garantire una probabilità minima di partenza
            probability = max(0.15, current_level / 100.0) - 0.10

            # random.random() genera un float tra 0.0 e 1.0
            if random.random() < probability:
                self.emotion.increase_level(10)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
