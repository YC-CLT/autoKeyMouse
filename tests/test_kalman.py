import numpy as np

from engine.kalman import KalmanFilter


class TestKalmanFilter:
    def test_initial_state(self):
        kf = KalmanFilter()
        kf.reset((100.0, 200.0))
        x, y = kf.position
        assert x == 100.0
        assert y == 200.0
        assert kf.stale_count == 0

    def test_predict_preserves_position(self):
        kf = KalmanFilter()
        kf.reset((100.0, 200.0))
        x, y = kf.predict()
        assert abs(x - 100.0) < 1e-6
        assert abs(y - 200.0) < 1e-6
        assert kf.stale_count == 1

    def test_update_converges(self):
        kf = KalmanFilter(process_noise=1e-4, measurement_noise=1e-4)
        kf.reset((0.0, 0.0))
        for _ in range(20):
            kf.predict()
            kf.update((100.0, 200.0))
        x, y = kf.position
        assert abs(x - 100.0) < 1.0
        assert abs(y - 200.0) < 1.0

    def test_staleness_increments(self):
        kf = KalmanFilter()
        kf.reset((0.0, 0.0))
        assert kf.stale_count == 0
        kf.predict()
        assert kf.stale_count == 1
        kf.predict()
        assert kf.stale_count == 2
        kf.predict()
        assert kf.stale_count == 3

    def test_update_resets_staleness(self):
        kf = KalmanFilter()
        kf.reset((0.0, 0.0))
        kf.predict()
        kf.predict()
        assert kf.stale_count == 2
        kf.update((100.0, 200.0))
        assert kf.stale_count == 0

    def test_reset_clears_staleness(self):
        kf = KalmanFilter()
        kf.reset((0.0, 0.0))
        kf.predict()
        kf.predict()
        kf.reset((50.0, 50.0))
        assert kf.stale_count == 0
        x, y = kf.position
        assert x == 50.0
        assert y == 50.0

    def test_noise_smoothing(self):
        kf = KalmanFilter(process_noise=1e-4, measurement_noise=1.0)
        kf.reset((100.0, 200.0))
        noisy_positions = [(100.0 + np.random.randn() * 5, 200.0 + np.random.randn() * 5) for _ in range(50)]
        for mx, my in noisy_positions:
            kf.predict()
            kf.update((mx, my))
        x, y = kf.position
        assert abs(x - 100.0) < 2.0
        assert abs(y - 200.0) < 2.0

    def test_low_process_noise_smooths_more(self):
        kf_high = KalmanFilter(process_noise=1.0, measurement_noise=1.0)
        kf_low = KalmanFilter(process_noise=1e-4, measurement_noise=1.0)
        kf_high.reset((100.0, 200.0))
        kf_low.reset((100.0, 200.0))
        np.random.seed(42)
        high_positions = []
        low_positions = []
        for _ in range(50):
            m = (100.0 + np.random.randn() * 5, 200.0 + np.random.randn() * 5)
            kf_high.predict()
            kf_high.update(m)
            kf_low.predict()
            kf_low.update(m)
            high_positions.append(kf_high.position[0])
            low_positions.append(kf_low.position[0])
        var_high = np.var(high_positions)
        var_low = np.var(low_positions)
        assert var_low < var_high