#ifndef SEMIOVIS_COLOR_FEATURES_HPP
#define SEMIOVIS_COLOR_FEATURES_HPP

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/// Compute all 8 modality markers from Kress & van Leeuwen, 2006, pp.160-163.
/// Returns dict with float values [0-1] for each marker:
///   colour_saturation, colour_differentiation, colour_modulation,
///   contextualization, representation, depth, illumination, brightness
py::dict compute_modality_cues(
    py::array_t<uint8_t> img_rgb
);

/// Extract dominant colour palette using k-means clustering.
/// Returns list of dicts: [{rgb: [r,g,b], hex: "#rrggbb", proportion: float}, ...]
py::list extract_color_palette(
    py::array_t<uint8_t> img_rgb,
    int k = 6,
    int max_iter = 100
);

#endif // SEMIOVIS_COLOR_FEATURES_HPP
