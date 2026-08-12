import os
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import win32api
import win32con
import win32clipboard
from PIL import ImageGrab

from config import (
    KALMAN_MAX_CONSECUTIVE_MISS,
    MATCH_CONFIDENCE,
    MATCH_SEARCH_RADIUS,
    STOP_HOTKEY,
)
from engine.hooks import HookManager
from engine.kalman import KalmanFilter
from engine.matcher import match_template
from engine.script import Event, load


@dataclass
class PlayerResult:
    completed_cycles: int = 0
    total_time_ms: int = 0
    stopped_early: bool = False


class Player:
    def __init__(
        self,
        script_dir: str,
        times: int = 1,
        speed: float = 1.0,
        use_match: bool = True,
    ):
        self._script = load(script_dir)
        self._script_dir = script_dir
        self._times = max(1, times)
        self._speed = max(0.01, speed)
        self._use_match = use_match
        self._stop_flag = False
        self._hooks: Optional[HookManager] = None

    def _rel_to_abs(
        self, pos: list[float], screen_w: int, screen_h: int
    ) -> tuple[int, int]:
        return (int(pos[0] * screen_w), int(pos[1] * screen_h))

    def _calc_delay(self, delay_ms: int) -> int:
        return max(1, int(delay_ms / self._speed))

    def _load_shot(self, shot_path: str) -> Optional[np.ndarray]:
        full_path = os.path.join(self._script_dir, shot_path)
        if not os.path.exists(full_path):
            return None
        img = ImageGrab._grayscale_from_argb(
            (0, 0, 0, 0), ImageGrab._load_image(full_path)
        )
        return np.array(img, dtype=np.float64)

    def _capture_screen(self) -> np.ndarray:
        screen = ImageGrab.grab()
        gray = ImageGrab._grayscale_from_argb((0, 0, 0, 0), screen)
        return np.array(gray, dtype=np.float64)

    def _pos_match(
        self,
        event: Event,
        kalman: Optional[KalmanFilter],
        screen_w: int,
        screen_h: int,
    ) -> tuple[int, int]:
        if not self._use_match or event.shot is None or kalman is None:
            return self._rel_to_abs(event.pos, screen_w, screen_h)

        predicted = kalman.predict()
        expected_x, expected_y = int(predicted[0]), int(predicted[1])

        shot = self._load_shot(event.shot)
        if shot is None:
            return self._rel_to_abs(event.pos, screen_w, screen_h)

        screen = self._capture_screen()
        result = match_template(
            screen,
            shot,
            (expected_x, expected_y),
            MATCH_SEARCH_RADIUS,
            MATCH_CONFIDENCE,
        )

        if result is not None:
            (mx, my), _ = result
            kalman.update((float(mx), float(my)))
            return (mx, my)
        else:
            return (int(predicted[0]), int(predicted[1]))

    def _execute_mouse_event(self, event: Event, x: int, y: int):
        win32api.SetCursorPos((x, y))

        action = event.action
        if action == "move":
            return

        flags_map = {
            "click": (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
            "rightclick": (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
            "middleclick": (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP),
        }

        if action in flags_map:
            down_flag, up_flag = flags_map[action]
            win32api.mouse_event(down_flag, 0, 0, 0, 0)
            win32api.mouse_event(up_flag, 0, 0, 0, 0)

    def _execute_key_event(self, event: Event):
        if event.action == "down":
            win32api.keybd_event(event.keycode, 0, 0, 0)
        elif event.action == "up":
            win32api.keybd_event(event.keycode, 0, win32con.KEYEVENTF_KEYUP, 0)

    def _execute_text_event(self, event: Event):
        if event.text:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(event.text)
            win32clipboard.CloseClipboard()

            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord("V"), 0, 0, 0)
            win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

    def _start_stop_listener(self):
        self._hooks = HookManager()
        self._hooks.start()

    def _check_stop(self) -> bool:
        if self._hooks is None:
            return False
        import queue

        try:
            while True:
                hook_event = self._hooks.get_event(timeout=0)
                msg_name = hook_event.MessageName.lower()
                if "key" in msg_name and hook_event.KeyID is not None:
                    key_name = hook_event.Key or ""
                    if key_name.lower() == STOP_HOTKEY.lower():
                        self._stop_flag = True
                        return True
        except queue.Empty:
            pass
        return False

    def _stop_listener(self):
        if self._hooks is not None:
            self._hooks.stop()
            self._hooks = None

    def play(self) -> PlayerResult:
        screen = ImageGrab.grab()
        screen_w, screen_h = screen.size

        self._stop_flag = False
        self._start_stop_listener()

        result = PlayerResult()

        try:
            start_time = time.time()

            for cycle in range(self._times):
                if self._stop_flag or self._check_stop():
                    result.stopped_early = True
                    break

                kalman = KalmanFilter() if self._use_match else None
                if kalman is not None:
                    first_event = self._script.events[0]
                    if first_event.pos is not None:
                        init_x, init_y = self._rel_to_abs(
                            first_event.pos, screen_w, screen_h
                        )
                        kalman.reset((float(init_x), float(init_y)))

                for event in self._script.events:
                    if self._stop_flag or self._check_stop():
                        result.stopped_early = True
                        break

                    delay_ms = self._calc_delay(event.delay_ms)
                    time.sleep(delay_ms / 1000.0)

                    if event.type == "mouse":
                        x, y = self._pos_match(event, kalman, screen_w, screen_h)
                        self._execute_mouse_event(event, x, y)
                    elif event.type == "key":
                        self._execute_key_event(event)
                    elif event.type == "text":
                        self._execute_text_event(event)

                if not result.stopped_early:
                    result.completed_cycles += 1

            result.total_time_ms = int((time.time() - start_time) * 1000)
        finally:
            self._stop_listener()

        return result