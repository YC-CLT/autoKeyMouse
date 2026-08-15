import threading
import time
from typing import Callable, Optional

import pyWinhook
import pythoncom
import win32api
import win32con

from config import PAUSE_HOTKEY, STOP_HOTKEY
from engine.logger import get_logger

_log = get_logger("engine.hooks")


class HookManager:
    def __init__(
        self,
        key_callback: Callable[[dict], None],
        mouse_callback: Optional[Callable[[dict], None]] = None,
    ):
        self._hm = pyWinhook.HookManager()
        self._key_callback = key_callback
        self._mouse_callback = mouse_callback
        self._stop_flag = False
        self._pause_flag = False
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _on_keyboard(self, event):
        action = "down" if "down" in event.MessageName.lower() else "up"
        key_name = event.Key or ""
        _log.debug("Key event: key=%s action=%s keycode=%s", key_name, action, event.KeyID)
        if key_name.lower() == STOP_HOTKEY.lower():
            self._stop_flag = True
        if key_name.lower() == PAUSE_HOTKEY.lower():
            self._pause_flag = not self._pause_flag
        self._key_callback({
            "key": key_name,
            "keycode": event.KeyID,
            "action": action,
            "timestamp": time.time(),
        })
        return True

    def _on_mouse(self, event):
        if self._mouse_callback is None:
            return True
        msg_name = event.MessageName.lower()
        if "right" in msg_name:
            action = "right_down" if "down" in msg_name else "right_up"
        elif "middle" in msg_name:
            action = "middle_down" if "down" in msg_name else "middle_up"
        elif "move" in msg_name:
            action = "move"
        elif "wheel" in msg_name:
            action = "wheel_up" if event.Wheel > 0 else "wheel_down"
        else:
            action = "left_down" if "down" in msg_name else "left_up"
        self._mouse_callback({
            "action": action,
            "pos": list(event.Position),
            "wheel": getattr(event, "Wheel", 0),
            "timestamp": time.time(),
        })
        _log.debug("Mouse event: action=%s pos=%s", action, event.Position)
        return True

    def _run(self):
        self._hm.KeyDown = self._on_keyboard
        self._hm.KeyUp = self._on_keyboard
        self._hm.MouseAllButtonsDown = self._on_mouse
        self._hm.MouseAllButtonsUp = self._on_mouse
        self._hm.MouseMove = self._on_mouse
        self._hm.MouseWheel = self._on_mouse

        try:
            self._hm.HookKeyboard()
            self._hm.HookMouse()
        except Exception as e:
            _log.error("Hook startup failed: %s", e)
            raise

        self._running = True
        pythoncom.PumpMessages()

    def start(self):
        self._stop_flag = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        _log.info("Hooks started")

    def stop(self):
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            win32api.PostThreadMessage(self._thread.ident, win32con.WM_QUIT, 0, 0)
            self._thread.join(timeout=2.0)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stop_flag(self) -> bool:
        return self._stop_flag

    @property
    def pause_flag(self) -> bool:
        return self._pause_flag

    def reset_pause(self):
        self._pause_flag = False