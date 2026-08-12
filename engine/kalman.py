import numpy as np

from config import KALMAN_PROCESS_NOISE, KALMAN_MEASURE_NOISE


class KalmanFilter:
    def __init__(
        self,
        process_noise: float = KALMAN_PROCESS_NOISE,
        measurement_noise: float = KALMAN_MEASURE_NOISE,
    ):
        self._Q = np.array([[process_noise, 0], [0, process_noise]], dtype=np.float64)
        self._R = np.array([[measurement_noise, 0], [0, measurement_noise]], dtype=np.float64)
        self._H = np.eye(2, dtype=np.float64)
        self._x = np.zeros(2, dtype=np.float64)
        self._P = np.eye(2, dtype=np.float64)
        self._stale_count = 0

    def reset(self, initial_pos: tuple[float, float]):
        self._x = np.array(initial_pos, dtype=np.float64)
        self._P = np.eye(2, dtype=np.float64)
        self._stale_count = 0

    def predict(self) -> tuple[float, float]:
        self._P = self._P + self._Q
        self._stale_count += 1
        return (float(self._x[0]), float(self._x[1]))

    def update(self, measurement: tuple[float, float]):
        z = np.array(measurement, dtype=np.float64)
        y = z - self._H @ self._x
        S = self._H @ self._P @ self._H.T + self._R
        K = self._P @ self._H.T @ np.linalg.inv(S)
        self._x = self._x + K @ y
        self._P = (np.eye(2, dtype=np.float64) - K @ self._H) @ self._P
        self._stale_count = 0

    @property
    def position(self) -> tuple[float, float]:
        return (float(self._x[0]), float(self._x[1]))

    @property
    def stale_count(self) -> int:
        return self._stale_count