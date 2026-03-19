"""POST /api/analyse/interactive — Interactive analysis.

Implements Kress & van Leeuwen (2006), Chapters 4-5.
Ch. 4: Representation and interaction (contact, social distance, attitude, power).
Ch. 5: Modality — designing models of reality (8-scale modality profile).
"""

import sys
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from api.models.interactive import (
    InteractiveResult,
    FaceAnalysis,
    ModalityProfile,
)
from core.image_utils import load_image, to_grayscale, image_to_base64

router = APIRouter()



class InteractiveRequest(BaseModel):
    image_id: str
    api_backend: str = "local"
    coding_orientation: str = "naturalistic"
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
    return getattr(request.app.state, "local_models", None)


def _classify_social_distance(person_bbox: list[float] | None, img_shape: tuple) -> tuple[str, str]:
    """Classify social distance from body framing.

    Kress & van Leeuwen, 2006, pp.124-128.
    Based on BODY framing (not face size).
    Returns: (social_distance, shot_type)
    """
    if person_bbox is None:
        return "social", "medium"

    person_height_ratio = person_bbox[3] - person_bbox[1]  # normalised height

    if person_height_ratio > 0.80:
        return "intimate", "extreme_close_up"
    elif person_height_ratio > 0.65:
        return "personal", "close_up"
    elif person_height_ratio > 0.50:
        return "personal", "medium_close"
    elif person_height_ratio > 0.35:
        return "social", "medium"
    elif person_height_ratio > 0.25:
        return "social", "medium_long"
    elif person_height_ratio > 0.15:
        return "public", "long"
    else:
        return "very_public", "very_long"


def _match_faces_to_persons(faces: list[dict], persons: list[dict]) -> dict[int, dict | None]:
    """Match each face to its corresponding full-body person detection."""
    face_to_person = {}
    for face in faces:
        fx1, fy1, fx2, fy2 = face["face_bbox"]
        face_cx = (fx1 + fx2) / 2
        face_cy = (fy1 + fy2) / 2

        best_person = None
        best_overlap = 0

        for person in persons:
            px1, py1, px2, py2 = person["bbox"]
            # Check if face centre is inside person bbox
            if px1 <= face_cx <= px2 and py1 <= face_cy <= py2:
                # Overlap area
                overlap = (min(fx2, px2) - max(fx1, px1)) * (min(fy2, py2) - max(fy1, py1))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_person = person

        face_to_person[face["face_id"]] = best_person

    return face_to_person


def _classify_vertical_angle(vp: dict | None, faces: list[dict]) -> str:
    """Classify vertical camera angle.

    Kress & van Leeuwen, 2006, p.140.
    high angle = viewer power, low angle = subject power, eye level = equality.
    """
    if vp and vp.get("vp_y") is not None:
        vp_y = vp["vp_y"]
        if isinstance(vp_y, (int, float)):
            if vp_y < 0.35:
                return "high"    # VP above centre -> looking down
            elif vp_y > 0.65:
                return "low"     # VP below centre -> looking up
            else:
                return "eye_level"

    # Fallback: estimate from face positions
    if faces:
        avg_face_y = np.mean([(f["face_bbox"][1] + f["face_bbox"][3]) / 2 for f in faces])
        if avg_face_y < 0.35:
            return "high"
        elif avg_face_y > 0.65:
            return "low"

    return "eye_level"


def _classify_horizontal_angle(vp: dict | None) -> str:
    """Classify horizontal angle.

    Kress & van Leeuwen, 2006, p.136.
    frontal = involvement, oblique = detachment.
    """
    if vp and vp.get("vp_x") is not None:
        vp_x = vp["vp_x"]
        if isinstance(vp_x, (int, float)):
            if 0.3 <= vp_x <= 0.7:
                return "frontal"
            else:
                return "oblique"
    return "frontal"


def _compute_modality_score(profile: dict, orientation: str = "naturalistic") -> float:
    """Compute modality score relative to coding orientation.

    Kress & van Leeuwen, 2006, pp.160-175, Fig. 5.5 (p.166).
    """
    markers = [
        profile["colour_saturation"],
        profile["colour_differentiation"],
        profile["colour_modulation"],
        profile["contextualization"],
        profile["representation"],
        profile["depth"],
        profile["illumination"],
        profile["brightness"],
    ]

    if orientation == "naturalistic":
        # Highest modality at moderate values (~0.6-0.7, photographic norm)
        return max(0.0, min(1.0,
            1.0 - np.mean([abs(m - 0.65) for m in markers]) / 0.65
        ))
    elif orientation == "sensory":
        # High values = high modality (maximal sensory impact)
        return float(np.mean(markers))
    elif orientation == "technological":
        # Low colour/texture = high modality (functional effectiveness)
        return float(1.0 - np.mean(markers))
    elif orientation == "abstract":
        # Reduction = high modality
        return float(1.0 - np.mean([
            profile["colour_saturation"],
            profile["contextualization"],
            profile["representation"],
            profile["depth"],
        ]))
    return float(np.mean(markers))


@router.post("/interactive", response_model=InteractiveResult)
async def analyse_interactive(req: InteractiveRequest, request: Request):
    """Analyse interactive meaning: gaze, social distance, modality, perspective."""
    cpp_core = _get_cpp_core(request)
    local_models = _get_local_models(request)

    # Load image
    try:
        img_rgb = load_image(req.image_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Image not found: {req.image_id}")

    img_gray = to_grayscale(img_rgb)
    h, w = img_rgb.shape[:2]

    # 1. Detect faces and persons
    raw_faces = []
    raw_persons = []
    if local_models is not None:
        raw_faces = await local_models.detect_faces(img_rgb)
        raw_persons = await local_models.detect_persons(img_rgb)
    elif req.api_backend != "local":
        from core.vision_api import call_vision_api
        results = await call_vision_api(
            img_rgb, ["faces", "persons"], api=req.api_backend, local_models=local_models
        )
        raw_faces = results.get("faces", [])
        raw_persons = results.get("persons", [])

    # 2. Match faces to persons for body-based social distance
    face_to_person = _match_faces_to_persons(raw_faces, raw_persons)

    # 3. Build face analysis results
    faces_out = []
    for face in raw_faces:
        person = face_to_person.get(face["face_id"])
        person_bbox = person["bbox"] if person else None

        social_dist, shot_type = _classify_social_distance(
            person_bbox or face.get("face_bbox"), (h, w)
        )

        faces_out.append(FaceAnalysis(
            face_id=face["face_id"],
            face_bbox=tuple(round(x, 4) for x in face["face_bbox"]),
            person_bbox=tuple(round(x, 4) for x in person_bbox) if person_bbox else None,
            gaze_type=face.get("gaze_type", "offer"),
            pan_angle=round(face.get("pan_angle", 0), 2),
            tilt_angle=round(face.get("tilt_angle", 0), 2),
            roll_angle=round(face.get("roll_angle", 0), 2),
            social_distance=social_dist,
            shot_type=shot_type,
            emotions=face.get("emotions", {}),
        ))

    # 4. Vanishing point and angles
    vp_result = cpp_core.estimate_vanishing_point(img_gray)
    vertical_angle = _classify_vertical_angle(vp_result, raw_faces)
    horizontal_angle = _classify_horizontal_angle(vp_result)

    # Power relation from vertical angle (p.140)
    power_map = {
        "high": "viewer_power",
        "eye_level": "equality",
        "low": "subject_power",
    }
    power_relation = power_map[vertical_angle]

    # Involvement from horizontal angle (p.136)
    involvement = "high" if horizontal_angle == "frontal" else "low"

    # 5. Modality profile (8 scales from C++)
    modality_cues = dict(cpp_core.compute_modality_cues(img_rgb))
    modality_score = _compute_modality_score(modality_cues, req.coding_orientation)

    modality_profile = ModalityProfile(
        colour_saturation=round(modality_cues["colour_saturation"], 4),
        colour_differentiation=round(modality_cues["colour_differentiation"], 4),
        colour_modulation=round(modality_cues["colour_modulation"], 4),
        contextualization=round(modality_cues["contextualization"], 4),
        representation=round(modality_cues["representation"], 4),
        depth=round(modality_cues["depth"], 4),
        illumination=round(modality_cues["illumination"], 4),
        brightness=round(modality_cues["brightness"], 4),
    )

    # 6. Vanishing point for response
    vp_out = None
    if vp_result.get("vp_x") is not None and not isinstance(vp_result["vp_x"], type(None)):
        vp_x = vp_result["vp_x"]
        vp_y = vp_result["vp_y"]
        if isinstance(vp_x, (int, float)) and isinstance(vp_y, (int, float)):
            vp_out = (round(float(vp_x), 4), round(float(vp_y), 4))

    # 7. Generate interpretation
    from core.vision_api import generate_interpretation

    interp_data = {
        "faces": [
            {
                "gaze_type": f.gaze_type,
                "social_distance": f.social_distance,
                "shot_type": f.shot_type,
                "emotions": dict(sorted(f.emotions.items(), key=lambda x: -x[1])[:3]),
            }
            for f in faces_out
        ],
        "vertical_angle": vertical_angle,
        "horizontal_angle": horizontal_angle,
        "power_relation": power_relation,
        "involvement": involvement,
        "modality_score": round(modality_score, 3),
        "coding_orientation": req.coding_orientation,
        "modality_profile": modality_cues,
        "vanishing_point": vp_out,
    }
    img_b64 = image_to_base64(img_rgb)
    interpretation = await generate_interpretation(
        "interactive", interp_data, img_b64,
        image_description=req.image_description,
    )

    return InteractiveResult(
        faces=faces_out,
        vertical_angle=vertical_angle,
        horizontal_angle=horizontal_angle,
        power_relation=power_relation,
        involvement=involvement,
        modality_profile=modality_profile,
        coding_orientation=req.coding_orientation,
        modality_score=round(modality_score, 4),
        vanishing_point=vp_out,
        interpretation=interpretation,
    )
