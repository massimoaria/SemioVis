#ifndef SEMIOVIS_SPATIAL_GRID_HPP
#define SEMIOVIS_SPATIAL_GRID_HPP

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/// Compute zonal statistics for semiotic spatial grid.
/// Divides the image into n_cols x n_rows zones and computes per-zone
/// saliency, visual weight, colour temperature, edge density, etc.
/// Returns list of zone dicts with semiotic labels.
py::list compute_spatial_zones(
    py::array_t<float> saliency_map,
    py::array_t<uint8_t> img_rgb,
    int n_cols = 3,
    int n_rows = 3
);

#endif // SEMIOVIS_SPATIAL_GRID_HPP
