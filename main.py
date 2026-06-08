import oled
import asyncio

class Application:
    def __init__(self):
        self.tasks: list[asyncio.Task[None]] = []
        self.oled_display = oled.OledDisplay()
        print("[app] Initializing application")
        self.oled_display.display_message("Remote Monitor")

    async def run(self) -> None:
        print("[app] Starting monitor application...")
        
        # Create background tasks
        self.tasks= [
            # asyncio.create_task(self.sensor_reader()),
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