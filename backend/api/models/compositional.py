"""Pydantic models for compositional analysis."""

from typing import Literal, Optional

from pydantic import BaseModel


class SpatialZone(BaseModel):
    zone_id: str
    position_label: str
    semiotic_label: str
    mean_saliency: float
    visual_weight: float
    color_temperature: Literal["warm", "neutral", "cool"]
    edge_density: float
    object_count: int
    tonal_contrast: float
    colour_contrast: float
    has_human_figure: bool
    foreground_ratio: float
    sharpness: float
    information_value_score: float


class ColorSwatch(BaseModel):
    hex: str
    rgb: tuple[int, int, int]
    proportion: float
    zone_association: str


class FramingAnalysis(BaseModel):
    """Framing breakdown — Kress & van Leeuwen, 2006, pp.203-204."""

    disconnection_score: float
    connection_score: float
    frame_lines: list[dict]
    empty_space_regions: int
    colour_discontinuities: int
    colour_continuities: int
    visual_vectors: int
    shape_rhymes: int


class ReadingPath(BaseModel):
    """Predicted reading path — Kress & van Leeuwen, 2006, pp.204-208."""

    waypoints: list[dict]
    path_shape: Literal[
        "linear_lr", "linear_tb", "circular", "spiral", "z_pattern", "irregular"
    ]
    is_linear: bool


class CompositionalResult(BaseModel):
    composition_type: Literal["centred", "polarized"]
    centred_subtype: Optional[Literal["circular", "triptych", "centre_margin"]] = None
    polarization_axes: Optional[list[Literal["given_new", "ideal_real"]]] = None
    has_triptych: bool
    triptych_orientation: Optional[Literal["horizontal", "vertical"]] = None
    zones: list[SpatialZone]
    saliency_map: list[list[float]]
    color_palette: list[ColorSwatch]
    framing: FramingAnalysis
    reading_path: ReadingPath
    dominant_structure: Literal[
        "given_new", "ideal_real", "centre_margin", "triptych", "circular", "mixed"
    ]
    interpretation: str
