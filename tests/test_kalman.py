import numpy as np

from engine.kalman import PositionKalman


class TestPositionKalman:
    def test_initial_state(self):
        kf = PositionKalman(100.0, 200.0)
        x, y = kf.predict()
        assert x == 100.0
        assert y == 200.0
        assert kf._stale_count == 1

    def test_predict_preserves_position(self):
        kf = PositionKalman(100.0, 200.0)
        x, y = kf.predict()
        assert abs(x - 100.0) < 1e-6
        assert abs(y - 200.0) < 1e-6
        assert kf._stale_count == 1

    def test_update_converges(self):
        kf = PositionKalman(0.0, 0.0)
        for _ in range(20):
            kf.predict()
            kf.update(np.array([100.0, 200.0]))
        x, y = kf.predict()
        assert abs(x - 100.0) < 1.0
        assert abs(y - 200.0) < 1.0

    def test_staleness_increments(self):
        kf = PositionKalman(0.0, 0.0)
        assert kf._stale_count == 0
        kf.predict()
        assert kf._stale_count == 1
        kf.predict()
        assert kf._stale_count == 2
        kf.predict()
        assert kf._stale_count == 3

    def test_update_resets_staleness(self):
        kf = PositionKalman(0.0, 0.0)
        kf.predict()
        kf.predict()
        assert kf._stale_count == 2
        kf.update(np.array([100.0, 200.0]))
        assert kf._stale_count == 0

    def test_is_stale_after_max_misses(self):
        kf = PositionKalman(0.0, 0.0)
        assert not kf.is_stale()
        for _ in range(5):
            kf.predict()
        assert kf._stale_count == 5
        assert kf.is_stale()

    def test_noise_smoothing(self):
        kf = PositionKalman(100.0, 200.0)
        np.random.seed(42)
        for _ in range(50):
            mx = 100.0 + np.random.randn() * 5
            my = 200.0 + np.random.randn() * 5
            kf.predict()
            kf.update(np.array([mx, my]))
        x, y = kf.predict()
        assert abs(x - 100.0) < 2.0
        assert abs(y - 200.0) < 2.0

    def test_predict_returns_ndarray(self):
        kf = PositionKalman(50.0, 75.0)
        result = kf.predict()
        assert isinstance(result, np.ndarray)
        assert result.shape == (2,)

    def test_update_returns_ndarray(self):
        kf = PositionKalman(50.0, 75.0)
        result = kf.update(np.array([60.0, 80.0]))
        assert isinstance(result, np.ndarray)
        assert result.shape == (2,)
        assert abs(result[0] - 60.0) < 10.0
        assert abs(result[1] - 80.0) < 10.0