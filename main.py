import asyncio
import atexit
import signal
import sys

import display.oled as oled
import soul.emotion_state_manager as emotion_state_manager
import input.knob_controller2 as knob_controller
from state import EventType, Mood, SetMood, StateStore
from navigation.navigation import Navigation
from input.movement import Movement
from input.temp import Temp
from database.librian import Librian

class Application:
    def __init__(self):
        self.tasks: list[asyncio.Task[None]] = []
        self._is_closed = False

        print("[app] Initializing application")
        self.state_store = StateStore()
        self.oled_display = oled.OledDisplay()
        self.emotion_manager = emotion_state_manager.EmotionStateManager()
        self.knob_controller = knob_controller.KnobController()
        self.movement = Movement()
        self.navigation = Navigation()
        self.temp = Temp()
        self.librian = Librian()

        # Emergency fallback to ensure background threads stop before interpreter exit
        atexit.register(self.close)

    async def run(self) -> None:
        print("[app] Starting monitor application...")

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        # Handle termination signals cleanly
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except (NotImplementedError, RuntimeError):
                pass
        
        # Create background tasks
        self.tasks = [
            asyncio.create_task(self.emotion_manager.startWorker()),
            #asyncio.create_task(self.knob_controller.start_worker()),
        ]

        stop_wait = asyncio.create_task(stop_event.wait())
        all_tasks = self.tasks + [stop_wait]

        done, pending = await asyncio.wait(
            all_tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        for task in self.tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    def close(self) -> None:
        """Gracefully shuts down all hardware subsystems and background threads."""
        if self._is_closed:
            return
        self._is_closed = True

        print("[app] Shutting down application...")

        # Cancel any pending asyncio tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        if hasattr(self, "oled_display") and self.oled_display is not None:
            try:
                self.oled_display.close()
            except Exception as e:
                print(f"[app] Error closing OLED: {e}")

        if hasattr(self, "navigation") and self.navigation is not None:
            try:
                self.navigation.close()
            except Exception as e:
                print(f"[app] Error closing Navigation: {e}")

        if hasattr(self, "temp") and self.temp is not None:
            try:
                self.temp.close()
            except Exception as e:
                print(f"[app] Error closing Temp: {e}")

        if hasattr(self, "librian") and self.librian is not None:
            try:
                self.librian.close()
            except Exception as e:
                print(f"[app] Error closing Librian: {e}")

        if hasattr(self, "movement") and self.movement is not None:
            try:
                self.movement.close()
            except Exception as e:
                print(f"[app] Error closing Movement: {e}")

        if hasattr(self, "knob_controller") and self.knob_controller is not None:
            try:
                self.knob_controller.close()
            except Exception as e:
                print(f"[app] Error closing KnobController: {e}")

        if hasattr(self, "emotion_manager") and self.emotion_manager is not None:
            try:
                self.emotion_manager.close()
            except Exception as e:
                print(f"[app] Error closing EmotionStateManager: {e}")

        print("[app] All subsystems stopped cleanly")

async def main() -> None:
    app = None
    try:
        app = Application()
        await app.run()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        if app is not None:
            app.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("\nApplication stopped")
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"Fatal error: {e}")