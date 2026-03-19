#ifndef SEMIOVIS_SALIENCY_HPP
#define SEMIOVIS_SALIENCY_HPP

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/// Compute Spectral Residual saliency map (Hou & Zhang, 2007).
/// Returns H x W float32 normalised saliency map.
py::array_t<float> compute_saliency_spectral(
    py::array_t<uint8_t> img_rgb,
    double scale_factor = 1.0
);

/// Compute Itti-Koch-Niebur saliency map.
/// Uses DoG + colour opponency channels.
/// Returns H x W float32 normalised saliency map.
py::array_t<float> compute_saliency_itti(
    py::array_t<uint8_t> img_rgb,
    double scale_factor = 1.0
);

/// Extract ordered salience peaks as predicted reading path waypoints.
/// Kress & van Leeuwen, 2006, pp.204-208.
/// Returns list of dicts: [{x, y, saliency, label}, ...]
py::list compute_reading_path(
    py::array_t<float> saliency_map,
    int max_waypoints = 10
);

#endif // SEMIOVIS_SALIENCY_HPP
