"""Tests for the C++ core module (semiovis_core via pybind11)."""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add C++ build dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "cpp" / "build"))
import semiovis_core as sc


@pytest.fixture
def sample_rgb():
    """A simple 200x300 RGB test image with some structure."""
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    # Gradient background
    for y in range(200):
        img[y, :, 0] = int(255 * y / 200)
        img[y, :, 2] = int(255 * (1 - y / 200))
    # White rectangle
    img[50:150, 80:220] = [255, 255, 255]
    # Dark circle region
    for y in range(200):
        for x in range(300):
            if (x - 150) ** 2 + (y - 100) ** 2 < 30 ** 2:
                img[y, x] = [50, 50, 50]
    return img


@pytest.fixture
def sample_gray(sample_rgb):
    import cv2
    return cv2.cvtColor(sample_rgb, cv2.COLOR_RGB2GRAY)


class TestSaliency:
    def test_spectral_output_shape(self, sample_rgb):
        sal = sc.compute_saliency_spectral(sample_rgb)
        assert sal.shape == (200, 300)

    def test_spectral_range(self, sample_rgb):
        sal = sc.compute_saliency_spectral(sample_rgb)
        assert sal.min() >= -1e-6  # floating point tolerance
        assert sal.max() <= 1.0 + 1e-6

    def test_itti_output_shape(self, sample_rgb):
        sal = sc.compute_saliency_itti(sample_rgb)
        assert sal.shape == (200, 300)

    def test_itti_range(self, sample_rgb):
        sal = sc.compute_saliency_itti(sample_rgb)
        assert sal.max() <= 1.0

    def test_scale_factor(self, sample_rgb):
        sal = sc.compute_saliency_spectral(sample_rgb, scale_factor=0.5)
        assert sal.shape == (200, 300)  # output always matches input size


class TestVectors:
    def test_detect_vectors_returns_list(self, sample_gray):
        result = sc.detect_vectors(sample_gray)
        assert isinstance(result, list)

    def test_vector_dict_keys(self, sample_gray):
        result = sc.detect_vectors(sample_gray, threshold=50, min_line_length=20.0)
        if result:
            keys = set(result[0].keys())
            assert {"x1", "y1", "x2", "y2", "angle", "strength", "direction"} <= keys

    def test_vector_coordinates_normalized(self, sample_gray):
        result = sc.detect_vectors(sample_gray, threshold=50, min_line_length=20.0)
        for v in result:
            assert 0.0 <= v["x1"] <= 1.0
            assert 0.0 <= v["y1"] <= 1.0

    def test_vanishing_point_dict(self, sample_gray):
        vp = sc.estimate_vanishing_point(sample_gray)
        assert isinstance(vp, dict)
        assert "vp_x" in vp
        assert "v_angle" in vp

    def test_framing_lines_dict(self, sample_gray):
        result = sc.detect_framing_lines(sample_gray)
        assert isinstance(result, dict)
        assert "framing_score" in result
        assert "lines" in result
        assert 0.0 <= result["framing_score"] <= 1.0


class TestSpatialGrid:
    def test_compute_zones_count(self, sample_rgb):
        sal = sc.compute_saliency_spectral(sample_rgb)
        zones = sc.compute_spatial_zones(sal, sample_rgb, 3, 3)
        assert len(zones) == 9

    def test_zone_dict_keys(self, sample_rgb):
        sal = sc.compute_saliency_spectral(sample_rgb)
        zones = sc.compute_spatial_zones(sal, sample_rgb, 2, 2)
        assert len(zones) == 4
        z = zones[0]
        assert "zone_id" in z
        assert "position_label" in z
        assert "mean_saliency" in z
        assert "visual_weight" in z
        assert "edge_density" in z
        assert "sharpness" in z

    def test_zone_2x2_positions(self, sample_rgb):
        sal = sc.compute_saliency_spectral(sample_rgb)
        zones = sc.compute_spatial_zones(sal, sample_rgb, 2, 2)
        positions = {z["position_label"] for z in zones}
        assert "top-left" in positions
        assert "bottom-right" in positions


class TestColorFeatures:
    def test_modality_cues_keys(self, sample_rgb):
        cues = sc.compute_modality_cues(sample_rgb)
        expected = {
            "colour_saturation", "colour_differentiation", "colour_modulation",
            "contextualization", "representation", "depth",
            "illumination", "brightness",
        }
        assert expected == set(cues.keys())

    def test_modality_cues_range(self, sample_rgb):
        cues = sc.compute_modality_cues(sample_rgb)
        for k, v in cues.items():
            assert 0.0 <= v <= 1.0, f"{k}={v} out of range"

    def test_extract_palette(self, sample_rgb):
        palette = sc.extract_color_palette(sample_rgb, 4, 50)
        assert len(palette) == 4
        total_prop = sum(p["proportion"] for p in palette)
        assert abs(total_prop - 1.0) < 0.05

    def test_palette_dict_keys(self, sample_rgb):
        palette = sc.extract_color_palette(sample_rgb, 3)
        assert "rgb" in palette[0]
        assert "hex" in palette[0]
        assert "proportion" in palette[0]


class TestTexture:
    def test_texture_features_keys(self, sample_gray):
        tex = sc.compute_texture_features(sample_gray)
        assert "gabor_energy" in tex
        assert "lbp_histogram" in tex
        assert "texture_homogeneity" in tex
        assert "dominant_orientation" in tex


class TestDepth:
    def test_depth_map_shape(self, sample_rgb):
        depth = sc.estimate_depth_map(sample_rgb)
        assert depth.shape == (200, 300)

    def test_depth_map_range(self, sample_rgb):
        depth = sc.estimate_depth_map(sample_rgb)
        assert depth.min() >= -1e-6  # floating point tolerance
        assert depth.max() <= 1.0 + 1e-6


class TestReadingPath:
    def test_reading_path_returns_list(self, sample_rgb):
        sal = sc.compute_saliency_spectral(sample_rgb)
        path = sc.compute_reading_path(sal, 5)
        assert isinstance(path, list)

    def test_waypoint_keys(self, sample_rgb):
        sal = sc.compute_saliency_itti(sample_rgb)
        path = sc.compute_reading_path(sal, 5)
        if path:
            assert "x" in path[0]
            assert "y" in path[0]
            assert "saliency" in path[0]
