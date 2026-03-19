"""SemioVis — FastAPI application entry point."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import upload, representational, interactive, compositional, dashboard, report

# Add C++ build directory to Python path ONLY if USE_CPP_CORE env is set
# (disabled by default to avoid OpenCV library conflicts with pip packages)
import os
if os.environ.get("USE_CPP_CORE", "").lower() in ("1", "true", "yes"):
    _cpp_build = Path(__file__).parent / "cpp" / "build"
    if _cpp_build.exists() and str(_cpp_build) not in sys.path:
        sys.path.insert(0, str(_cpp_build))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load C++ core and ML models on startup."""
    # Load C++ shared library or Python fallback
    try:
        import semiovis_core
        app.state.cpp_core = semiovis_core
        print("C++ core loaded: semiovis_core")
    except (ImportError, OSError) as e:
        print(f"C++ core not available ({e}) — using Python fallback")
        from core import python_fallback
        app.state.cpp_core = python_fallback

    # Download missing model files and load local ML models
    from models.download_models import ensure_models
    from core.local_models import LocalModels

    try:
        ensure_models()
        local_models = LocalModels()
        local_models.load()
        app.state.local_models = local_models
        print("Local ML models loaded")
    except Exception as e:
        print(f"WARNING: Could not load local ML models ({e})")
        app.state.local_models = None

    yield


app = FastAPI(
    title="SemioVis API",
    description="Semiotic image analysis based on Kress & van Leeuwen (2006)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(representational.router, prefix="/api/analyse")
app.include_router(interactive.router, prefix="/api/analyse")
app.include_router(compositional.router, prefix="/api/analyse")
app.include_router(dashboard.router, prefix="/api/analyse")
app.include_router(report.router, prefix="/api")


# --- Settings endpoint: receive API keys from frontend ---
from pydantic import BaseModel as _BM

class _ApiKeysPayload(_BM):
    gemini: str = ""
    openai: str = ""
    mistral: str = ""

@app.post("/api/settings/keys")
async def update_api_keys(payload: _ApiKeysPayload):
    """Receive API keys from the frontend Settings panel."""
    from core.vision_api import set_api_keys
    set_api_keys(payload.model_dump())
    return {"status": "ok"}
