from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

class Mood(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    CURIOUS = "curious"
    CONFUSED = "confused"
    THINKING = "thinking"
    TOO_COLD = "too_cold"
    TOO_HOT = "too_hot"
    BORED = "bored"


class ActionType(str, Enum):
    SET_MOOD = "SetMood"
    KNOB_BTN_PRESSED = "KnobBtnPressed"


class EventType(str, Enum):
    STATE_UPDATED = "state.updated"
    MOOD_CHANGED = "mood.changed"
    KNOB_BTN_PRESSED = "knob.btn.pressed"


@dataclass(frozen=True)
class Action:
    type: ActionType
    payload: Any = None


@dataclass(frozen=True)
class SetMood(Action):
    payload: Mood

    def __init__(self, mood: Mood) -> None:
        super().__init__(ActionType.SET_MOOD, mood)

@dataclass(frozen=True)
class KnobBtnPressed(Action):
    payload: None = None

    def __init__(self) -> None:
        super().__init__(ActionType.KNOB_BTN_PRESSED, self.payload)


@dataclass(frozen=True)
class AppState:
    mood: Mood = Mood.NEUTRAL


def reduce_state(state: AppState, action: Action) -> AppState:
    if action.type == ActionType.SET_MOOD:
        if not isinstance(action.payload, Mood):
            raise ValueError("SetMood action payload must be a Mood value.")
        return AppState(mood=action.payload)
    if action.type == ActionType.KNOB_BTN_PRESSED:
        return state
    return state
