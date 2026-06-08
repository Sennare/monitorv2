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
    KNOB = "Knob"


class EventType(str, Enum):
    STATE_UPDATED = "state.updated"
    MOOD_CHANGED = "mood.changed"
    KNOB = "knob"

class KnobUserAction(str, Enum):
    PRESS = "press"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"


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
class Knob(Action):
    payload: KnobUserAction = KnobUserAction.PRESS

    def __init__(self, action: KnobUserAction = KnobUserAction.PRESS) -> None:
        object.__setattr__(self, 'payload', action)
        object.__setattr__(self, 'type', ActionType.KNOB)


@dataclass(frozen=True)
class AppState:
    mood: Mood = Mood.NEUTRAL


def reduce_state(state: AppState, action: Action) -> AppState:
    if action.type == ActionType.SET_MOOD:
        if not isinstance(action.payload, Mood):
            raise ValueError("SetMood action payload must be a Mood value.")
        return AppState(mood=action.payload)
    if action.type == ActionType.KNOB:
        return state
    return state
