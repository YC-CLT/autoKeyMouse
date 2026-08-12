import numpy as np

from engine.matcher import match_template


def _make_test_image(w, h):
    img = np.random.rand(h, w).astype(np.float64)
    return img


class TestMatchTemplate:
    def test_exact_match(self):
        screen = _make_test_image(200, 200)
        template = screen[50:70, 50:70].copy()
        expected = (60, 60)
        result = match_template(screen, template, expected, search_radius=20, confidence_threshold=0.5)
        assert result is not None
        (x, y), conf = result
        assert abs(x - 50) <= 2
        assert abs(y - 50) <= 2
        assert conf > 0.9

    def test_shifted_match(self):
        template = np.random.rand(30, 40).astype(np.float64)
        screen = np.zeros((200, 200), dtype=np.float64)
        screen[60:90, 80:120] = template
        screen += np.random.rand(200, 200).astype(np.float64) * 0.01

        expected = (100, 75)
        result = match_template(screen, template, expected, search_radius=30, confidence_threshold=0.5)
        assert result is not None
        (x, y), conf = result
        assert abs(x - 80) <= 2
        assert abs(y - 60) <= 2
        assert conf > 0.9

    def test_outside_search_radius(self):
        screen = _make_test_image(200, 200)
        template = screen[50:70, 50:70].copy()
        expected = (150, 150)
        result = match_template(screen, template, expected, search_radius=10, confidence_threshold=0.5)
        assert result is None

    def test_low_confidence(self):
        screen = _make_test_image(200, 200)
        template = _make_test_image(30, 40)
        expected = (100, 100)
        result = match_template(screen, template, expected, search_radius=30, confidence_threshold=0.999)
        assert result is None

    def test_same_image_match(self):
        screen = _make_test_image(200, 200)
        template = screen.copy()
        expected = (0, 0)
        result = match_template(screen, template, expected, search_radius=5, confidence_threshold=0.5)
        assert result is not None
        (x, y), conf = result
        assert abs(x - 0) <= 2
        assert abs(y - 0) <= 2
        assert conf > 0.9

    def test_confidence_in_range(self):
        screen = _make_test_image(200, 200)
        template = screen[50:70, 50:70].copy()
        expected = (60, 60)
        result = match_template(screen, template, expected, search_radius=20, confidence_threshold=0.5)
        assert result is not None
        _, conf = result
        assert 0.0 <= conf <= 1.0