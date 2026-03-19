"""Tests for the rule-based local interpretation module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from core.local_interpretation import generate_local_interpretation


class TestRepresentationalInterpretation:
    def test_narrative_transactional(self):
        data = {
            "structure_type": "narrative",
            "narrative_subtype": "transactional",
            "vector_count": 5,
            "dominant_direction": "diagonal",
            "participants": [{"label": "person"}],
        }
        text = generate_local_interpretation("representational", data)
        assert "narrative" in text.lower()
        assert "transactional" in text.lower()
        assert "Kress" in text

    def test_conceptual_symbolic(self):
        data = {
            "structure_type": "conceptual",
            "conceptual_subtype": "symbolic",
            "vector_count": 0,
            "participants": [{"label": "object"}],
        }
        text = generate_local_interpretation("representational", data)
        assert "conceptual" in text.lower()

    def test_empty_data(self):
        text = generate_local_interpretation("representational", {})
        assert len(text) > 0


class TestInteractiveInterpretation:
    def test_with_demand_faces(self):
        data = {
            "faces": [
                {"gaze_type": "demand"},
                {"gaze_type": "offer"},
            ],
            "vertical_angle": "eye_level",
            "horizontal_angle": "frontal",
            "modality_score": 0.7,
            "coding_orientation": "naturalistic",
        }
        text = generate_local_interpretation("interactive", data)
        assert "demand" in text.lower()
        assert "eye level" in text.lower()

    def test_no_faces(self):
        data = {
            "faces": [],
            "vertical_angle": "high",
            "horizontal_angle": "oblique",
            "modality_score": 0.3,
            "coding_orientation": "technological",
        }
        text = generate_local_interpretation("interactive", data)
        assert "offer" in text.lower()
        assert "high" in text.lower()


class TestCompositionalInterpretation:
    def test_polarized(self):
        data = {
            "composition_type": "polarized",
            "polarization_axes": ["given_new", "ideal_real"],
            "framing": {"disconnection_score": 0.5},
            "reading_path": {"path_shape": "z_pattern"},
        }
        text = generate_local_interpretation("compositional", data)
        assert "polarized" in text.lower()
        assert "Given" in text or "given" in text.lower()

    def test_centred(self):
        data = {
            "composition_type": "centred",
            "centred_subtype": "centre_margin",
            "framing": {"disconnection_score": 0.1},
            "reading_path": {"path_shape": "circular"},
        }
        text = generate_local_interpretation("compositional", data)
        assert "centred" in text.lower()


class TestFullInterpretation:
    def test_full_combines_all(self):
        data = {
            "representational": {
                "structure_type": "narrative",
                "narrative_subtype": "reactional",
                "vector_count": 3,
                "participants": [],
            },
            "interactive": {
                "faces": [],
                "vertical_angle": "low",
                "horizontal_angle": "frontal",
                "modality_score": 0.5,
                "coding_orientation": "sensory",
            },
            "compositional": {
                "composition_type": "polarized",
                "polarization_axes": ["ideal_real"],
                "framing": {"disconnection_score": 0.8},
                "reading_path": {"path_shape": "linear_tb"},
            },
        }
        text = generate_local_interpretation("full", data)
        assert "narrative" in text.lower()
        assert "offer" in text.lower() or "no human" in text.lower()
        assert "polarized" in text.lower()
