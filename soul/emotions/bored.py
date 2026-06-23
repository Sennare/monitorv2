import threading
import time

from .base_emotion import BaseEmotion


class Bored:
    def __init__(self):
        self.emotion = BaseEmotion()
        self._thread = threading.Thread(target=self._runner, daemon=True)
        self._thread.start()

    def _runner(self):
        while True:
            time.sleep(5)
            self.emotion.increase_level(1)

    def get_emotion(self) -> BaseEmotion:
        return self.emotion
