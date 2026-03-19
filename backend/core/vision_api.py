"""Unified vision API dispatcher and LLM interpretation cascade."""

import json
import os

import httpx


async def call_vision_api(img_path, features, api="local", local_models=None):
    """Unified dispatcher for object/face detection."""
    match api:
        case "local":
            return await _call_local_models(img_path, features, local_models)
        case "google":
            return await _call_google_vision(img_path, features)
        case "aws":
            return await _call_aws_rekognition(img_path, features)
        case _:
            raise ValueError(f"Unknown API backend: {api}")


async def _call_local_models(img_path, features, local_models):
    import cv2
    import numpy as np

    if isinstance(img_path, np.ndarray):
        img = img_path
    else:
        img = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2RGB)

    results = {}
    if "objects" in features:
        results["objects"] = await local_models.detect_objects(img)
    if "faces" in features:
        results["faces"] = await local_models.detect_faces(img)
    if "persons" in features:
        results["persons"] = await local_models.detect_persons(img)
    return results


async def _call_google_vision(img_path, features):
    raise NotImplementedError("Google Vision backend not yet implemented")


async def _call_aws_rekognition(img_path, features):
    raise NotImplementedError("AWS Rekognition backend not yet implemented")


# --- LLM Interpretation Cascade ---

SEMIOTIC_PROMPT = """You are an expert in social semiotics specialising in
Kress and van Leeuwen's visual grammar (Reading Images, 2006).

Extracted features:
{features_json}

{context_info}

Provide a {analysis_type} analysis covering:
- How meaning is constructed through this visual dimension
- Specific visual elements that carry semiotic weight
- The communicative strategy implied
- Reference methodological concepts by name (e.g., transactional narrative, demand/offer gaze, Given-New axis) without citing page or chapter numbers

Write in academic English, approximately 150-200 words."""


# Runtime API key storage (set from frontend Settings)
_runtime_keys: dict[str, str] = {}


def set_api_keys(keys: dict[str, str]):
    """Update API keys at runtime (called when frontend sends settings)."""
    global _runtime_keys
    _runtime_keys = {k: v for k, v in keys.items() if v}


def _get_key(name: str) -> str:
    """Get API key from runtime storage or environment."""
    return _runtime_keys.get(name, "") or os.getenv(name, "").strip()


async def generate_interpretation(
    analysis_type: str,
    data: dict,
    img_base64: str | None = None,
    preferred_llm: str = "auto",
    image_description: str = "",
) -> str:
    """Generate semiotic interpretation using the best available LLM."""
    features_json = json.dumps(data, indent=2, default=str)

    context_info = ""
    if image_description:
        context_info = f"Image context provided by the user: {image_description}\nUse this context to enrich your interpretation."

    prompt = SEMIOTIC_PROMPT.format(
        features_json=features_json,
        analysis_type=analysis_type,
        context_info=context_info,
    )

    if preferred_llm == "auto":
        for backend in ["openai", "gemini", "mistral", "local"]:
            result = await _try_llm(backend, prompt, img_base64, analysis_type, data)
            if result:
                return result
    else:
        result = await _try_llm(preferred_llm, prompt, img_base64, analysis_type, data)
        if result:
            return result

    from core.local_interpretation import generate_local_interpretation
    return generate_local_interpretation(analysis_type, data)


async def _try_llm(backend, prompt, img_base64, analysis_type, data):
    try:
        match backend:
            case "openai":
                return await _call_openai_llm(prompt, img_base64)
            case "gemini":
                return await _call_gemini_llm(prompt, img_base64)
            case "mistral":
                return await _call_mistral_llm(prompt, img_base64)
            case "local":
                from core.local_interpretation import generate_local_interpretation
                return generate_local_interpretation(analysis_type, data)
    except Exception:
        return None


async def _call_openai_llm(prompt, img_base64):
    key = _get_key("openai") or _get_key("OPENAI_API_KEY")
    if not key:
        return None
    async with httpx.AsyncClient() as client:
        content = []
        if img_base64:
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
            )
        content.append({"type": "text", "text": prompt})
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 500,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_gemini_llm(prompt, img_base64):
    key = _get_key("gemini") or _get_key("GEMINI_API_KEY")
    if not key:
        return None
    async with httpx.AsyncClient() as client:
        parts = []
        if img_base64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_base64}})
        parts.append({"text": prompt})
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={key}",
            json={"contents": [{"parts": parts}], "generationConfig": {"maxOutputTokens": 500}},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _call_mistral_llm(prompt, img_base64):
    key = _get_key("mistral") or _get_key("MISTRAL_API_KEY")
    if not key:
        return None
    async with httpx.AsyncClient() as client:
        content = []
        if img_base64:
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
            )
        content.append({"type": "text", "text": prompt})
        resp = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "pixtral-12b-2409",
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 500,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
