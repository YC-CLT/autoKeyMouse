import os
import threading
import time
from typing import Optional

from PIL import ImageGrab

from config import MOUSE_MOVE_INTERVAL_MS, DRAG_THRESHOLD_MS, SHOT_RADIUS, STOP_HOTKEY
from engine.capture import capture
from engine.hooks import HookManager
from engine.logger import get_logger
from engine.script import Event, Meta, Script

_log = get_logger("engine.recorder")


class Recorder:
    def __init__(
        self,
        output_dir: str,
        record_move: bool = True,
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
        self._drag_button: Optional[str] = None
        self._drag_start_time = 0.0
        self._drag_move_count = 0

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
        if data["key"].lower() == STOP_HOTKEY.lower():
            return
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
            if self._drag_button is not None:
                if int(round((now - self._drag_start_time) * 1000)) < DRAG_THRESHOLD_MS:
                    return
                delay_ms = int((now - self._last_event_time) * 1000)
                self._last_event_time = now
                pos = data["pos"]
                rel_pos = list(self._relative_pos(pos[0], pos[1], self._screen_w, self._screen_h))
                event = Event(
                    type="mouse",
                    action=action,
                    delay_ms=delay_ms,
                    pos=rel_pos,
                )
                self._events.append(event)
                self._drag_move_count += 1
                return
            else:
                if not self._record_move:
                    return
                if now - self._last_mouse_move_time < self._move_interval / 1000.0:
                    _log.debug("Mouse move throttled: interval=%dms", self._move_interval)
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
            if "down" in action:
                if action == "left_down":
                    self._drag_button = "left"
                    self._drag_start_time = now
                    self._drag_move_count = 0
                if self._no_shot:
                    shot = None
                else:
                    try:
                        shot = capture(pos, self._shot_radius, self._output_dir, self._shot_index)
                        self._shot_index += 1
                    except Exception as e:
                        _log.error("Screenshot failed: %s", e)
                        shot = None
            else:
                is_drag = False
                if action == "left_up" and self._drag_button == "left":
                    is_drag = (int(round((now - self._drag_start_time) * 1000)) >= DRAG_THRESHOLD_MS
                               and self._drag_move_count > 0)
                self._drag_button = None
                self._drag_start_time = 0.0
                if self._no_shot or not is_drag:
                    shot = None
                else:
                    try:
                        shot = capture(pos, self._shot_radius, self._output_dir, self._shot_index)
                        self._shot_index += 1
                    except Exception as e:
                        _log.error("Screenshot failed: %s", e)
                        shot = None
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
        _log.info("Recording started: dir=%s screen=%dx%d record_move=%s",
                  self._output_dir, self._screen_w, self._screen_h, self._record_move)
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
        script = self._build_script()
        _log.info("Recording stopped: events=%d duration=%dms",
                  script.meta.event_count, script.meta.duration_ms)
        return script

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