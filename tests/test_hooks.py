import pytest

from engine.hooks import HookManager


class TestHookManagerPause:
    def test_pause_flag_default_false(self):
        hm = HookManager(key_callback=lambda e: None)
        assert hm.pause_flag is False

    def test_reset_pause_sets_false(self):
        hm = HookManager(key_callback=lambda e: None)
        hm._pause_flag = True
        hm.reset_pause()
        assert hm.pause_flag is False

    def test_pause_hotkey_toggles_flag(self):
        hm = HookManager(key_callback=lambda e: None)
        flag_values = []

        class FakeEvent:
            MessageName = "key down"
            Key = "F8"
            KeyID = 119

        def capture(e):
            flag_values.append(hm.pause_flag)

        hm._key_callback = capture
        hm._on_keyboard(FakeEvent)
        assert hm.pause_flag is True
        hm._on_keyboard(FakeEvent)
        assert hm.pause_flag is False

    def test_pause_flag_property_readonly(self):
        hm = HookManager(key_callback=lambda e: None)
        with pytest.raises(AttributeError):
            hm.pause_flag = True