import asyncio

import display.oled as oled
import soul.emotion_state_manager as emotion_state_manager
import input.knob_controller2 as knob_controller
from state import EventType, Mood, SetMood, StateStore
from navigation.navigation import Navigation

class Application:
    def __init__(self):
        self.tasks: list[asyncio.Task[None]] = []
        self.oled_display = oled.OledDisplay()
        self.emotion_manager = emotion_state_manager.EmotionStateManager()
        self.knob_controller = knob_controller.KnobController()
        self.state_store = StateStore()
        self.navigation = Navigation()

        print("[app] Initializing application")

    async def run(self) -> None:
        print("[app] Starting monitor application...")
        
        # Create background tasks
        self.tasks = [
            asyncio.create_task(self.emotion_manager.startWorker()),
            #asyncio.create_task(self.knob_controller.start_worker()),
        ]
        
        await asyncio.gather(*self.tasks)

async def main() -> None:
    app = Application()
    await app.run()
    await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"Fatal error: {e}")