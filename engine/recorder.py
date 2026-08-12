import os
import queue
import threading
import time
from typing import Optional

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
        self._hooks = HookManager()
        self._output_dir = output_dir
        self._events: list[Event] = []
        self._start_time = 0.0
        self._last_event_time = 0.0
        self._shot_index = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_shot: Optional[str] = None
        self._last_mouse_move_time = 0.0
        self._record_move = record_move
        self._move_interval = move_interval
        self._shot_radius = shot_radius
        self._no_shot = no_shot

    def _build_output_dir(self):
        os.makedirs(self._output_dir, exist_ok=True)
        os.makedirs(os.path.join(self._output_dir, "shots"), exist_ok=True)

    def _build_key_event(self, hook_event, delay_ms: int) -> Event:
        action = "down" if "down" in hook_event.MessageName.lower() else "up"
        return Event(
            type="key",
            action=action,
            delay_ms=delay_ms,
            key=hook_event.Key,
            keycode=hook_event.KeyID,
        )

    def _build_mouse_event(self, hook_event, delay_ms: int) -> Event:
        msg_name = hook_event.MessageName.lower()
        if "right" in msg_name:
            action = "rightclick"
        elif "middle" in msg_name:
            action = "middleclick"
        else:
            action = "click"

        pos = list(hook_event.Position)
        if self._no_shot:
            shot = None
        else:
            shot = capture(pos, self._shot_radius, self._output_dir, self._shot_index)
        self._shot_index += 1

        return Event(
            type="mouse",
            action=action,
            delay_ms=delay_ms,
            pos=pos,
            shot=shot,
        )

    def _build_mouse_move_event(self, hook_event, delay_ms: int) -> Event:
        return Event(
            type="mouse",
            action="move",
            delay_ms=delay_ms,
            pos=list(hook_event.Position),
        )

    def _process_events(self):
        while self._running:
            try:
                hook_event = self._hooks.get_event(timeout=0.1)
            except queue.Empty:
                continue

            now = time.time()
            delay_ms = int((now - self._last_event_time) * 1000)
            self._last_event_time = now

            msg_name = hook_event.MessageName.lower()

            if "mouse" in msg_name:
                if "move" in msg_name:
                    if not self._record_move:
                        continue
                    if now - self._last_mouse_move_time < self._move_interval / 1000.0:
                        continue
                    self._last_mouse_move_time = now
                    event = self._build_mouse_move_event(hook_event, delay_ms)
                elif "down" in msg_name:
                    event = self._build_mouse_event(hook_event, delay_ms)
                else:
                    continue
            else:
                event = self._build_key_event(hook_event, delay_ms)

            self._events.append(event)

    def start(self):
        self._build_output_dir()
        self._hooks.start()
        self._start_time = time.time()
        self._last_event_time = self._start_time
        self._last_mouse_move_time = self._start_time
        self._running = True
        self._thread = threading.Thread(target=self._process_events, daemon=True)
        self._thread.start()

    def stop(self) -> Script:
        self._running = False
        self._hooks.stop()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        return self._build_script()

    def _build_script(self) -> Script:
        duration_ms = int((self._last_event_time - self._start_time) * 1000)
        meta = Meta(
            created=time.strftime("%Y-%m-%d %H:%M:%S"),
            duration_ms=duration_ms,
            event_count=len(self._events),
        )
        return Script(version=1, meta=meta, events=list(self._events))