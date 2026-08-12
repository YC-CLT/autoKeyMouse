import numpy as np

from config import (
    KALMAN_MAX_CONSECUTIVE_MISS,
    KALMAN_MEASURE_NOISE,
    KALMAN_PROCESS_NOISE,
)


class PositionKalman:
    def __init__(self, x: float, y: float):
        self._Q = np.array(
            [[KALMAN_PROCESS_NOISE, 0], [0, KALMAN_PROCESS_NOISE]], dtype=np.float64
        )
        self._R = np.array(
            [[KALMAN_MEASURE_NOISE, 0], [0, KALMAN_MEASURE_NOISE]], dtype=np.float64
        )
        self._H = np.eye(2, dtype=np.float64)
        self._x = np.array([x, y], dtype=np.float64)
        self._P = np.eye(2, dtype=np.float64)
        self._stale_count = 0

    def predict(self) -> np.ndarray:
        self._P = self._P + self._Q
        self._stale_count += 1
        return self._x.copy()

    def update(self, measurement: np.ndarray) -> np.ndarray:
        z = np.asarray(measurement, dtype=np.float64)
        y = z - self._H @ self._x
        S = self._H @ self._P @ self._H.T + self._R
        K = self._P @ self._H.T @ np.linalg.inv(S)
        self._x = self._x + K @ y
        self._P = (np.eye(2, dtype=np.float64) - K @ self._H) @ self._P
        self._stale_count = 0
        return self._x.copy()

    def is_stale(self) -> bool:
        return self._stale_count >= KALMAN_MAX_CONSECUTIVE_MISS