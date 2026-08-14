import os
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import win32api
import win32con
import win32clipboard
from PIL import Image, ImageGrab

from config import (
    MATCH_CONFIDENCE,
    MATCH_SEARCH_RADIUS,
)
from engine.hooks import HookManager

from engine.logger import get_logger
from engine.matcher import match_template
from engine.script import Event, load

_log = get_logger("engine.player")


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
        use_match: bool = False,
    ):
        self._script = load(script_dir)
        self._script_dir = script_dir
        self._times = max(1, times)
        self._speed = max(0.01, speed)
        self._use_match = use_match
        self._stop_flag = False
        self._offset = (0, 0)
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
            _log.warning("Shot file not found: %s", full_path)
            return None
        return np.array(Image.open(full_path).convert("L"), dtype=np.float64)

    def _capture_screen(self) -> np.ndarray:
        screen = ImageGrab.grab()
        return np.array(screen.convert("L"), dtype=np.float64)

    def _pos_match(
        self,
        event: Event,
        screen_w: int,
        screen_h: int,
    ) -> tuple[int, int]:
        ox, oy = self._rel_to_abs(event.pos, screen_w, screen_h)

        if not self._use_match or event.shot is None:
            return (ox + self._offset[0], oy + self._offset[1])

        shot = self._load_shot(event.shot)
        if shot is None:
            _log.warning("Shot not found, falling back to original+offset")
            return (ox + self._offset[0], oy + self._offset[1])

        screen = self._capture_screen()

        # 尝试 1: 原始坐标 + offset 周围搜索
        guess_x = ox + self._offset[0]
        guess_y = oy + self._offset[1]
        result = match_template(
            screen, shot, (guess_x, guess_y),
            MATCH_SEARCH_RADIUS, MATCH_CONFIDENCE,
        )
        if result is not None:
            (mx, my), confidence = result
            self._offset = (mx - ox, my - oy)
            _log.debug("Matched at offset: pos=(%d,%d) conf=%.3f", mx, my, confidence)
            return (mx, my)

        # 尝试 2: 纯原始坐标周围搜索（offset 可能过时）
        _log.debug("Offset search failed, trying original position")
        result = match_template(
            screen, shot, (ox, oy),
            MATCH_SEARCH_RADIUS, MATCH_CONFIDENCE,
        )
        if result is not None:
            (mx, my), confidence = result
            self._offset = (mx - ox, my - oy)
            _log.info("Re-matched at original: pos=(%d,%d) conf=%.3f offset=(%d,%d)",
                       mx, my, confidence, self._offset[0], self._offset[1])
            return (mx, my)

        # 尝试 3: 全屏搜索
        _log.warning("Local search failed, trying full-screen search")
        full_radius = max(screen_w, screen_h)
        result = match_template(
            screen, shot, (ox, oy),
            full_radius, MATCH_CONFIDENCE,
        )
        if result is not None:
            (mx, my), confidence = result
            self._offset = (mx - ox, my - oy)
            _log.warning("Full-screen match: pos=(%d,%d) conf=%.3f offset=(%d,%d)",
                          mx, my, confidence, self._offset[0], self._offset[1])
            return (mx, my)

        # 兜底: 原始坐标 + offset
        _log.error("All match strategies failed, falling back to original+offset: (%d,%d)",
                   guess_x, guess_y)
        return (guess_x, guess_y)

    def _execute_mouse_event(self, event: Event, x: int, y: int):
        win32api.SetCursorPos((x, y))

        action = event.action
        if action == "move":
            return

        flags_map = {
            "left_down": (win32con.MOUSEEVENTF_LEFTDOWN,),
            "left_up": (win32con.MOUSEEVENTF_LEFTUP,),
            "right_down": (win32con.MOUSEEVENTF_RIGHTDOWN,),
            "right_up": (win32con.MOUSEEVENTF_RIGHTUP,),
            "middle_down": (win32con.MOUSEEVENTF_MIDDLEDOWN,),
            "middle_up": (win32con.MOUSEEVENTF_MIDDLEUP,),
            "wheel_up": (win32con.MOUSEEVENTF_WHEEL, 120),
            "wheel_down": (win32con.MOUSEEVENTF_WHEEL, -120),
        }

        if action in flags_map:
            flags = flags_map[action]
            if action in ("wheel_up", "wheel_down"):
                flag, delta = flags
                win32api.mouse_event(flag, 0, 0, delta, 0)
            else:
                flag = flags[0]
                win32api.mouse_event(flag, 0, 0, 0, 0)

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
        self._hooks = HookManager(key_callback=lambda d: None)
        self._hooks.start()

    def _check_stop(self) -> bool:
        if self._hooks is None:
            return False
        if self._hooks.stop_flag:
            self._stop_flag = True
            return True
        return False

    def _stop_listener(self):
        if self._hooks is not None:
            self._hooks.stop()
            self._hooks = None

    def play(self) -> PlayerResult:
        screen = ImageGrab.grab()
        screen_w, screen_h = screen.size
        _log.info("Playback started: script=%s times=%d speed=%.1f screen=%dx%d match=%s",
                  self._script_dir, self._times, self._speed, screen_w, screen_h, self._use_match)

        self._stop_flag = False
        self._start_stop_listener()

        result = PlayerResult()

        try:
            start_time = time.time()

            for cycle in range(self._times):
                if self._stop_flag or self._check_stop():
                    result.stopped_early = True
                    break

                _log.info("Cycle %d/%d starting", cycle + 1, self._times)

                self._offset = (0, 0)

                for event in self._script.events:
                    if self._stop_flag or self._check_stop():
                        result.stopped_early = True
                        break

                    delay_ms = self._calc_delay(event.delay_ms)
                    time.sleep(delay_ms / 1000.0)

                    _log.debug("Event: type=%s action=%s pos=%s delay=%dms",
                               event.type, event.action, event.pos, event.delay_ms)

                    try:
                        if event.type == "mouse":
                            x, y = self._pos_match(event, screen_w, screen_h)
                            _log.info("Mouse event: action=%s pos=(%d,%d)", event.action, x, y)
                            self._execute_mouse_event(event, x, y)
                        elif event.type == "key":
                            _log.info("Key event: key=%s action=%s", event.key, event.action)
                            self._execute_key_event(event)
                        elif event.type == "text":
                            _log.info("Text event: len=%d", len(event.text or ""))
                            self._execute_text_event(event)
                    except Exception as e:
                        _log.error("Event execution failed: type=%s action=%s error=%s",
                                   event.type, event.action, e)
                        raise

                if not result.stopped_early:
                    _log.info("Cycle %d/%d completed", cycle + 1, self._times)
                    result.completed_cycles += 1

            result.total_time_ms = int((time.time() - start_time) * 1000)
        finally:
            self._stop_listener()

        _log.info("Playback finished: cycles=%d/%d time=%dms stopped_early=%s",
                  result.completed_cycles, self._times, result.total_time_ms, result.stopped_early)
        return result