from __future__ import annotations

from typing import Any, Callable, Dict, List

from .events import (
    Action,
    ActionType,
    AppState,
    EventType,
    Mood,
    SetMood,
    reduce_state,
)


class EventBus:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        self._listeners.setdefault(event_type, []).append(callback)

        def unsubscribe() -> None:
            listeners = self._listeners.get(event_type)
            if listeners and callback in listeners:
                listeners.remove(callback)

        return unsubscribe

    def publish(self, event_type: str, payload: Any = None) -> None:
        for callback in list(self._listeners.get(event_type, [])):
            callback(payload)


class StateStore:
    _instance: "StateStore | None" = None

    def __new__(cls, initial_state: AppState | None = None) -> "StateStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, initial_state: AppState | None = None) -> None:
        if getattr(self, "_initialized", False):
            return

        self._state = initial_state or AppState()
        self.bus = EventBus()
        self._initialized = True

    @property
    def state(self) -> AppState:
        return self._state

    def get_state(self) -> AppState:
        return self._state

    def dispatch(self, action: Action) -> None:
        previous_state = self._state
        self._state = reduce_state(self._state, action)

        self.bus.publish(
            EventType.STATE_UPDATED.value,
            {"previous": previous_state, "current": self._state, "action": action},
        )

        if action.type == ActionType.SET_MOOD:
            self.bus.publish(EventType.MOOD_CHANGED.value, self._state.mood)

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        return self.bus.subscribe(event_type, callback)

    def publish(self, event_type: str, payload: Any = None) -> None:
        self.bus.publish(event_type, payload)
