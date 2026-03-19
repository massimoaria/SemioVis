"""Tests for FastAPI API routes."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "cpp" / "build"))

from main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def uploaded_image():
    """Upload a test image and return the image_id."""
    import cv2
    import numpy as np

    img = np.zeros((200, 300, 3), dtype=np.uint8)
    for y in range(200):
        img[y, :] = [int(200 - y * 0.8), int(100 + y * 0.3), int(50 + y * 0.5)]
    cv2.rectangle(img, (50, 30), (250, 170), (255, 200, 100), -1)
    cv2.circle(img, (150, 100), 40, (50, 50, 200), -1)

    path = "/tmp/semiovis_test_image.jpg"
    cv2.imwrite(path, img)

    with open(path, "rb") as f:
        response = client.post("/api/upload", files={"file": ("test.jpg", f, "image/jpeg")})

    assert response.status_code == 200
    data = response.json()
    assert "image_id" in data
    return data["image_id"]


class TestUpload:
    def test_upload_success(self):
        import cv2
        import numpy as np

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        path = "/tmp/semiovis_upload_test.jpg"
        cv2.imwrite(path, img)

        with open(path, "rb") as f:
            resp = client.post("/api/upload", files={"file": ("test.jpg", f, "image/jpeg")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["width"] == 50
        assert data["height"] == 50
        assert len(data["thumbnail_base64"]) > 0

    def test_upload_rejects_non_image(self):
        from io import BytesIO

        resp = client.post(
            "/api/upload",
            files={"file": ("test.txt", BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 400


class TestCompositional:
    def test_compositional_analysis(self, uploaded_image):
        resp = client.post(
            "/api/analyse/compositional",
            json={
                "image_id": uploaded_image,
                "saliency_method": "spectral",
                "grid_size": "3x3",
                "reading_direction": "ltr",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["composition_type"] in ("centred", "polarized")
        assert len(data["zones"]) == 9
        assert len(data["color_palette"]) > 0
        assert "disconnection_score" in data["framing"]
        assert data["reading_path"]["path_shape"] in (
            "linear_lr", "linear_tb", "circular", "spiral", "z_pattern", "irregular"
        )

    def test_compositional_2x2_grid(self, uploaded_image):
        resp = client.post(
            "/api/analyse/compositional",
            json={"image_id": uploaded_image, "grid_size": "2x2"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["zones"]) == 4

    def test_compositional_rtl(self, uploaded_image):
        resp = client.post(
            "/api/analyse/compositional",
            json={"image_id": uploaded_image, "reading_direction": "rtl"},
        )
        assert resp.status_code == 200
        zones = resp.json()["zones"]
        # In RTL, left column should be "New", right should be "Given"
        left_zones = [z for z in zones if "left" in z["position_label"]]
        for z in left_zones:
            if z["semiotic_label"]:
                assert "New" in z["semiotic_label"] or "Margin" in z["semiotic_label"]

    def test_compositional_missing_image(self):
        resp = client.post(
            "/api/analyse/compositional",
            json={"image_id": "nonexistent-id"},
        )
        assert resp.status_code == 404


class TestRepresentational:
    def test_representational_analysis(self, uploaded_image):
        resp = client.post(
            "/api/analyse/representational",
            json={"image_id": uploaded_image},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["structure_type"] in ("narrative", "conceptual")
        assert isinstance(data["vectors"], list)
        assert isinstance(data["participants"], list)
        assert data["vector_count"] >= 0
        assert len(data["interpretation"]) > 0


class TestInteractive:
    def test_interactive_analysis(self, uploaded_image):
        resp = client.post(
            "/api/analyse/interactive",
            json={"image_id": uploaded_image},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vertical_angle"] in ("high", "eye_level", "low")
        assert data["horizontal_angle"] in ("frontal", "oblique")
        assert data["power_relation"] in ("viewer_power", "equality", "subject_power")
        assert 0.0 <= data["modality_score"] <= 1.0
        mp = data["modality_profile"]
        assert all(k in mp for k in (
            "colour_saturation", "colour_differentiation", "depth", "brightness"
        ))

    def test_interactive_coding_orientations(self, uploaded_image):
        for orientation in ("naturalistic", "sensory", "technological", "abstract"):
            resp = client.post(
                "/api/analyse/interactive",
                json={"image_id": uploaded_image, "coding_orientation": orientation},
            )
            assert resp.status_code == 200
            assert resp.json()["coding_orientation"] == orientation


class TestReport:
    def test_report_generation_pdf(self, uploaded_image):
        resp = client.post(
            "/api/report",
            json={
                "image_id": uploaded_image,
                "analysis_results": {
                    "representational": {"structure_type": "narrative", "interpretation": "Test"},
                },
                "format": "pdf",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_report_generation_html(self, uploaded_image):
        resp = client.post(
            "/api/report",
            json={
                "image_id": uploaded_image,
                "analysis_results": {},
                "format": "html",
            },
        )
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
