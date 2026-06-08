from typing import List
from PIL import Image
import importlib


def load_frames(mood_name: str) -> List[Image.Image]:
    """Dynamically import moods.<mood_name> and return its frames.
    Falls back to neutral if not found.
    """
    try:
        mod = importlib.import_module(f"moods.{mood_name}")
        return mod.get_frames()
    except Exception:
        # fallback to neutral
        try:
            mod = importlib.import_module("moods.neutral")
            return mod.get_frames()
        except Exception:
            # ultimate fallback: one blank frame
            img = Image.new("1", (128, 64))
            return [img]
