"""Pydantic models for interactive analysis."""

from typing import Literal, Optional

from pydantic import BaseModel


class FaceAnalysis(BaseModel):
    face_id: int
    face_bbox: tuple[float, float, float, float]
    person_bbox: Optional[tuple[float, float, float, float]] = None
    gaze_type: Literal["demand", "offer"]
    pan_angle: float
    tilt_angle: float
    roll_angle: float
    social_distance: Literal["intimate", "personal", "social", "public", "very_public"]
    shot_type: Literal[
        "extreme_close_up",
        "close_up",
        "medium_close",
        "medium",
        "medium_long",
        "long",
        "very_long",
    ]
    emotions: dict[str, float]


class ModalityProfile(BaseModel):
    """8 modality marker scales — Kress & van Leeuwen, 2006, pp.160-163."""

    colour_saturation: float
    colour_differentiation: float
    colour_modulation: float
    contextualization: float
    representation: float
    depth: float
    illumination: float
    brightness: float


class InteractiveResult(BaseModel):
    faces: list[FaceAnalysis]
    vertical_angle: Literal["high", "eye_level", "low"]
    horizontal_angle: Literal["frontal", "oblique"]
    power_relation: Literal["viewer_power", "equality", "subject_power"]
    involvement: Literal["high", "low"]
    modality_profile: ModalityProfile
    coding_orientation: Literal["naturalistic", "sensory", "technological", "abstract"]
    modality_score: float
    vanishing_point: Optional[tuple[float, float]] = None
    interpretation: str
