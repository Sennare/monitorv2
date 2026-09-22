from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.animations.cat_blink import CuteCatBlinkAnimation
from state import AppState, KnobUserAction, StateStore, BoostEmotion, Mood
from typing import Optional


class CatPage(AbstractLocation):
    """
    Cute Cat Mascot screen: plays the Cat Blink animation while active.
    Boosts HAPPY emotion on soul.
    """

    def __init__(self):
        self.state_store = StateStore()
        self._animation = CuteCatBlinkAnimation()

    def on_enter(self) -> None:
        self.state_store.dispatch(BoostEmotion(Mood.HAPPY, 50))

    def render(self, lcd: LCDCore, state: AppState) -> None:
        # Loop animation smoothly
        lcd.play_animation(self._animation, frame_delay=0.4, cycles=999)

    def on_exit(self) -> None:
        pass

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        # User interacted, leave mascot screen back to menu
        return "MENU"
