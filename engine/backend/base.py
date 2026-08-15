from abc import ABC, abstractmethod


class DesktopDriver(ABC):
    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> None:
        ...

    @abstractmethod
    def move(self, x: int, y: int) -> None:
        ...

    @abstractmethod
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 500) -> None:
        ...

    @abstractmethod
    def scroll(self, x: int, y: int, direction: str, amount: int = 3) -> None:
        ...

    @abstractmethod
    def type_text(self, text: str) -> None:
        ...

    @abstractmethod
    def key_down(self, keycode: int) -> None:
        ...

    @abstractmethod
    def key_up(self, keycode: int) -> None:
        ...

    @abstractmethod
    def get_screen_size(self) -> tuple[int, int]:
        ...