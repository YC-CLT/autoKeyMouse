from typing import Optional

import numpy as np

from engine.logger import get_logger

_log = get_logger("engine.matcher")

TemplateMatchResult = tuple[tuple[int, int], float]


def match_template(
    screen: np.ndarray,
    template: np.ndarray,
    expected_pos: tuple[int, int],
    search_radius: int,
    confidence_threshold: float,
) -> Optional[TemplateMatchResult]:
    h, w = template.shape
    H, W = screen.shape
    n = float(h * w)

    ex, ey = expected_pos

    roi_x1 = max(0, ex - search_radius)
    roi_y1 = max(0, ey - search_radius)
    roi_x2 = min(W, ex + search_radius + w)
    roi_y2 = min(H, ey + search_radius + h)

    roi = screen[roi_y1:roi_y2, roi_x1:roi_x2].copy()
    roi_h, roi_w = roi.shape

    if roi_h < h or roi_w < w:
        _log.warning("ROI too small for matching: roi=%dx%d template=%dx%d", roi_w, roi_h, w, h)
        return None

    sum_t = float(np.sum(template))
    template_zero_mean = template - sum_t / n
    template_norm = np.sqrt(np.sum(template_zero_mean ** 2))
    if template_norm < 1e-12:
        return None

    template_padded = np.zeros_like(roi)
    template_padded[:h, :w] = template_zero_mean

    fft_roi = np.fft.fft2(roi)
    fft_tpl = np.fft.fft2(template_padded)
    cross_corr = np.fft.ifft2(fft_roi * np.conj(fft_tpl)).real

    integral = np.zeros((roi_h + 1, roi_w + 1), dtype=np.float64)
    integral[1:, 1:] = np.cumsum(np.cumsum(roi, axis=0), axis=1)

    integral_sq = np.zeros((roi_h + 1, roi_w + 1), dtype=np.float64)
    integral_sq[1:, 1:] = np.cumsum(np.cumsum(roi ** 2, axis=0), axis=1)

    best_conf = -1.0
    best_x = 0
    best_y = 0

    valid_rows = roi_h - h + 1
    valid_cols = roi_w - w + 1

    for i in range(valid_rows):
        local_sum = integral[i + h, w:w + valid_cols] - integral[i, w:w + valid_cols]
        local_sum -= integral[i + h, :valid_cols] - integral[i, :valid_cols]

        local_sum_sq = integral_sq[i + h, w:w + valid_cols] - integral_sq[i, w:w + valid_cols]
        local_sum_sq -= integral_sq[i + h, :valid_cols] - integral_sq[i, :valid_cols]

        local_mean = local_sum / n
        local_var = np.maximum(local_sum_sq / n - local_mean ** 2, 0.0)
        local_std = np.sqrt(local_var)

        ncc = cross_corr[i, :valid_cols] / (np.sqrt(n) * local_std * template_norm + 1e-12)

        row_best_idx = np.argmax(ncc)
        row_best_conf = ncc[row_best_idx]

        if row_best_conf > best_conf:
            best_conf = row_best_conf
            best_x = row_best_idx
            best_y = i

    screen_x = roi_x1 + best_x
    screen_y = roi_y1 + best_y

    dx = screen_x - ex
    dy = screen_y - ey
    if abs(dx) > search_radius or abs(dy) > search_radius:
        return None

    if best_conf < confidence_threshold:
        _log.debug("Confidence below threshold: %.3f < %.3f", best_conf, confidence_threshold)
        return None

    return ((screen_x, screen_y), float(best_conf))