"""Rule-based semiotic interpretation — no LLM required.

Generates structured academic text using templates derived from
Kress & van Leeuwen's (2006) terminology.
"""


def generate_local_interpretation(analysis_type: str, data: dict) -> str:
    """Generate rule-based semiotic interpretation without LLM."""
    match analysis_type:
        case "representational":
            return _interpret_representational(data)
        case "interactive":
            return _interpret_interactive(data)
        case "compositional":
            return _interpret_compositional(data)
        case "full":
            return "\n\n".join(
                [
                    _interpret_representational(data.get("representational", {})),
                    _interpret_interactive(data.get("interactive", {})),
                    _interpret_compositional(data.get("compositional", {})),
                ]
            )
        case _:
            return ""


def _interpret_representational(data: dict) -> str:
    parts = []
    st = data.get("structure_type", "narrative")
    n_participants = len(data.get("participants", []))
    n_vectors = data.get("vector_count", 0)
    subtype = data.get("narrative_subtype") or data.get("conceptual_subtype", "unknown")

    if st == "narrative":
        parts.append(
            f"The image presents a narrative structure with {n_participants} "
            f"identified participant(s) and {n_vectors} action vector(s)."
        )
        match subtype:
            case "transactional":
                parts.append(
                    "The structure is transactional: a clear vector connects "
                    "an Actor to a Goal, establishing a doing-to relationship "
                    "(Kress & van Leeuwen, 2006)."
                )
            case "reactional":
                parts.append(
                    "The structure is reactional: the primary vector is formed "
                    "by an eyeline, connecting a Reacter to a Phenomenon "
                    "(Kress & van Leeuwen, 2006)."
                )
            case "non_transactional":
                parts.append(
                    "The structure is non-transactional: the Actor initiates "
                    "a vector but no identifiable Goal is present, leaving "
                    "the action open-ended (Kress & van Leeuwen, 2006)."
                )
            case "bidirectional":
                parts.append(
                    "The structure is bidirectional: two participants act on "
                    "each other reciprocally (Kress & van Leeuwen, 2006)."
                )
    else:
        parts.append(
            f"The image presents a conceptual structure ({subtype}) "
            f"with {n_participants} participant(s) and no prominent action vectors."
        )

    direction = data.get("dominant_direction", "")
    if direction:
        parts.append(f"The dominant vector direction is {direction}.")

    return " ".join(parts)


def _interpret_interactive(data: dict) -> str:
    parts = []
    faces = data.get("faces", [])
    demands = sum(1 for f in faces if f.get("gaze_type") == "demand")
    offers = len(faces) - demands

    if faces:
        parts.append(
            f"The image establishes contact through {len(faces)} detected face(s): "
            f"{demands} 'demand' (direct gaze) and {offers} 'offer' (averted gaze)."
        )
        if demands > offers:
            parts.append(
                "The dominant mode is 'demand': the represented participant(s) "
                "address the viewer directly, creating an imaginary social relation "
                "(Kress & van Leeuwen, 2006)."
            )
        else:
            parts.append(
                "The dominant mode is 'offer': the represented participants are "
                "presented as objects of contemplation "
                "(Kress & van Leeuwen, 2006)."
            )
    else:
        parts.append(
            "No human faces are detected. The image functions as an 'offer', "
            "presenting its content impersonally to the viewer."
        )

    va = data.get("vertical_angle", "eye_level")
    ha = data.get("horizontal_angle", "frontal")
    power_map = {
        "high": "viewer power over the subject",
        "eye_level": "equality between viewer and subject",
        "low": "subject power over the viewer",
    }
    involvement_map = {
        "frontal": "involvement and identification",
        "oblique": "detachment and otherness",
    }
    parts.append(
        f"The vertical angle is {va.replace('_', ' ')}, suggesting "
        f"{power_map.get(va, 'equality')}. "
        f"The horizontal angle is {ha}, encoding "
        f"{involvement_map.get(ha, 'detachment')}."
    )

    ms = data.get("modality_score", 0)
    co = data.get("coding_orientation", "naturalistic")
    parts.append(
        f"The modality score is {ms:.2f} under {co} coding orientation "
        f"(Kress & van Leeuwen, 2006)."
    )

    return " ".join(parts)


def _interpret_compositional(data: dict) -> str:
    parts = []
    comp_type = data.get("composition_type", "polarized")

    parts.append(f"The composition is {comp_type}.")

    if comp_type == "centred":
        sub = data.get("centred_subtype", "centre_margin")
        parts.append(
            f"The structure is {sub.replace('_', '-')}: a central element acts as "
            f"the nucleus of information, with marginal elements in a subordinate "
            f"role (Kress & van Leeuwen, 2006)."
        )
    else:
        axes = data.get("polarization_axes", [])
        if "given_new" in axes:
            parts.append(
                "A Given-New (left-right) axis is present: the left side presents "
                "familiar information, while the right presents the message "
                "(Kress & van Leeuwen, 2006)."
            )
        if "ideal_real" in axes:
            parts.append(
                "An Ideal-Real (top-bottom) axis is present: the top presents "
                "the aspirational essence, while the bottom shows practical detail "
                "(Kress & van Leeuwen, 2006)."
            )

    framing = data.get("framing", {})
    disc = framing.get("disconnection_score", 0)
    if disc > 0.6:
        framing_desc = "strong separation between elements"
    elif disc > 0.3:
        framing_desc = "moderate framing"
    else:
        framing_desc = "weak framing, elements presented as connected"
    parts.append(
        f"Framing analysis shows a disconnection score of {disc:.2f} "
        f"({framing_desc})."
    )

    rp = data.get("reading_path", {})
    if rp:
        shape = rp.get("path_shape", "irregular")
        parts.append(
            f"The predicted reading path follows a {shape.replace('_', ' ')} "
            f"pattern."
        )

    return " ".join(parts)
