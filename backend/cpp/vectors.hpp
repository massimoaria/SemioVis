#ifndef SEMIOVIS_VECTORS_HPP
#define SEMIOVIS_VECTORS_HPP

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <cmath>

namespace py = pybind11;

/// Detect vectors using Probabilistic Hough Line Transform.
/// Returns list of dicts: [{x1, y1, x2, y2, angle, strength, direction}, ...]
py::list detect_vectors(
    py::array_t<uint8_t> img_gray,
    double rho = 1.0,
    double theta = M_PI / 180.0,
    int threshold = 100,
    double min_line_length = 50.0,
    double max_line_gap = 10.0
);

/// Estimate vanishing point via RANSAC on Hough lines.
/// Returns dict: {vp_x, vp_y, v_angle, h_angle}
py::dict estimate_vanishing_point(
    py::array_t<uint8_t> img_gray
);

/// Detect framing lines using Canny edge detection + Hough transform.
/// Returns dict: {framing_score (0-1), lines: [...]}
py::dict detect_framing_lines(
    py::array_t<uint8_t> img_gray,
    double threshold1 = 50.0,
    double threshold2 = 150.0
);

#endif // SEMIOVIS_VECTORS_HPP
