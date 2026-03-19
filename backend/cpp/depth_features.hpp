#ifndef SEMIOVIS_DEPTH_FEATURES_HPP
#define SEMIOVIS_DEPTH_FEATURES_HPP

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/// Estimate monocular depth map using MiDaS/DPT ONNX model via OpenCV DNN.
/// Used for perspective analysis, foreground/background separation,
/// and the depth modality marker (Kress & vL, 2006, p.162).
/// Returns H x W float32 normalised depth map (0 = near, 1 = far).
py::array_t<float> estimate_depth_map(
    py::array_t<uint8_t> img_rgb,
    const std::string& model_path = ""
);

#endif // SEMIOVIS_DEPTH_FEATURES_HPP
