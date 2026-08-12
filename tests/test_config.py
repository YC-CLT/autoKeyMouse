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

    def test_shot_format_exists(self):
        assert hasattr(config, "SHOT_FORMAT")

    def test_shot_format_type(self):
        assert isinstance(config.SHOT_FORMAT, str)

    def test_shot_format_value(self):
        assert config.SHOT_FORMAT == "PNG"

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

    def test_kalman_process_noise_exists(self):
        assert hasattr(config, "KALMAN_PROCESS_NOISE")

    def test_kalman_process_noise_type(self):
        assert isinstance(config.KALMAN_PROCESS_NOISE, float)

    def test_kalman_process_noise_range(self):
        assert config.KALMAN_PROCESS_NOISE > 0

    def test_kalman_measurement_noise_exists(self):
        assert hasattr(config, "KALMAN_MEASURE_NOISE")

    def test_kalman_measurement_noise_type(self):
        assert isinstance(config.KALMAN_MEASURE_NOISE, float)

    def test_kalman_measurement_noise_range(self):
        assert config.KALMAN_MEASURE_NOISE > 0

    def test_kalman_max_consecutive_miss_exists(self):
        assert hasattr(config, "KALMAN_MAX_CONSECUTIVE_MISS")

    def test_kalman_max_consecutive_miss_type(self):
        assert isinstance(config.KALMAN_MAX_CONSECUTIVE_MISS, int)

    def test_kalman_max_consecutive_miss_range(self):
        assert config.KALMAN_MAX_CONSECUTIVE_MISS > 0

    def test_mouse_move_interval_exists(self):
        assert hasattr(config, "MOUSE_MOVE_INTERVAL_MS")

    def test_mouse_move_interval_type(self):
        assert isinstance(config.MOUSE_MOVE_INTERVAL_MS, int)

    def test_mouse_move_interval_range(self):
        assert config.MOUSE_MOVE_INTERVAL_MS > 0