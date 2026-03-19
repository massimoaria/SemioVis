#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <cmath>

#include "saliency.hpp"
#include "vectors.hpp"
#include "spatial_grid.hpp"
#include "color_features.hpp"
#include "texture_features.hpp"
#include "depth_features.hpp"

namespace py = pybind11;

PYBIND11_MODULE(semiovis_core, m) {
    m.doc() = "SemioVis — C++ core via pybind11. "
              "Implements low-level computer vision algorithms for semiotic image analysis "
              "based on Kress & van Leeuwen (2006).";

    // --- Saliency ---

    m.def("compute_saliency_spectral", &compute_saliency_spectral,
          py::arg("img_rgb"),
          py::arg("scale_factor") = 1.0,
          "Spectral Residual saliency map (Hou & Zhang, 2007). "
          "Accepts H x W x 3 uint8 RGB array. Returns H x W float32 normalised [0, 1].");

    m.def("compute_saliency_itti", &compute_saliency_itti,
          py::arg("img_rgb"),
          py::arg("scale_factor") = 1.0,
          "Itti-Koch-Niebur saliency map using DoG + colour opponency. "
          "Accepts H x W x 3 uint8 RGB array. Returns H x W float32 normalised [0, 1].");

    m.def("compute_reading_path", &compute_reading_path,
          py::arg("saliency_map"),
          py::arg("max_waypoints") = 10,
          "Extract ordered salience peaks as predicted reading path waypoints "
          "(Kress & van Leeuwen, 2006, pp.204-208). "
          "Accepts H x W float32 saliency map. Returns list of {x, y, saliency, label} dicts.");

    // --- Vectors ---

    m.def("detect_vectors", &detect_vectors,
          py::arg("img_gray"),
          py::arg("rho") = 1.0,
          py::arg("theta") = M_PI / 180.0,
          py::arg("threshold") = 100,
          py::arg("min_line_length") = 50.0,
          py::arg("max_line_gap") = 10.0,
          "Probabilistic Hough Lines for vector detection. "
          "Accepts H x W uint8 grayscale array. "
          "Returns list of {x1, y1, x2, y2, angle, strength, direction} dicts.");

    m.def("estimate_vanishing_point", &estimate_vanishing_point,
          py::arg("img_gray"),
          "RANSAC vanishing point estimation from Hough lines. "
          "Accepts H x W uint8 grayscale array. "
          "Returns {vp_x, vp_y, v_angle, h_angle} dict.");

    m.def("detect_framing_lines", &detect_framing_lines,
          py::arg("img_gray"),
          py::arg("threshold1") = 50.0,
          py::arg("threshold2") = 150.0,
          "Canny + Hough framing line detection (Kress & vL, pp.203-204). "
          "Accepts H x W uint8 grayscale array. "
          "Returns {framing_score, lines} dict.");

    // --- Spatial Grid ---

    m.def("compute_spatial_zones", &compute_spatial_zones,
          py::arg("saliency_map"),
          py::arg("img_rgb"),
          py::arg("n_cols") = 3,
          py::arg("n_rows") = 3,
          "Zonal statistics for semiotic grid (Kress & vL, Ch. 6). "
          "Accepts saliency map (H x W float32) and RGB image (H x W x 3 uint8). "
          "Returns list of zone dicts with position labels and visual weight.");

    // --- Colour Features ---

    m.def("compute_modality_cues", &compute_modality_cues,
          py::arg("img_rgb"),
          "All 8 modality markers from Kress & vL, 2006, pp.160-163: "
          "colour_saturation, colour_differentiation, colour_modulation, "
          "contextualization, representation, depth, illumination, brightness. "
          "Accepts H x W x 3 uint8 RGB array. Returns dict with float values [0-1].");

    m.def("extract_color_palette", &extract_color_palette,
          py::arg("img_rgb"),
          py::arg("k") = 6,
          py::arg("max_iter") = 100,
          "k-means colour palette extraction. "
          "Accepts H x W x 3 uint8 RGB array. "
          "Returns list of {rgb, hex, proportion} dicts sorted by proportion.");

    // --- Texture Features ---

    m.def("compute_texture_features", &compute_texture_features,
          py::arg("img_gray"),
          "Gabor filterbank + LBP texture analysis. "
          "Accepts H x W uint8 grayscale array. "
          "Returns dict with gabor_energy, lbp_histogram, texture_homogeneity, etc.");

    // --- Depth Features ---

    m.def("estimate_depth_map", &estimate_depth_map,
          py::arg("img_rgb"),
          py::arg("model_path") = "",
          "Monocular depth estimation via MiDaS/DPT ONNX model. "
          "Used for perspective analysis and depth modality marker (p.162). "
          "Accepts H x W x 3 uint8 RGB array. Returns H x W float32 normalised depth map.");
}
