import queue
import threading
from typing import Optional

import pyWinhook
import pythoncom
import win32api
import win32con


class HookManager:
    def __init__(self):
        self._hm = pyWinhook.HookManager()
        self._event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _keyboard_callback(self, event):
        self._event_queue.put(event)
        return True

    def _mouse_callback(self, event):
        self._event_queue.put(event)
        return True

    def _run(self):
        self._hm.KeyDown = self._keyboard_callback
        self._hm.KeyUp = self._keyboard_callback
        self._hm.MouseAllButtonsDown = self._mouse_callback
        self._hm.MouseAllButtonsUp = self._mouse_callback
        self._hm.MouseMove = self._mouse_callback

        self._hm.HookKeyboard()
        self._hm.HookMouse()

        self._running = True
        pythoncom.PumpMessages()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            win32api.PostThreadMessage(self._thread.ident, win32con.WM_QUIT, 0, 0)
            self._thread.join(timeout=2.0)

    def get_event(self, timeout: Optional[float] = None):
        return self._event_queue.get(timeout=timeout)

    @property
    def event_queue(self) -> queue.Queue:
        return self._event_queue

    @property
    def is_running(self) -> bool:
        return self._running