from __future__ import annotations

from dataclasses import dataclass, replace
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
    LOOKING_AROUND = "looking_around"

@dataclass(frozen=True)
class TempAndHumi:
    temperature: float
    humidity: float

class ActionType(str, Enum):
    SET_MOOD = "SetMood"
    KNOB = "Knob"
    SET_ENVIRONMENT = "SetEnvironment"
    SET_TEMP_HUMI = "SetTempHumi"


class EventType(str, Enum):
    STATE_UPDATED = "state.updated"
    MOOD_CHANGED = "mood.changed"
    KNOB = "knob"
    ENVIRONMENT_CHANGED = "environment.changed"

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
    payload: Mood = Mood.NEUTRAL

    def __init__(self, mood: Mood) -> None:
        super().__init__(ActionType.SET_MOOD, mood)

@dataclass(frozen=True)
class Knob(Action):
    payload: KnobUserAction = KnobUserAction.PRESS

    def __init__(self, action: KnobUserAction = KnobUserAction.PRESS) -> None:
        object.__setattr__(self, 'payload', action)
        object.__setattr__(self, 'type', ActionType.KNOB)

@dataclass(frozen=True)
class SetSomeoneAround(Action):
    payload: bool = False

    def __init__(self, someone_around: bool) -> None:
        super().__init__(ActionType.SET_ENVIRONMENT, someone_around)

@dataclass(frozen=True)
class SetTemAndHumi(Action):
    payload: TempAndHumi = TempAndHumi(0, 0)

    def __init__(self, temp_and_humi: TempAndHumi) -> None:
        super().__init__(ActionType.SET_TEMP_HUMI, temp_and_humi)

@dataclass(frozen=True)
class AppState:
    mood: Mood = Mood.NEUTRAL
    someone_around: bool = False
    temperature: float = 0
    humidity: float = 0

def reduce_state(state: AppState, action: Action) -> AppState:
    if action.type == ActionType.SET_MOOD:
        if not isinstance(action.payload, Mood):
            raise ValueError("SetMood action payload must be a Mood value.")
        return replace(state, mood=action.payload)
    if action.type == ActionType.KNOB:
        return state
    if action.type == ActionType.SET_ENVIRONMENT:
        if not isinstance(action.payload, bool):
            raise ValueError("SetEnvironment action payload must be a bool value.")
        return replace(state, someone_around=action.payload)
    if action.type == ActionType.SET_TEMP_HUMI:
        if not isinstance(action.payload, TempAndHumi):
            raise ValueError("SetTempAndHumi action payload must be a TempAndHumi.")
        return replace(state, temperature = action.payload.temperature, humidity = action.payload.humidity)
    return state
