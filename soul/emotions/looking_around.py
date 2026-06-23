from .base_emotion import BaseEmotion
from state import StateStore, EventType, AppState


class LookingAround:
    def __init__(self):
        self.emotion = BaseEmotion()
        self.someone_around_lately = False

        self.state_store = StateStore()
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

    def _on_env_changed(self, app_state: AppState) -> None:
        if app_state.someone_around and not self.someone_around_lately:
            self.emotion.increase_level(100)
            self.someone_around_lately = True
        if not app_state.someone_around:
            self.someone_around_lately = False

    def get_emotion(self) -> BaseEmotion:
        return self.emotion