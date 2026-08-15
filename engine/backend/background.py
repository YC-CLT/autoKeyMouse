import asyncio
from cua_driver import (
    ClickButton,
    ClickInput,
    CuaDriver,
    DesktopScope,
    DragInput,
    GetScreenSizeInput,
    MoveCursorInput,
    PressKeyInput,
    ScrollDirection,
    ScrollInput,
    TypeTextInput,
)

import json

from engine.backend.base import DesktopDriver


class BackgroundDriver(DesktopDriver):
    def __init__(self):
        self._driver = CuaDriver.create()

    def click(self, x: int, y: int, button: str = "left") -> None:
        btn_map = {
            "left": ClickButton.LEFT,
            "right": ClickButton.RIGHT,
            "middle": ClickButton.MIDDLE,
        }
        asyncio.run(self._driver.click(ClickInput(
            x=x, y=y,
            scope=DesktopScope.DESKTOP,
            session=None,
            button=btn_map.get(button, ClickButton.LEFT),
        )))

    def move(self, x: int, y: int) -> None:
        asyncio.run(self._driver.move_cursor(MoveCursorInput(
            x=x, y=y,
            scope=DesktopScope.DESKTOP,
            session=None,
        )))

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 500) -> None:
        asyncio.run(self._driver.drag(DragInput(
            from_x=x1, from_y=y1,
            to_x=x2, to_y=y2,
            scope=DesktopScope.DESKTOP,
            session=None,
            duration_ms=duration_ms,
        )))

    def scroll(self, x: int, y: int, direction: str, amount: int = 3) -> None:
        dir_map = {
            "up": ScrollDirection.UP,
            "down": ScrollDirection.DOWN,
        }
        asyncio.run(self._driver.scroll(ScrollInput(
            x=x, y=y,
            direction=dir_map.get(direction, ScrollDirection.UP),
            scope=DesktopScope.DESKTOP,
            session=None,
            amount=amount,
        )))

    def type_text(self, text: str) -> None:
        asyncio.run(self._driver.type_text(TypeTextInput(
            text=text,
            scope=DesktopScope.DESKTOP,
            session=None,
        )))

    def key_down(self, keycode: int) -> None:
        asyncio.run(self._driver.press_key(PressKeyInput(
            key=str(keycode),
            scope=DesktopScope.DESKTOP,
            session=None,
        )))

    def key_up(self, keycode: int) -> None:
        pass

    def get_screen_size(self) -> tuple[int, int]:
        result = asyncio.run(self._driver.get_screen_size(
            GetScreenSizeInput(session=None)
        ))
        data = json.loads(result.structured_json)
        return (data["width"], data["height"])

    def mouse_event(self, x: int, y: int, action: str) -> None:
        if action == "move":
            self.move(x, y)
        elif action == "wheel_up":
            self.scroll(x, y, "up", 1)
        elif action == "wheel_down":
            self.scroll(x, y, "down", 1)
        elif action in ("left_down", "left_up"):
            self.click(x, y, "left")
        elif action in ("right_down", "right_up"):
            self.click(x, y, "right")
        elif action in ("middle_down", "middle_up"):
            self.click(x, y, "middle")

    def key_event(self, keycode: int, action: str) -> None:
        if action == "down":
            self.key_down(keycode)

    def text_event(self, text: str) -> None:
        self.type_text(text)