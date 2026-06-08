import asyncio

import oled
import emotion_state_manager
from state import EventType, Mood, SetMood, StateStore


class Application:
    def __init__(self):
        self.tasks: list[asyncio.Task[None]] = []
        self.oled_display = oled.OledDisplay()
        self.emotion_manager = emotion_state_manager.EmotionStateManager()
        self.state_store = StateStore()

        print("[app] Initializing application")

    async def run(self) -> None:
        print("[app] Starting monitor application...")
        
        # Create background tasks
        self.tasks = [
            asyncio.create_task(self.emotion_manager.startWorker()),
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