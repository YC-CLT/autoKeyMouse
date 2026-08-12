import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image

from engine.capture import capture


def _make_screen_image(w, h):
    return Image.fromarray(np.zeros((h, w, 3), dtype=np.uint8))


class TestCapture:
    def test_normal_capture(self):
        screen_img = _make_screen_image(1920, 1080)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("engine.capture.ImageGrab") as mock_grab:
                mock_grab.grab.return_value = screen_img
                result = capture((500, 300), 50, tmpdir, 1)
                assert result == "shots/0001.png"
                assert os.path.exists(os.path.join(tmpdir, "shots", "0001.png"))

    def test_edge_clamping_left_top(self):
        screen_img = _make_screen_image(1920, 1080)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("engine.capture.ImageGrab") as mock_grab:
                mock_grab.grab.return_value = screen_img
                result = capture((10, 10), 50, tmpdir, 2)
                assert result == "shots/0002.png"
                assert os.path.exists(os.path.join(tmpdir, "shots", "0002.png"))

    def test_edge_clamping_right_bottom(self):
        screen_img = _make_screen_image(1920, 1080)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("engine.capture.ImageGrab") as mock_grab:
                mock_grab.grab.return_value = screen_img
                result = capture((1900, 1060), 50, tmpdir, 3)
                assert result == "shots/0003.png"
                assert os.path.exists(os.path.join(tmpdir, "shots", "0003.png"))

    def test_error_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("engine.capture.ImageGrab") as mock_grab:
                mock_grab.grab.side_effect = Exception("screenshot failed")
                result = capture((500, 300), 50, tmpdir, 4)
                assert result is None

    def test_sequential_indices(self):
        screen_img = _make_screen_image(1920, 1080)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("engine.capture.ImageGrab") as mock_grab:
                mock_grab.grab.return_value = screen_img
                r1 = capture((500, 300), 50, tmpdir, 1)
                r2 = capture((600, 400), 50, tmpdir, 2)
                r3 = capture((700, 500), 50, tmpdir, 3)
                assert r1 == "shots/0001.png"
                assert r2 == "shots/0002.png"
                assert r3 == "shots/0003.png"
                assert os.path.exists(os.path.join(tmpdir, "shots", "0001.png"))
                assert os.path.exists(os.path.join(tmpdir, "shots", "0002.png"))
                assert os.path.exists(os.path.join(tmpdir, "shots", "0003.png"))

    def test_creates_shots_directory(self):
        screen_img = _make_screen_image(1920, 1080)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("engine.capture.ImageGrab") as mock_grab:
                mock_grab.grab.return_value = screen_img
                capture((500, 300), 50, tmpdir, 5)
                assert os.path.isdir(os.path.join(tmpdir, "shots"))