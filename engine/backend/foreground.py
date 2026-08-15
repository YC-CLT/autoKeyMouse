import win32api
import win32con
import win32clipboard
from PIL import ImageGrab

from engine.backend.base import DesktopDriver


class ForegroundDriver(DesktopDriver):
    def click(self, x: int, y: int, button: str = "left") -> None:
        win32api.SetCursorPos((x, y))
        flags_map = {
            "left": (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
            "right": (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
            "middle": (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP),
        }
        if button in flags_map:
            down, up = flags_map[button]
            win32api.mouse_event(down, 0, 0, 0, 0)
            win32api.mouse_event(up, 0, 0, 0, 0)

    def move(self, x: int, y: int) -> None:
        win32api.SetCursorPos((x, y))

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 500) -> None:
        win32api.SetCursorPos((x1, y1))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.SetCursorPos((x2, y2))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def scroll(self, x: int, y: int, direction: str, amount: int = 3) -> None:
        win32api.SetCursorPos((x, y))
        delta = win32con.WHEEL_DELTA * amount if direction == "up" else -win32con.WHEEL_DELTA * amount
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, delta, 0)

    def type_text(self, text: str) -> None:
        if not text:
            return
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

    def key_down(self, keycode: int) -> None:
        win32api.keybd_event(keycode, 0, 0, 0)

    def key_up(self, keycode: int) -> None:
        win32api.keybd_event(keycode, 0, win32con.KEYEVENTF_KEYUP, 0)

    def get_screen_size(self) -> tuple[int, int]:
        screen = ImageGrab.grab()
        return screen.size

    def mouse_event(self, x: int, y: int, action: str) -> None:
        win32api.SetCursorPos((x, y))
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

    def key_event(self, keycode: int, action: str) -> None:
        if action == "down":
            win32api.keybd_event(keycode, 0, 0, 0)
        elif action == "up":
            win32api.keybd_event(keycode, 0, win32con.KEYEVENTF_KEYUP, 0)

    def text_event(self, text: str) -> None:
        if not text:
            return
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)