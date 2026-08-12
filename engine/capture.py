import os
from typing import Optional

from PIL import ImageGrab


def capture(
    pos: tuple[float, float],
    radius: int,
    output_dir: str,
    shot_index: int,
) -> Optional[str]:
    try:
        screen = ImageGrab.grab()
        screen_w, screen_h = screen.size

        x, y = int(pos[0]), int(pos[1])

        left = max(0, x - radius)
        top = max(0, y - radius)
        right = min(screen_w, x + radius)
        bottom = min(screen_h, y + radius)

        cropped = screen.crop((left, top, right, bottom))

        shots_dir = os.path.join(output_dir, "shots")
        os.makedirs(shots_dir, exist_ok=True)

        filename = f"{shot_index:04d}.png"
        filepath = os.path.join(shots_dir, filename)
        cropped.save(filepath, "PNG")

        return f"shots/{filename}"
    except Exception:
        return None