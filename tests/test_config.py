import config


class TestConfigConstants:
    def test_stop_hotkey_exists(self):
        assert hasattr(config, "STOP_HOTKEY")

    def test_stop_hotkey_type(self):
        assert isinstance(config.STOP_HOTKEY, str)

    def test_stop_hotkey_value(self):
        assert config.STOP_HOTKEY == "f9"

    def test_shot_radius_exists(self):
        assert hasattr(config, "SHOT_RADIUS")

    def test_shot_radius_type(self):
        assert isinstance(config.SHOT_RADIUS, int)

    def test_shot_radius_range(self):
        assert config.SHOT_RADIUS > 0

    def test_match_confidence_exists(self):
        assert hasattr(config, "MATCH_CONFIDENCE")

    def test_match_confidence_type(self):
        assert isinstance(config.MATCH_CONFIDENCE, float)

    def test_match_confidence_range(self):
        assert 0.0 < config.MATCH_CONFIDENCE < 1.0

    def test_match_search_radius_exists(self):
        assert hasattr(config, "MATCH_SEARCH_RADIUS")

    def test_match_search_radius_type(self):
        assert isinstance(config.MATCH_SEARCH_RADIUS, int)

    def test_match_search_radius_range(self):
        assert config.MATCH_SEARCH_RADIUS > 0

    def test_mouse_move_interval_exists(self):
        assert hasattr(config, "MOUSE_MOVE_INTERVAL_MS")

    def test_mouse_move_interval_type(self):
        assert isinstance(config.MOUSE_MOVE_INTERVAL_MS, int)

    def test_mouse_move_interval_range(self):
        assert config.MOUSE_MOVE_INTERVAL_MS > 0

    def test_pause_hotkey_exists(self):
        assert hasattr(config, "PAUSE_HOTKEY")

    def test_pause_hotkey_type(self):
        assert isinstance(config.PAUSE_HOTKEY, str)

    def test_pause_hotkey_value(self):
        assert config.PAUSE_HOTKEY == "f8"