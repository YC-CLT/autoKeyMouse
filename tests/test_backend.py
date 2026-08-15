import pytest
from engine.backend import DesktopDriver


class TestDesktopDriverABC:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            DesktopDriver()

    def test_subclass_must_implement_all(self):
        class Incomplete(DesktopDriver):
            def click(self, x, y, button="left"):
                pass

        with pytest.raises(TypeError):
            Incomplete()


class ConcreteDriver(DesktopDriver):
    def click(self, x, y, button="left"):
        pass

    def move(self, x, y):
        pass

    def drag(self, x1, y1, x2, y2, duration_ms=500):
        pass

    def scroll(self, x, y, direction, amount=3):
        pass

    def type_text(self, text):
        pass

    def key_down(self, keycode):
        pass

    def key_up(self, keycode):
        pass

    def get_screen_size(self):
        return (1920, 1080)


class TestConcreteDriver:
    def test_instantiate(self):
        d = ConcreteDriver()
        assert d.get_screen_size() == (1920, 1080)