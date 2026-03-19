#ifndef SEMIOVIS_TEXTURE_FEATURES_HPP
#define SEMIOVIS_TEXTURE_FEATURES_HPP

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/// Compute texture features using Gabor filterbank and Local Binary Patterns (LBP).
/// Returns dict with texture descriptors: {gabor_energy, gabor_orientations,
///   lbp_histogram, texture_homogeneity, texture_contrast, dominant_orientation}
py::dict compute_texture_features(
    py::array_t<uint8_t> img_gray
);

#endif // SEMIOVIS_TEXTURE_FEATURES_HPP
