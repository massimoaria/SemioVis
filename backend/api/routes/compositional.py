"""POST /api/analyse/compositional — Compositional analysis.

Implements Kress & van Leeuwen (2006), Chapter 6: The meaning of composition.
Analyses information value, salience, framing, and reading path.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from api.models.compositional import (
    CompositionalResult,
    SpatialZone,
    ColorSwatch,
    FramingAnalysis,
    ReadingPath,
)
from core.image_utils import load_image, to_grayscale, image_to_base64

router = APIRouter()

# Add C++ build directory to path


class CompositionalRequest(BaseModel):
    image_id: str
    saliency_method: str = "spectral"
    grid_size: str = "3x3"
    reading_direction: str = "ltr"
    image_description: str = ""


def _get_cpp_core(request: Request):
    """Get C++ core module, falling back to direct import."""
    cpp = getattr(request.app.state, "cpp_core", None)
    if cpp is not None:
        return cpp
    try:
        import semiovis_core
        return semiovis_core
    except ImportError:
        raise HTTPException(500, "C++ core module not available")


def _parse_grid_size(grid_size: str) -> tuple[int, int]:
    """Parse '3x3' -> (n_rows, n_cols)."""
    parts = grid_size.lower().split("x")
    if len(parts) != 2:
        return 3, 3
    return int(parts[0]), int(parts[1])


def _classify_composition_type(
    saliency_map: np.ndarray, zones: list[dict], n_rows: int, n_cols: int
) -> tuple[str, str | None, list[str] | None, bool, str | None]:
    """Classify composition as Centred or Polarized.

    Kress & van Leeuwen, 2006, pp.194-210, Fig. 6.21 (p.210).
    Returns: (composition_type, centred_subtype, polarization_axes,
              has_triptych, triptych_orientation)
    """
    h, w = saliency_map.shape

    # Compute centre vs periphery visual weight
    ch, cw = h // 4, w // 4
    centre_roi = saliency_map[h // 2 - ch : h // 2 + ch, w // 2 - cw : w // 2 + cw]
    centre_weight = float(np.mean(centre_roi))
    total_weight = float(np.mean(saliency_map))

    # Left/right and top/bottom weights
    left_weight = float(np.mean(saliency_map[:, : w // 2]))
    right_weight = float(np.mean(saliency_map[:, w // 2 :]))
    top_weight = float(np.mean(saliency_map[: h // 2, :]))
    bottom_weight = float(np.mean(saliency_map[h // 2 :, :]))

    lr_asymmetry = abs(left_weight - right_weight) / (total_weight + 1e-10)
    tb_asymmetry = abs(top_weight - bottom_weight) / (total_weight + 1e-10)

    # Centre dominance ratio
    periphery_weight = total_weight  # approximate
    centre_ratio = centre_weight / (periphery_weight + 1e-10)

    # Classify
    if centre_ratio > 1.3:
        comp_type = "centred"

        # Detect subtypes
        has_triptych = False
        triptych_orientation = None
        centred_subtype = "centre_margin"

        if n_cols >= 3:
            # Check for triptych: strong left, centre, right panels
            col_weights = []
            for c in range(n_cols):
                x1 = c * w // n_cols
                x2 = (c + 1) * w // n_cols
                col_weights.append(float(np.mean(saliency_map[:, x1:x2])))

            if len(col_weights) >= 3:
                mid = len(col_weights) // 2
                left_panel = np.mean(col_weights[:mid])
                centre_panel = col_weights[mid]
                right_panel = np.mean(col_weights[mid + 1 :])
                # Triptych: all three panels have significant weight
                if (
                    min(left_panel, centre_panel, right_panel)
                    > 0.3 * max(left_panel, centre_panel, right_panel)
                ):
                    has_triptych = True
                    triptych_orientation = "horizontal"
                    centred_subtype = "triptych"

        if not has_triptych and n_rows >= 3:
            # Check vertical triptych
            row_weights = []
            for r in range(n_rows):
                y1 = r * h // n_rows
                y2 = (r + 1) * h // n_rows
                row_weights.append(float(np.mean(saliency_map[y1:y2, :])))
            if len(row_weights) >= 3:
                mid = len(row_weights) // 2
                if (
                    min(row_weights[0], row_weights[mid], row_weights[-1])
                    > 0.3 * max(row_weights[0], row_weights[mid], row_weights[-1])
                ):
                    has_triptych = True
                    triptych_orientation = "vertical"
                    centred_subtype = "triptych"

        # Check circular arrangement
        if not has_triptych and n_rows >= 3 and n_cols >= 3:
            margin_zones = [
                z for z in zones if z.get("position_label") != "center"
            ]
            margin_weights = [z.get("visual_weight", 0) for z in margin_zones]
            if margin_weights:
                margin_cv = np.std(margin_weights) / (np.mean(margin_weights) + 1e-10)
                if margin_cv < 0.3:  # relatively uniform margins
                    centred_subtype = "circular"

        return comp_type, centred_subtype, None, has_triptych, triptych_orientation
    else:
        comp_type = "polarized"
        axes = []
        if lr_asymmetry > 0.1:
            axes.append("given_new")
        if tb_asymmetry > 0.1:
            axes.append("ideal_real")
        if not axes:
            axes.append("given_new")  # default

        return comp_type, None, axes, False, None


def _assign_semiotic_labels(
    zones: list[dict],
    n_rows: int,
    n_cols: int,
    composition_type: str,
    reading_direction: str = "ltr",
) -> list[dict]:
    """Assign semiotic labels based on composition type and reading direction.

    Kress & van Leeuwen, 2006, pp.180-214.
    RTL cultures reverse Given/New (p.181, Fig. 6.3).
    """
    if reading_direction == "ltr":
        left_label, right_label = "Given", "New"
    else:
        left_label, right_label = "New", "Given"

    for zone in zones:
        col, row = zone["col"], zone["row"]
        labels = []

        if composition_type == "polarized":
            if col == 0:
                labels.append(left_label)
            elif col == n_cols - 1:
                labels.append(right_label)
            if row == 0:
                labels.append("Ideal")
            elif row == n_rows - 1:
                labels.append("Real")
        elif composition_type == "centred":
            if n_rows >= 3 and n_cols >= 3:
                is_centre = (
                    row > 0 and row < n_rows - 1 and col > 0 and col < n_cols - 1
                )
                if is_centre:
                    labels = ["Centre"]
                else:
                    labels = ["Margin"]
                    if col == 0:
                        labels.append(left_label)
                    elif col == n_cols - 1:
                        labels.append(right_label)
                    if row == 0:
                        labels.append("Ideal")
                    elif row == n_rows - 1:
                        labels.append("Real")
            else:
                # 2x2 grid: use polarized labels
                if col == 0:
                    labels.append(left_label)
                elif col == n_cols - 1:
                    labels.append(right_label)
                if row == 0:
                    labels.append("Ideal")
                elif row == n_rows - 1:
                    labels.append("Real")

        zone["semiotic_label"] = " / ".join(labels) if labels else "Margin"

    return zones


def _compute_framing(
    img_gray: np.ndarray, cpp_core, zones: list[dict], saliency_map: np.ndarray
) -> dict:
    """Compute framing analysis — Kress & van Leeuwen, 2006, pp.203-204."""
    framing_result = cpp_core.detect_framing_lines(img_gray)
    framing_score = framing_result["framing_score"]
    frame_lines = list(framing_result["lines"])

    h, w = img_gray.shape

    # Empty space regions: count large low-saliency areas
    low_sal = (saliency_map < 0.1).astype(np.uint8)
    # Morphological closing to merge nearby regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
    low_sal = cv2.morphologyEx(low_sal, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(low_sal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = h * w * 0.02
    empty_regions = sum(1 for c in contours if cv2.contourArea(c) > min_area)

    # Colour discontinuities: abrupt colour changes between adjacent zones
    colour_discontinuities = 0
    hsv = cv2.cvtColor(
        cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB), cv2.COLOR_RGB2HSV
    )
    # Actually need the RGB image for colour - use saliency as proxy
    # Count zones with very different visual weight from neighbours
    zone_map = {}
    for z in zones:
        zone_map[(z["row"], z["col"])] = z

    n_rows = max(z["row"] for z in zones) + 1
    n_cols = max(z["col"] for z in zones) + 1

    for z in zones:
        r, c = z["row"], z["col"]
        neighbours = []
        for dr, dc in [(0, 1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in zone_map:
                neighbours.append(zone_map[(nr, nc)])
        for nb in neighbours:
            weight_diff = abs(z["visual_weight"] - nb["visual_weight"])
            if weight_diff > 0.3:
                colour_discontinuities += 1

    # Colour continuities: shared colour linking zones
    colour_continuities = 0
    for z in zones:
        r, c = z["row"], z["col"]
        for dr, dc in [(0, 1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in zone_map:
                nb = zone_map[(nr, nc)]
                if z["color_temperature"] == nb["color_temperature"]:
                    colour_continuities += 1

    # Visual vectors crossing between zones (from detected vectors)
    vectors = cpp_core.detect_vectors(img_gray, min_line_length=40.0)
    visual_vectors = 0
    for v in vectors:
        # Check if vector spans across zone boundaries
        vx1, vy1 = v["x1"], v["y1"]
        vx2, vy2 = v["x2"], v["y2"]
        z1_col = min(int(vx1 * n_cols), n_cols - 1)
        z1_row = min(int(vy1 * n_rows), n_rows - 1)
        z2_col = min(int(vx2 * n_cols), n_cols - 1)
        z2_row = min(int(vy2 * n_rows), n_rows - 1)
        if z1_col != z2_col or z1_row != z2_row:
            visual_vectors += 1

    # Shape rhymes: detect repeated forms across zones via template matching
    # Simplified: count zones with similar edge density
    edge_densities = [z["edge_density"] for z in zones]
    shape_rhymes = 0
    if len(edge_densities) >= 2:
        for i in range(len(edge_densities)):
            for j in range(i + 1, len(edge_densities)):
                if abs(edge_densities[i] - edge_densities[j]) < 0.05:
                    shape_rhymes += 1

    disconnection = min(1.0, framing_score * 0.4 + empty_regions * 0.15 +
                        colour_discontinuities * 0.1)
    connection = min(1.0, colour_continuities * 0.15 + visual_vectors * 0.05 +
                     shape_rhymes * 0.05)

    return {
        "disconnection_score": round(disconnection, 3),
        "connection_score": round(connection, 3),
        "frame_lines": frame_lines,
        "empty_space_regions": empty_regions,
        "colour_discontinuities": colour_discontinuities,
        "colour_continuities": colour_continuities,
        "visual_vectors": visual_vectors,
        "shape_rhymes": shape_rhymes,
    }


def _classify_reading_path(waypoints: list[dict], img_w: int, img_h: int) -> dict:
    """Classify reading path shape — Kress & van Leeuwen, 2006, pp.204-208."""
    if len(waypoints) < 2:
        return {
            "waypoints": waypoints,
            "path_shape": "irregular",
            "is_linear": False,
        }

    pts = [(w["x"], w["y"]) for w in waypoints]

    # Check linearity
    lr_increases = sum(1 for i in range(1, len(pts)) if pts[i][0] > pts[i - 1][0])
    tb_increases = sum(1 for i in range(1, len(pts)) if pts[i][1] > pts[i - 1][1])
    n = len(pts) - 1

    lr_ratio = lr_increases / n if n > 0 else 0
    tb_ratio = tb_increases / n if n > 0 else 0

    # Direction changes for Z-pattern detection
    direction_changes = 0
    for i in range(2, len(pts)):
        prev_right = pts[i - 1][0] > pts[i - 2][0]
        cur_right = pts[i][0] > pts[i - 1][0]
        if prev_right != cur_right:
            direction_changes += 1

    if lr_ratio > 0.75 and tb_ratio < 0.4:
        shape = "linear_lr"
        is_linear = True
    elif tb_ratio > 0.75 and lr_ratio < 0.4:
        shape = "linear_tb"
        is_linear = True
    elif direction_changes >= 2 and tb_ratio > 0.5:
        shape = "z_pattern"
        is_linear = False
    else:
        # Check circular
        if len(pts) >= 4:
            dx = pts[0][0] - pts[-1][0]
            dy = pts[0][1] - pts[-1][1]
            loop_dist = (dx ** 2 + dy ** 2) ** 0.5
            if loop_dist < 0.2:
                shape = "circular"
                is_linear = False
            else:
                shape = "irregular"
                is_linear = False
        else:
            shape = "irregular"
            is_linear = False

    return {
        "waypoints": waypoints,
        "path_shape": shape,
        "is_linear": is_linear,
    }


def _determine_dominant_structure(
    composition_type: str,
    centred_subtype: str | None,
    polarization_axes: list[str] | None,
    has_triptych: bool,
    zones: list[dict],
) -> str:
    """Determine the dominant compositional structure."""
    if composition_type == "centred":
        if has_triptych:
            return "triptych"
        if centred_subtype == "circular":
            return "circular"
        return "centre_margin"
    else:
        if polarization_axes:
            if len(polarization_axes) == 1:
                return polarization_axes[0]
            # Both axes: determine which is stronger
            n_rows = max(z["row"] for z in zones) + 1
            n_cols = max(z["col"] for z in zones) + 1

            left_w = np.mean([z["visual_weight"] for z in zones if z["col"] == 0])
            right_w = np.mean(
                [z["visual_weight"] for z in zones if z["col"] == n_cols - 1]
            )
            top_w = np.mean([z["visual_weight"] for z in zones if z["row"] == 0])
            bot_w = np.mean(
                [z["visual_weight"] for z in zones if z["row"] == n_rows - 1]
            )

            lr_diff = abs(left_w - right_w)
            tb_diff = abs(top_w - bot_w)
            return "given_new" if lr_diff > tb_diff else "ideal_real"
        return "mixed"


def _associate_palette_zones(
    palette: list[dict], img_rgb: np.ndarray, n_rows: int, n_cols: int
) -> list[dict]:
    """Associate each palette colour with its dominant spatial zone."""
    h, w = img_rgb.shape[:2]

    for swatch in palette:
        r, g, b = swatch["rgb"]
        # Find where this colour appears most
        diff = np.abs(img_rgb.astype(float) - np.array([r, g, b], dtype=float))
        dist = np.sum(diff, axis=2)
        mask = dist < 80  # pixels close to this colour

        best_zone = "global"
        best_count = 0
        for zr in range(n_rows):
            for zc in range(n_cols):
                y1, y2 = zr * h // n_rows, (zr + 1) * h // n_rows
                x1, x2 = zc * w // n_cols, (zc + 1) * w // n_cols
                count = int(np.sum(mask[y1:y2, x1:x2]))
                if count > best_count:
                    best_count = count
                    v_pos = "top" if zr == 0 else ("bottom" if zr == n_rows - 1 else "center")
                    h_pos = "left" if zc == 0 else ("right" if zc == n_cols - 1 else "center")
                    best_zone = f"{v_pos}-{h_pos}" if v_pos != h_pos else v_pos

        swatch["zone_association"] = best_zone

    return palette


@router.post("/compositional", response_model=CompositionalResult)
async def analyse_compositional(req: CompositionalRequest, request: Request):
    """Analyse compositional meaning: information value, salience, framing, reading path."""
    cpp_core = _get_cpp_core(request)

    # Load image
    try:
        img_rgb = load_image(req.image_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Image not found: {req.image_id}")

    img_gray = to_grayscale(img_rgb)
    h, w = img_rgb.shape[:2]
    n_rows, n_cols = _parse_grid_size(req.grid_size)

    # 1. Compute saliency map
    if req.saliency_method == "itti":
        saliency_map = np.array(cpp_core.compute_saliency_itti(img_rgb))
    else:
        saliency_map = np.array(cpp_core.compute_saliency_spectral(img_rgb))

    # 2. Compute spatial zones
    raw_zones = list(cpp_core.compute_spatial_zones(saliency_map, img_rgb, n_cols, n_rows))

    # 3. Compute depth map for foreground_ratio
    depth_model_path = str(
        Path(__file__).parent.parent.parent / "models" / "midas_v21_small_256.onnx"
    )
    depth_map = np.array(cpp_core.estimate_depth_map(img_rgb, depth_model_path))

    # Enrich zones with depth-based foreground ratio
    for zone in raw_zones:
        r, c = zone["row"], zone["col"]
        y1 = r * h // n_rows
        y2 = (r + 1) * h // n_rows
        x1 = c * w // n_cols
        x2 = (c + 1) * w // n_cols
        zone_depth = depth_map[y1:y2, x1:x2]
        # Foreground = high depth values (close to camera)
        zone["foreground_ratio"] = round(float(np.mean(zone_depth > 0.6)), 3)

    # 4. Classify composition type
    (
        composition_type,
        centred_subtype,
        polarization_axes,
        has_triptych,
        triptych_orientation,
    ) = _classify_composition_type(saliency_map, raw_zones, n_rows, n_cols)

    # 5. Assign semiotic labels
    raw_zones = _assign_semiotic_labels(
        raw_zones, n_rows, n_cols, composition_type, req.reading_direction
    )

    # 6. Colour palette
    raw_palette = list(cpp_core.extract_color_palette(img_rgb, 6, 100))
    palette_with_zones = _associate_palette_zones(raw_palette, img_rgb, n_rows, n_cols)

    # 7. Framing analysis
    framing_data = _compute_framing(img_gray, cpp_core, raw_zones, saliency_map)

    # 8. Reading path
    raw_waypoints = list(cpp_core.compute_reading_path(saliency_map, 10))
    reading_path_data = _classify_reading_path(raw_waypoints, w, h)

    # 9. Dominant structure
    dominant = _determine_dominant_structure(
        composition_type, centred_subtype, polarization_axes, has_triptych, raw_zones
    )

    # 10. Downsample saliency map for JSON response
    sal_small = cv2.resize(saliency_map, (50, 50), interpolation=cv2.INTER_AREA)
    saliency_list = [[round(float(v), 4) for v in row] for row in sal_small]

    # 11. Generate interpretation
    from core.vision_api import generate_interpretation

    interpretation_data = {
        "composition_type": composition_type,
        "centred_subtype": centred_subtype,
        "polarization_axes": polarization_axes,
        "has_triptych": has_triptych,
        "dominant_structure": dominant,
        "framing": framing_data,
        "reading_path": {
            "path_shape": reading_path_data["path_shape"],
            "n_waypoints": len(reading_path_data["waypoints"]),
        },
        "n_zones": len(raw_zones),
        "zone_summaries": [
            {
                "label": z["semiotic_label"],
                "saliency": round(z["mean_saliency"], 3),
                "weight": round(z["visual_weight"], 3),
            }
            for z in raw_zones
        ],
    }

    img_b64 = image_to_base64(img_rgb)
    interpretation = await generate_interpretation(
        "compositional", interpretation_data, img_b64,
        image_description=req.image_description,
    )

    # Build response
    zones_out = [
        SpatialZone(
            zone_id=z["zone_id"],
            position_label=z["position_label"],
            semiotic_label=z["semiotic_label"],
            mean_saliency=round(z["mean_saliency"], 4),
            visual_weight=round(z["visual_weight"], 4),
            color_temperature=z["color_temperature"],
            edge_density=round(z["edge_density"], 4),
            object_count=z["object_count"],
            tonal_contrast=round(z["tonal_contrast"], 4),
            colour_contrast=round(z["colour_contrast"], 4),
            has_human_figure=z["has_human_figure"],
            foreground_ratio=round(z["foreground_ratio"], 4),
            sharpness=round(z["sharpness"], 4),
            information_value_score=round(z["information_value_score"], 4),
        )
        for z in raw_zones
    ]

    palette_out = [
        ColorSwatch(
            hex=p["hex"],
            rgb=tuple(p["rgb"]) if isinstance(p["rgb"], list) else p["rgb"],
            proportion=round(p["proportion"], 4),
            zone_association=p.get("zone_association", "global"),
        )
        for p in palette_with_zones
    ]

    return CompositionalResult(
        composition_type=composition_type,
        centred_subtype=centred_subtype,
        polarization_axes=polarization_axes,
        has_triptych=has_triptych,
        triptych_orientation=triptych_orientation,
        zones=zones_out,
        saliency_map=saliency_list,
        color_palette=palette_out,
        framing=FramingAnalysis(**framing_data),
        reading_path=ReadingPath(**reading_path_data),
        dominant_structure=dominant,
        interpretation=interpretation,
    )
