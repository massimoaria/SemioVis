"""Pydantic models for representational analysis."""

from typing import Literal, Optional

from pydantic import BaseModel


class Vector(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    angle: float
    strength: float
    direction: Literal["horizontal", "vertical", "diagonal"]


class Participant(BaseModel):
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    is_human: bool
    is_animal: bool


class RepresentationalResult(BaseModel):
    structure_type: Literal["narrative", "conceptual"]
    narrative_subtype: Optional[
        Literal[
            "transactional",
            "non_transactional",
            "bidirectional",
            "reactional",
            "mental",
            "verbal",
            "conversion",
        ]
    ] = None
    conceptual_subtype: Optional[
        Literal["classificational", "analytical", "symbolic"]
    ] = None
    vectors: list[Vector]
    participants: list[Participant]
    vector_count: int
    dominant_direction: str
    interpretation: str
