import os
import threading
import time
from typing import Optional

from PIL import ImageGrab

from config import MOUSE_MOVE_INTERVAL_MS, SHOT_RADIUS
from engine.capture import capture
from engine.hooks import HookManager
from engine.script import Event, Meta, Script


class Recorder:
    def __init__(
        self,
        output_dir: str,
        record_move: bool = False,
        move_interval: int = MOUSE_MOVE_INTERVAL_MS,
        shot_radius: int = SHOT_RADIUS,
        no_shot: bool = False,
    ):
        self._output_dir = output_dir
        self._events: list[Event] = []
        self._start_time = 0.0
        self._last_event_time = 0.0
        self._shot_index = 0
        self._running = False
        self._last_shot: Optional[str] = None
        self._last_mouse_move_time = 0.0
        self._record_move = record_move
        self._move_interval = move_interval
        self._shot_radius = shot_radius
        self._no_shot = no_shot
        self._screen_w = 0
        self._screen_h = 0
        self._hooks: Optional[HookManager] = None

    def _build_output_dir(self):
        os.makedirs(self._output_dir, exist_ok=True)
        os.makedirs(os.path.join(self._output_dir, "shots"), exist_ok=True)

    def _relative_pos(
        self, x: float, y: float, screen_w: int, screen_h: int
    ) -> tuple[float, float]:
        return (x / screen_w, y / screen_h)

    def _map_mouse_action(self, win_msg: str) -> Optional[str]:
        msg = win_msg.lower()
        if "right" in msg:
            return "right_down" if "down" in msg else "right_up"
        if "middle" in msg:
            return "middle_down" if "down" in msg else "middle_up"
        if "left" in msg or "mouse" in msg:
            return "left_down" if "down" in msg else "left_up"
        return None

    def _on_key_callback(self, data: dict):
        now = time.time()
        delay_ms = int((now - self._last_event_time) * 1000)
        self._last_event_time = now
        event = Event(
            type="key",
            action=data["action"],
            delay_ms=delay_ms,
            key=data["key"],
            keycode=data["keycode"],
        )
        self._events.append(event)

    def _on_mouse_callback(self, data: dict):
        now = time.time()
        action = data["action"]

        if action == "move":
            if not self._record_move:
                return
            if now - self._last_mouse_move_time < self._move_interval / 1000.0:
                return
            self._last_mouse_move_time = now

        delay_ms = int((now - self._last_event_time) * 1000)
        self._last_event_time = now

        pos = data["pos"]
        rel_pos = list(self._relative_pos(pos[0], pos[1], self._screen_w, self._screen_h))

        if action == "move":
            event = Event(
                type="mouse",
                action=action,
                delay_ms=delay_ms,
                pos=rel_pos,
            )
        elif action == "wheel_up" or action == "wheel_down":
            event = Event(
                type="mouse",
                action=action,
                delay_ms=delay_ms,
                pos=rel_pos,
            )
        else:
            if self._no_shot:
                shot = None
            else:
                shot = capture(pos, self._shot_radius, self._output_dir, self._shot_index)
            self._shot_index += 1
            event = Event(
                type="mouse",
                action=action,
                delay_ms=delay_ms,
                pos=rel_pos,
                shot=shot,
            )

        self._events.append(event)

    def start(self):
        self._build_output_dir()
        screen = ImageGrab.grab()
        self._screen_w, self._screen_h = screen.size
        self._hooks = HookManager(
            key_callback=self._on_key_callback,
            mouse_callback=self._on_mouse_callback,
        )
        self._hooks.start()
        self._start_time = time.time()
        self._last_event_time = self._start_time
        self._last_mouse_move_time = self._start_time
        self._running = True

    def stop(self) -> Script:
        self._running = False
        if self._hooks is not None:
            self._hooks.stop()
            self._hooks = None
        return self._build_script()

    def is_recording(self) -> bool:
        return self._running

    def _build_script(self) -> Script:
        duration_ms = int((self._last_event_time - self._start_time) * 1000)
        meta = Meta(
            created=time.strftime("%Y-%m-%d %H:%M:%S"),
            screen=[self._screen_w, self._screen_h],
            duration_ms=duration_ms,
            event_count=len(self._events),
        )
        return Script(version=1, meta=meta, events=list(self._events))