"""POST /api/analyse/representational — Representational analysis.

Implements Kress & van Leeuwen (2006), Chapters 2-3.
Ch. 2: Narrative representations (vectors, actors, goals, processes).
Ch. 3: Conceptual representations (classificational, analytical, symbolic).
"""

import sys
import math
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from api.models.representational import (
    RepresentationalResult,
    Vector,
    Participant,
)
from core.image_utils import load_image, to_grayscale, image_to_base64

router = APIRouter()



class RepresentationalRequest(BaseModel):
    image_id: str
    api_backend: str = "local"
    image_description: str = ""


def _get_cpp_core(request: Request):
    cpp = getattr(request.app.state, "cpp_core", None)
    if cpp is not None:
        return cpp
    try:
        import semiovis_core
        return semiovis_core
    except ImportError:
        raise HTTPException(500, "C++ core module not available")


def _get_local_models(request: Request):
    models = getattr(request.app.state, "local_models", None)
    return models


def _classify_vectors(raw_vectors: list[dict]) -> list[Vector]:
    """Convert raw C++ vector dicts to typed Vector objects."""
    vectors = []
    for v in raw_vectors:
        vectors.append(Vector(
            x1=round(v["x1"], 4),
            y1=round(v["y1"], 4),
            x2=round(v["x2"], 4),
            y2=round(v["y2"], 4),
            angle=round(v["angle"], 2),
            strength=round(v["strength"], 4),
            direction=v["direction"],
        ))
    return vectors


def _dominant_direction(vectors: list[Vector]) -> str:
    """Find the dominant vector direction."""
    if not vectors:
        return "none"
    counts = {"horizontal": 0, "vertical": 0, "diagonal": 0}
    for v in vectors:
        counts[v.direction] += v.strength
    return max(counts, key=counts.get)


def _vectors_connect_participants(
    vectors: list[Vector], participants: list[dict]
) -> list[tuple[int, int, Vector]]:
    """Find vectors that connect pairs of participants (actor -> goal)."""
    connections = []
    for v in vectors:
        # Vector midpoint and direction
        vmx, vmy = (v.x1 + v.x2) / 2, (v.y1 + v.y2) / 2

        closest_start = -1
        closest_end = -1
        min_start_dist = 0.15  # max distance threshold (normalised)
        min_end_dist = 0.15

        for i, p in enumerate(participants):
            bx1, by1, bx2, by2 = p["bbox"]
            # Centre of bbox
            cx, cy = (bx1 + bx2) / 2, (by1 + by2) / 2

            # Distance from vector start to participant centre
            d_start = math.sqrt((v.x1 - cx) ** 2 + (v.y1 - cy) ** 2)
            # Distance from vector end to participant centre
            d_end = math.sqrt((v.x2 - cx) ** 2 + (v.y2 - cy) ** 2)

            if d_start < min_start_dist:
                min_start_dist = d_start
                closest_start = i
            if d_end < min_end_dist:
                min_end_dist = d_end
                closest_end = i

        if closest_start >= 0 and closest_end >= 0 and closest_start != closest_end:
            connections.append((closest_start, closest_end, v))

    return connections


def _classify_narrative_structure(
    vectors: list[Vector],
    participants: list[dict],
    faces: list[dict],
) -> tuple[str, str | None, str | None]:
    """Classify representational structure (Kress & vL, Ch. 2-3).

    Returns: (structure_type, narrative_subtype, conceptual_subtype)
    """
    n_vectors = len(vectors)
    n_participants = len(participants)
    n_humans = sum(1 for p in participants if p.get("is_human", False))

    # Strong vectors indicate narrative structure
    strong_vectors = [v for v in vectors if v.strength > 0.05]

    if len(strong_vectors) < 2 and n_vectors < 5:
        # Few/weak vectors -> likely conceptual
        structure_type = "conceptual"

        if n_participants <= 1:
            return structure_type, None, "symbolic"

        # Check for hierarchical arrangement (classificational)
        if n_participants >= 3:
            ys = sorted([((p["bbox"][1] + p["bbox"][3]) / 2) for p in participants])
            # If participants are arranged in distinct vertical levels
            y_gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
            if y_gaps and max(y_gaps) > 0.15:
                return structure_type, None, "classificational"

        # Check for part-whole (analytical): one large participant containing others
        if n_participants >= 2:
            areas = []
            for p in participants:
                bx1, by1, bx2, by2 = p["bbox"]
                areas.append((bx2 - bx1) * (by2 - by1))
            if max(areas) > 3 * np.median(areas):
                return structure_type, None, "analytical"

        return structure_type, None, "symbolic"

    # Narrative structure
    structure_type = "narrative"

    # Check for gaze vectors (reactional process)
    if faces:
        gaze_demands = [f for f in faces if f.get("gaze_type") == "demand"]
        gaze_offers = [f for f in faces if f.get("gaze_type") == "offer"]

        # If participants look at something specific -> reactional
        if gaze_offers and n_participants >= 2:
            return structure_type, "reactional", None

    # Check connections between participants
    connections = _vectors_connect_participants(vectors, participants)

    if len(connections) >= 2:
        # Check bidirectional: two participants connected in both directions
        pairs = set()
        for s, e, _ in connections:
            pair = (min(s, e), max(s, e))
            if pair in pairs:
                return structure_type, "bidirectional", None
            pairs.add(pair)

    if connections:
        # Transactional: clear actor -> goal connection
        return structure_type, "transactional", None

    if n_participants >= 1 and n_vectors >= 3:
        # Vectors present but not connecting to specific goals
        return structure_type, "non_transactional", None

    if n_participants == 0 and n_vectors >= 3:
        return structure_type, "non_transactional", None

    return structure_type, "non_transactional", None


@router.post("/representational", response_model=RepresentationalResult)
async def analyse_representational(req: RepresentationalRequest, request: Request):
    """Analyse representational meaning: narrative/conceptual structure, vectors, participants."""
    cpp_core = _get_cpp_core(request)
    local_models = _get_local_models(request)

    # Load image
    try:
        img_rgb = load_image(req.image_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Image not found: {req.image_id}")

    img_gray = to_grayscale(img_rgb)

    # 1. Detect vectors (C++ Hough lines)
    raw_vectors = list(cpp_core.detect_vectors(img_gray, min_line_length=40.0))
    vectors = _classify_vectors(raw_vectors)

    # 2. Detect participants (objects) via local models or API
    raw_participants = []
    faces = []
    if local_models is not None:
        raw_participants = await local_models.detect_objects(img_rgb)
        faces = await local_models.detect_faces(img_rgb)
    elif req.api_backend != "local":
        from core.vision_api import call_vision_api
        results = await call_vision_api(
            img_rgb, ["objects", "faces"], api=req.api_backend, local_models=local_models
        )
        raw_participants = results.get("objects", [])
        faces = results.get("faces", [])

    # 3. Classify structure
    structure_type, narrative_subtype, conceptual_subtype = _classify_narrative_structure(
        vectors, raw_participants, faces
    )

    # 4. Build participant list
    participants = [
        Participant(
            label=p["label"],
            confidence=round(p["confidence"], 3),
            bbox=tuple(round(x, 4) for x in p["bbox"]),
            is_human=p.get("is_human", False),
            is_animal=p.get("is_animal", False),
        )
        for p in raw_participants
    ]

    # 5. Dominant direction
    dom_dir = _dominant_direction(vectors)

    # 6. Generate interpretation
    from core.vision_api import generate_interpretation

    interp_data = {
        "structure_type": structure_type,
        "narrative_subtype": narrative_subtype,
        "conceptual_subtype": conceptual_subtype,
        "vector_count": len(vectors),
        "dominant_direction": dom_dir,
        "participants": [
            {"label": p.label, "is_human": p.is_human, "bbox": list(p.bbox)}
            for p in participants
        ],
        "faces_detected": len(faces),
    }
    img_b64 = image_to_base64(img_rgb)
    interpretation = await generate_interpretation(
        "representational", interp_data, img_b64,
        image_description=req.image_description,
    )

    return RepresentationalResult(
        structure_type=structure_type,
        narrative_subtype=narrative_subtype,
        conceptual_subtype=conceptual_subtype,
        vectors=vectors,
        participants=participants,
        vector_count=len(vectors),
        dominant_direction=dom_dir,
        interpretation=interpretation,
    )
