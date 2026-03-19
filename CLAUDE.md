# CLAUDE.md — SemioVis
## Build Instructions for Claude Code

---

## 1. Project Overview

Build a cross-platform application called **`SemioVis`** that implements the analytical framework from:

> Kress, G., & van Leeuwen, T. (2006). *Reading Images: The Grammar of Visual Design* (2nd ed.). Routledge.

The app allows users to **import an image** and automatically perform — with interactive visualisations — the three fundamental semiotic analyses described in the book: **Representational**, **Interactive**, and **Compositional**.

### Deployment targets

| Target | Stack |
|---|---|
| **Desktop (Mac / Win / Linux)** | Tauri v2 shell → bundles React frontend + calls FastAPI backend locally |
| **SaaS / Web** | Same React frontend → calls FastAPI backend deployed on cloud (Docker / Kubernetes) |
| **Core C++** | Compiled as shared library, wrapped with **pybind11**, consumed by FastAPI |

---

## 2. Project Structure

```
SemioVis/
├── CLAUDE.md                        # this file
├── README.md
├── docker-compose.yml               # dev environment
├── Dockerfile                       # production backend image
│
├── backend/                         # Python FastAPI
│   ├── main.py                      # FastAPI app entry point
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── config.py                    # settings via pydantic-settings
│   ├── api/
│   │   ├── routes/
│   │   │   ├── upload.py            # POST /api/upload
│   │   │   ├── representational.py  # POST /api/analyse/representational
│   │   │   ├── interactive.py       # POST /api/analyse/interactive
│   │   │   ├── compositional.py     # POST /api/analyse/compositional
│   │   │   ├── dashboard.py         # GET  /api/analyse/full
│   │   │   └── report.py            # POST /api/report
│   │   └── models/                  # Pydantic response models
│   │       ├── image.py
│   │       ├── representational.py
│   │       ├── interactive.py
│   │       └── compositional.py
│   ├── core/
│   │   ├── vision_api.py            # Google Vision / OpenAI / AWS dispatcher
│   │   ├── local_models.py          # fully-local inference: YOLO, MediaPipe, ONNX
│   │   ├── local_interpretation.py  # rule-based semiotic interpretation (no LLM)
│   │   ├── color_analysis.py        # colour palette, harmony, temperature
│   │   ├── image_utils.py           # load, resize, normalise images
│   │   └── report_generator.py      # PDF / DOCX report builder
│   ├── models/                      # local ML model weights (~50MB total)
│   │   ├── .gitkeep
│   │   ├── download_models.py       # script to download models on first run
│   │   └── README.md                # model list, licenses, sources
│   ├── workers/
│   │   ├── celery_app.py            # Celery + Redis for async heavy tasks
│   │   └── tasks.py                 # background analysis tasks
│   └── cpp/                         # C++ core + pybind11 bindings
│       ├── CMakeLists.txt
│       ├── bindings.cpp             # pybind11 module definition
│       ├── saliency.cpp             # spectral residual + Itti-Koch saliency
│       ├── saliency.hpp
│       ├── vectors.cpp              # Hough line detection, vanishing point
│       ├── vectors.hpp
│       ├── spatial_grid.cpp         # zonal statistics (Given/New, Ideal/Real)
│       ├── spatial_grid.hpp
│       ├── color_features.cpp       # LAB/HSV feature extraction, k-means palette
│       ├── color_features.hpp
│       ├── texture_features.cpp     # Gabor filterbank, LBP
│       ├── texture_features.hpp
│       ├── depth_features.cpp       # monocular depth estimation (MiDaS/DPT via ONNX)
│       ├── depth_features.hpp
│       └── utils.cpp                # OpenCV <-> numpy bridge helpers
│
├── frontend/                        # React + TypeScript + Vite
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   └── client.ts            # Axios client (auto-switches desktop/SaaS base URL)
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Navbar.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   └── Layout.tsx
│       │   ├── upload/
│       │   │   ├── ImageUploader.tsx
│       │   │   └── ImagePreview.tsx
│       │   ├── representational/
│       │   │   ├── RepresentationalPanel.tsx
│       │   │   ├── VectorOverlay.tsx
│       │   │   └── ParticipantsTable.tsx
│       │   ├── interactive/
│       │   │   ├── InteractivePanel.tsx
│       │   │   ├── GazeOverlay.tsx
│       │   │   ├── ModalityRadar.tsx      # 8-axis radar chart (replaces single gauge)
│       │   │   ├── CodingOrientationSelector.tsx
│       │   │   └── PerspectiveCompass.tsx
│       │   ├── compositional/
│       │   │   ├── CompositionalPanel.tsx
│       │   │   ├── SaliencyHeatmap.tsx
│       │   │   ├── SemioticGrid.tsx
│       │   │   ├── ReadingPathOverlay.tsx  # animated reading path visualisation
│       │   │   ├── FramingBreakdown.tsx    # connection vs disconnection detail
│       │   │   └── ColorPalette.tsx
│       │   ├── dashboard/
│       │   │   └── DashboardPanel.tsx
│       │   └── report/
│       │       └── ReportPanel.tsx
│       ├── hooks/
│       │   ├── useImageAnalysis.ts
│       │   └── useSettings.ts
│       ├── store/
│       │   └── analysisStore.ts     # Zustand global state
│       ├── types/
│       │   └── analysis.ts          # TypeScript types matching Pydantic models
│       └── styles/
│           └── globals.css
│
├── desktop/                         # Tauri v2
│   ├── src-tauri/
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json
│   │   └── src/
│   │       ├── main.rs              # Tauri entry point
│   │       └── sidecar.rs           # spawns FastAPI backend as sidecar process
│   └── build-scripts/
│       ├── bundle_backend.py        # PyInstaller: packages FastAPI into binary
│       └── build_all.sh             # full cross-platform build script
│
├── tests/
│   ├── backend/
│   │   ├── test_saliency.py
│   │   ├── test_vectors.py
│   │   ├── test_compositional.py
│   │   └── test_api_routes.py
│   ├── frontend/
│   │   └── components/              # Vitest unit tests
│   └── cpp/
│       └── catch2_tests/            # Catch2 C++ unit tests
│
└── infra/
    ├── nginx.conf                   # reverse proxy for SaaS
    ├── k8s/                         # Kubernetes manifests
    └── terraform/                   # optional cloud provisioning
```

---

## 3. Technology Stack

### 3.1 Backend — Python

```
Python >= 3.11

fastapi              — async REST API framework
pydantic v2          — request/response validation and settings
pybind11             — C++ bindings (replaces Rcpp)
opencv-python        — OpenCV bindings
numpy                — array operations
Pillow               — image I/O and metadata
celery               — async task queue for heavy analyses (SaaS only, not Desktop)
redis                — celery broker + result caching (SaaS only, not Desktop)
onnxruntime          — run MiDaS/DPT depth model + emotion model (perspective, modality, faces)
httpx                — async HTTP client for Vision APIs (only needed if using cloud APIs)
python-dotenv        — environment variable management
reportlab            — PDF report generation
python-docx          — DOCX report generation
uvicorn              — ASGI server
gunicorn             — production process manager

# Local inference models (NO API keys required):
ultralytics          — YOLOv8 object detection + pose estimation
mediapipe            — face mesh (468 landmarks), gaze estimation, hand detection
```

### 3.1.1 Local Model Weights (`backend/models/`)

The app ships with (or auto-downloads on first run) a set of lightweight ML models
that provide **full functionality without any API keys**. Total size: ~55MB.

```
Model                          File                        Size    Purpose
─────────────────────────────  ──────────────────────────  ──────  ──────────────────────────────
YOLOv8n (object detection)     yolov8n.pt                  ~6MB   Object detection, participants
YOLOv8n-pose (body+keypoints)  yolov8n-pose.pt             ~7MB   Body bbox for social distance,
                                                                   body pose for power angle
YuNet (face detection)         face_detection_yunet.onnx   ~90KB  Face bounding boxes
MediaPipe Face Mesh            (bundled in mediapipe)       ~2MB   468 landmarks → gaze pan/tilt,
                                                                   head pose (demand/offer)
FER+ emotion (ONNX)            emotion-ferplus-8.onnx      ~34MB  7 basic emotions per face
MiDaS v2.1 small (depth)       midas_v21_small_256.onnx    ~5MB   Monocular depth estimation
```

### 3.2 Frontend — JavaScript/TypeScript

```
React 18 + TypeScript
Vite 5               — build tool and dev server
TailwindCSS v3       — utility-first styling
shadcn/ui            — accessible component library
Zustand              — lightweight global state
Plotly.js            — charts and data visualisation
Konva.js             — canvas-based image annotations (vectors, bboxes, grids)
React Query          — server state management and caching
Axios                — HTTP client
Lucide React         — icon library
```

### 3.3 Desktop — Tauri v2

```
Tauri v2 (Rust)      — native shell (~5 MB overhead)
  - bundles React frontend as embedded webview
  - spawns FastAPI backend as sidecar process via PyInstaller binary
  - handles OS-level: file dialogs, tray icon, auto-update, code signing

PyInstaller          — packages Python + FastAPI into a single executable
                        included in Tauri bundle (no Python install required)
```

### 3.4 C++ Core

```
C++ 17
OpenCV >= 4.8        — computer vision algorithms
Eigen3               — linear algebra (replaces Armadillo)
pybind11 >= 2.11     — Python bindings
CMake >= 3.22        — build system
Catch2 v3            — C++ unit tests
OpenMP               — parallelism
```

### 3.5 Infrastructure (SaaS)

```
Docker + Docker Compose   — containerisation
Nginx                     — reverse proxy / static frontend serving
Redis                     — task queue broker and cache
PostgreSQL (optional)     — persist analysis history for SaaS users
Fly.io / Railway / Render — simple SaaS deployment targets
Kubernetes (optional)     — full horizontal scaling
```

---

## 4. System Requirements (Development)

```bash
# macOS
brew install cmake opencv python@3.11 node rust
brew install redis

# Ubuntu / Debian
apt-get install -y cmake libopencv-dev python3.11-dev nodejs npm
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
apt-get install -y redis-server

# Windows
# Use WSL2 (Ubuntu) for C++ build, or vcpkg for OpenCV
winget install Rustlang.Rustup
winget install OpenJS.NodeJS
```

---

## 5. Environment Variables (`.env`)

```bash
# ALL API keys are OPTIONAL. The app works fully offline without any of these.
# Never commit this file.

# --- LLM Interpretation keys (pick one, or none for rule-based output) ---
# Priority order: OPENAI_API_KEY > GEMINI_API_KEY > MISTRAL_API_KEY > rule-based
GEMINI_API_KEY=...               # Google Gemini — FREE tier: 15 RPM, 1M tokens/day, vision support
OPENAI_API_KEY=...               # OpenAI GPT-4o — paid, best quality
MISTRAL_API_KEY=...              # Mistral / Pixtral — free tier available, vision support

# --- Vision API keys (for object/face detection; default is local YOLO+MediaPipe) ---
GOOGLE_VISION_KEY=...            # Google Cloud Vision — object/face/label detection
AWS_ACCESS_KEY_ID=...            # AWS Rekognition — face analysis, emotions
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# --- App config ---
APP_ENV=development              # development | production
API_HOST=0.0.0.0
API_PORT=8000
REDIS_URL=redis://localhost:6379/0   # only needed for SaaS with USE_CELERY=true

# Desktop mode: frontend sets this automatically
IS_DESKTOP=false
```

---

## 6. Backend Architecture

### 6.1 FastAPI Main (`backend/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes import upload, representational, interactive, compositional, dashboard, report

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load C++ shared library on startup
    import semiovis_core  # pybind11 module
    app.state.cpp_core = semiovis_core

    # Load local ML models (YOLO, MediaPipe, FER+, MiDaS) — no API keys needed
    from core.local_models import LocalModels
    from models.download_models import ensure_models
    ensure_models()              # download missing model files on first run
    local_models = LocalModels()
    local_models.load()
    app.state.local_models = local_models

    yield

app = FastAPI(
    title="SemioVis API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

app.include_router(upload.router,           prefix="/api")
app.include_router(representational.router, prefix="/api/analyse")
app.include_router(interactive.router,      prefix="/api/analyse")
app.include_router(compositional.router,    prefix="/api/analyse")
app.include_router(dashboard.router,        prefix="/api/analyse")
app.include_router(report.router,           prefix="/api")
```

**Desktop vs SaaS async strategy:**
- **Desktop (Tauri):** Do NOT use Celery/Redis. Use `asyncio` + `concurrent.futures.ProcessPoolExecutor` for CPU-bound C++ tasks. Set `USE_CELERY=false` in config. This avoids requiring a Redis installation on end-user machines.
- **SaaS:** Use Celery + Redis for horizontal scaling and background task queues. Set `USE_CELERY=true`.

```python
# backend/config.py
class Settings(BaseSettings):
    use_celery: bool = False           # True only for SaaS deployment
    reading_direction: str = "ltr"     # "ltr" or "rtl" — affects Given/New axis
    coding_orientation: str = "naturalistic"  # default modality coding orientation
    depth_model_path: str = ""         # path to MiDaS/DPT ONNX model

    # Detection backend: "local" (default, no API), "google", "aws"
    detection_backend: str = "local"

    # LLM interpretation: "auto" (cascade), "openai", "gemini", "mistral", "local"
    interpretation_llm: str = "auto"

    # API keys (all optional — app works fully without them)
    gemini_api_key: str = ""           # FREE: Google Gemini
    openai_api_key: str = ""           # Paid: GPT-4o
    mistral_api_key: str = ""          # Free tier: Pixtral
    google_vision_key: str = ""        # Google Cloud Vision
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
```

### 6.2 API Routes

All routes accept either:
- `image_id: str` — references a previously uploaded image (stored in `/tmp/semiovis_uploads/`)
- `image_url: str` — public image URL (downloaded server-side)

```
POST /api/upload
     Body: multipart/form-data { file: File }
     Returns: { image_id, width, height, format, exif_data, thumbnail_base64 }

POST /api/analyse/representational
     Body: { image_id, api_backend: "google"|"openai"|"aws"|"local" }
     Returns: RepresentationalResult

POST /api/analyse/interactive
     Body: { image_id, api_backend,
             coding_orientation: "naturalistic"|"sensory"|"technological"|"abstract" }
     Returns: InteractiveResult (includes 8-scale modality profile)

POST /api/analyse/compositional
     Body: { image_id, saliency_method: "spectral"|"itti", grid_size: "2x2"|"3x3",
             reading_direction: "ltr"|"rtl" }
     Returns: CompositionalResult (includes composition type, reading path, framing breakdown)

POST /api/analyse/full
     Body: { image_id, api_backend, saliency_method, grid_size }
     Returns: FullAnalysisResult (all three + GPT-4o interpretation)

POST /api/report
     Body: { image_id, analysis_results, format: "pdf"|"docx"|"html" }
     Returns: { download_url }
```

### 6.3 Pydantic Response Models (`backend/api/models/`)

```python
# representational.py
class Vector(BaseModel):
    x1: float; y1: float; x2: float; y2: float
    angle: float; strength: float
    direction: Literal["horizontal", "vertical", "diagonal"]

class Participant(BaseModel):
    label: str; confidence: float
    bbox: tuple[float, float, float, float]  # x1,y1,x2,y2 normalised [0-1]
    is_human: bool; is_animal: bool

class RepresentationalResult(BaseModel):
    structure_type: Literal["narrative", "conceptual"]
    # Narrative subtypes — Kress & vL, 2006, Ch. 2:
    #   transactional:         Actor → Goal via vector (p.74)
    #   non-transactional:     Actor + vector but no identifiable Goal (p.75)
    #   bidirectional:         two participants act on each other reciprocally (p.66)
    #   reactional:            vector is a gaze/eyeline (Reacter → Phenomenon) (p.67)
    #   mental:                thought bubble or dashed line (mental process)
    #   verbal:                speech bubble (verbal process)
    #   conversion:            participant is both Goal and Actor in different chains (p.68)
    narrative_subtype: Optional[Literal["transactional", "non_transactional",
                                         "bidirectional", "reactional",
                                         "mental", "verbal", "conversion"]]
    conceptual_subtype: Optional[Literal["classificational", "analytical", "symbolic"]]
    vectors: list[Vector]
    participants: list[Participant]
    vector_count: int
    dominant_direction: str
    interpretation: str  # GPT-4o generated text

# interactive.py
class FaceAnalysis(BaseModel):
    face_id: int
    face_bbox: tuple[float, float, float, float]   # face bounding box normalised [0-1]
    person_bbox: Optional[tuple[float, float, float, float]]  # full body bbox if available
    gaze_type: Literal["demand", "offer"]
    pan_angle: float; tilt_angle: float; roll_angle: float
    # Social distance based on BODY framing, not face size (Kress & vL, pp.124-128)
    social_distance: Literal["intimate", "personal", "social", "public", "very_public"]
    shot_type: Literal["extreme_close_up", "close_up", "medium_close",
                        "medium", "medium_long", "long", "very_long"]
    emotions: dict[str, float]

class ModalityProfile(BaseModel):
    """8 modality marker scales from Kress & vL, 2006, pp.160-163.
    Each scale ranges 0.0-1.0 where the meaning depends on coding_orientation."""
    colour_saturation: float       # full colour (1.0) ↔ black & white (0.0)       p.160
    colour_differentiation: float  # diversified palette (1.0) ↔ monochrome (0.0)  p.160
    colour_modulation: float       # fully modulated (1.0) ↔ flat/plain (0.0)      p.160
    contextualization: float       # detailed background (1.0) ↔ no background (0.0) p.161
    representation: float          # maximum detail (1.0) ↔ maximum abstraction (0.0) p.161
    depth: float                   # deep perspective (1.0) ↔ no perspective (0.0)  p.162
    illumination: float            # full light/shade play (1.0) ↔ none (0.0)      p.162
    brightness: float              # many brightness degrees (1.0) ↔ two only (0.0) p.162

class InteractiveResult(BaseModel):
    faces: list[FaceAnalysis]
    vertical_angle: Literal["high", "eye_level", "low"]
    horizontal_angle: Literal["frontal", "oblique"]
    power_relation: Literal["viewer_power", "equality", "subject_power"]
    involvement: Literal["high", "low"]
    # Modality: 8-scale profile, NOT a single score (Kress & vL, pp.160-163)
    # Markers can go in opposite directions in the same image (p.163, p.171)
    modality_profile: ModalityProfile
    # Coding orientation determines how to interpret the profile (pp.165-166, Fig. 5.5)
    coding_orientation: Literal["naturalistic", "sensory", "technological", "abstract"]
    # Composite score computed relative to the selected coding orientation
    modality_score: float          # 0 (low modality) -> 1 (high modality)
    vanishing_point: Optional[tuple[float, float]]
    interpretation: str

# compositional.py
class SpatialZone(BaseModel):
    zone_id: str
    position_label: str            # "top-left", "center", etc.
    semiotic_label: str            # "Given", "New", "Ideal", "Real", "Centre", "Margin"
    mean_saliency: float
    visual_weight: float
    color_temperature: Literal["warm", "neutral", "cool"]
    edge_density: float
    object_count: int
    # Additional salience factors from Kress & vL, 2006, p.202:
    tonal_contrast: float          # local vs global brightness difference
    colour_contrast: float         # chromatic contrast within zone
    has_human_figure: bool         # cultural salience boost for human presence
    foreground_ratio: float        # proportion of zone in foreground (from depth map)
    sharpness: float               # focus sharpness (Laplacian variance)
    information_value_score: float

class ColorSwatch(BaseModel):
    hex: str; rgb: tuple[int, int, int]
    proportion: float
    zone_association: str

class FramingAnalysis(BaseModel):
    """Detailed framing breakdown — Kress & vL, 2006, pp.203-204"""
    disconnection_score: float         # 0 (fully connected) -> 1 (strongly framed)
    connection_score: float            # 0 (fully disconnected) -> 1 (strongly connected)
    # Means of disconnection:
    frame_lines: list[dict]            # physical dividing lines detected
    empty_space_regions: int           # count of significant empty space gaps
    colour_discontinuities: int        # abrupt colour boundaries between zones
    # Means of connection:
    colour_continuities: int           # shared colour linking zones
    visual_vectors: int                # vectors leading eye between elements
    shape_rhymes: int                  # repeated shapes/forms across zones (visual "rhyme")

class ReadingPath(BaseModel):
    """Predicted reading path — Kress & vL, 2006, pp.204-208"""
    waypoints: list[dict]              # ordered [{x, y, saliency, label}] from most to least salient
    path_shape: Literal["linear_lr", "linear_tb", "circular", "spiral", "z_pattern", "irregular"]
    is_linear: bool                    # strictly coded reading path vs. non-linear (p.208)

class CompositionalResult(BaseModel):
    # Composition type detection — Kress & vL, 2006, pp.194-210, Fig. 6.21 (p.210)
    # FIRST classify as Centred or Polarized, THEN assign sub-labels.
    composition_type: Literal["centred", "polarized"]
    # Centred subtypes (p.194-199):
    centred_subtype: Optional[Literal["circular", "triptych", "centre_margin"]]
    # Polarized subtypes:
    polarization_axes: Optional[list[Literal["given_new", "ideal_real"]]]
    # Triptych structure (pp.197-199): Given | Mediator | New or Ideal | Mediator | Real
    has_triptych: bool
    triptych_orientation: Optional[Literal["horizontal", "vertical"]]

    zones: list[SpatialZone]
    saliency_map: list[list[float]]    # normalised 2D array (downsampled)
    color_palette: list[ColorSwatch]
    framing: FramingAnalysis           # detailed framing breakdown
    reading_path: ReadingPath          # predicted reading path (pp.204-208)
    dominant_structure: Literal["given_new", "ideal_real", "centre_margin",
                                "triptych", "circular", "mixed"]
    interpretation: str
```

---

## 7. C++ Core — pybind11 Module

### 7.1 CMake Setup (`backend/cpp/CMakeLists.txt`)

```cmake
cmake_minimum_required(VERSION 3.22)
project(semiovis_core CXX)

set(CMAKE_CXX_STANDARD 17)

find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(pybind11 REQUIRED)
find_package(OpenMP)

pybind11_add_module(semiovis_core
    bindings.cpp
    saliency.cpp
    vectors.cpp
    spatial_grid.cpp
    color_features.cpp
    texture_features.cpp
    depth_features.cpp
    utils.cpp
)

target_include_directories(semiovis_core PRIVATE
    ${OpenCV_INCLUDE_DIRS}
    ${EIGEN3_INCLUDE_DIR}
)

target_link_libraries(semiovis_core PRIVATE
    ${OpenCV_LIBS}
    Eigen3::Eigen
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(semiovis_core PRIVATE OpenMP::OpenMP_CXX)
endif()
```

### 7.2 pybind11 Bindings (`backend/cpp/bindings.cpp`)

```cpp
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "saliency.hpp"
#include "vectors.hpp"
#include "spatial_grid.hpp"
#include "color_features.hpp"
#include "texture_features.hpp"
#include "depth_features.hpp"

namespace py = pybind11;

PYBIND11_MODULE(semiovis_core, m) {
    m.doc() = "SemioVis — C++ core via pybind11";

    // Saliency
    m.def("compute_saliency_spectral", &compute_saliency_spectral,
          py::arg("img_rgb"),          // numpy array H x W x 3 uint8
          py::arg("scale_factor") = 1.0,
          "Spectral Residual saliency map (Hou & Zhang, 2007). Returns H x W float32.");

    m.def("compute_saliency_itti", &compute_saliency_itti,
          py::arg("img_rgb"),
          py::arg("scale_factor") = 1.0,
          "Itti-Koch-Niebur saliency map. Returns H x W float32.");

    // Vectors
    m.def("detect_vectors", &detect_vectors,
          py::arg("img_gray"),
          py::arg("rho") = 1.0,
          py::arg("theta") = CV_PI / 180.0,
          py::arg("threshold") = 100,
          py::arg("min_line_length") = 50.0,
          py::arg("max_line_gap") = 10.0,
          "Probabilistic Hough Lines. Returns list of dicts {x1,y1,x2,y2,angle,strength}.");

    m.def("estimate_vanishing_point", &estimate_vanishing_point,
          py::arg("img_gray"),
          "RANSAC vanishing point. Returns dict {vp_x, vp_y, v_angle, h_angle}.");

    m.def("detect_framing_lines", &detect_framing_lines,
          py::arg("img_gray"),
          py::arg("threshold1") = 50.0,
          py::arg("threshold2") = 150.0,
          "Canny + Hough framing detection. Returns framing_score [0-1] and line list.");

    // Spatial grid
    m.def("compute_spatial_zones", &compute_spatial_zones,
          py::arg("saliency_map"),     // H x W float32
          py::arg("img_rgb"),          // H x W x 3 uint8
          py::arg("n_cols") = 3,
          py::arg("n_rows") = 3,
          "Zonal statistics for semiotic grid. Returns list of zone dicts.");

    // Colour features — 8 modality scales (Kress & vL, 2006, pp.160-163)
    m.def("compute_modality_cues", &compute_modality_cues,
          py::arg("img_rgb"),
          "All 8 modality markers: colour_saturation, colour_differentiation, "
          "colour_modulation, contextualization, representation, depth, "
          "illumination, brightness. Returns dict with float values [0-1].");

    m.def("extract_color_palette", &extract_color_palette,
          py::arg("img_rgb"),
          py::arg("k") = 6,
          py::arg("max_iter") = 100,
          "k-means colour palette. Returns list of {rgb, hex, proportion}.");

    // Texture
    m.def("compute_texture_features", &compute_texture_features,
          py::arg("img_gray"),
          "Gabor filterbank + LBP. Returns feature dict.");

    // Depth estimation (for perspective analysis, foreground/background, modality depth marker)
    m.def("estimate_depth_map", &estimate_depth_map,
          py::arg("img_rgb"),
          py::arg("model_path") = "",   // path to MiDaS/DPT ONNX model
          "Monocular depth estimation. Returns H x W float32 normalised depth map.");

    // Reading path (Kress & vL, 2006, pp.204-208)
    m.def("compute_reading_path", &compute_reading_path,
          py::arg("saliency_map"),
          py::arg("max_waypoints") = 10,
          "Extract ordered salience peaks as predicted reading path waypoints.");
}
```

### 7.3 C++ Functions Reference

| Function | File | Algorithm |
|---|---|---|
| `compute_saliency_spectral` | `saliency.cpp` | FFT spectral residual |
| `compute_saliency_itti` | `saliency.cpp` | DoG + colour opponency |
| `detect_vectors` | `vectors.cpp` | Probabilistic Hough Lines |
| `estimate_vanishing_point` | `vectors.cpp` | RANSAC on Hough lines |
| `detect_framing_lines` | `vectors.cpp` | Canny + Hough |
| `compute_spatial_zones` | `spatial_grid.cpp` | Zonal statistics |
| `compute_modality_cues` | `color_features.cpp` | All 8 modality markers: LAB/HSV saturation, differentiation, modulation, Laplacian detail, depth proxy, illumination, brightness range, background complexity |
| `extract_color_palette` | `color_features.cpp` | k-means on RGB pixels |
| `compute_texture_features` | `texture_features.cpp` | Gabor filterbank + LBP |
| `estimate_depth_map` | `depth_features.cpp` | Monocular depth estimation via OpenCV DNN (MiDaS/DPT ONNX model) — used for perspective analysis, foreground/background separation, and depth modality marker |
| `compute_reading_path` | `saliency.cpp` | Extract ordered salience waypoints from saliency map to predict visual reading path (Kress & vL, pp.204-208) |

**Performance rules:**
- All functions accept `numpy.ndarray` via pybind11 numpy interface — zero-copy where possible
- Auto-downsample internally for images larger than 2000×2000 px
- Use `#pragma omp parallel for` for pixel-level loops
- Return Python-native types (list of dicts, numpy arrays)

---

## 8. Semiotic Analysis Logic

### 8.1 Representational Analysis (`backend/api/routes/representational.py`)

```python
async def analyse_representational(image_id, api_backend):
    img = load_image(image_id)
    img_gray = to_grayscale(img)

    # C++ vector detection
    raw_vectors = cpp_core.detect_vectors(img_gray, min_line_length=50)
    vectors = classify_vectors(raw_vectors)   # horizontal / vertical / diagonal

    # Vision API participant detection
    participants = await call_vision_api(img, features=["objects","faces"], api=api_backend)

    # Structure classification (Kress & vL, 2006, Ch. 2-3)
    structure = classify_narrative_structure(vectors, participants)
    # Narrative subtypes (Ch. 2):
    #   transactional:     vector connects Actor → Goal (one direction)          p.74
    #   non-transactional: Actor + vector but no identifiable Goal               p.75
    #   bidirectional:     two participants act on each other reciprocally       p.66
    #   reactional:        vector is a gaze/eyeline (Reacter → Phenomenon)      p.67
    #   mental:            thought bubble or dashed line (mental process)
    #   verbal:            speech bubble (verbal process)
    #   conversion:        participant is both Goal and Actor in diff. chains    p.68
    # Conceptual subtypes (Ch. 3):
    #   classificational:  taxonomic tree structure (superordinate/subordinate)  p.79
    #   analytical:        part-whole relationship (Carrier + Possessive Attr.)  p.87
    #   symbolic:          what a participant means/is (Carrier + Symbolic Attr.) p.105
```

### 8.2 Interactive Analysis (`backend/api/routes/interactive.py`)

```python
def classify_gaze(pan_angle, tilt_angle):
    # Kress & vL, 2006, p.117
    return "demand" if abs(pan_angle) < 15 and abs(tilt_angle) < 15 else "offer"

def classify_social_distance(person_bbox, img_shape):
    # Kress & vL, 2006, pp.124-128 — based on BODY framing, not face size.
    # The book maps Hall's (1966) proxemics to film shot types:
    #   Close shot (head+shoulders) → intimate/personal distance    p.124-125
    #   Medium shot (waist up)      → close social distance
    #   Medium long (knees up)      → far social distance
    #   Long shot (full figure)     → public distance
    #   Very long shot (figure+env) → very public / impersonal
    # Use person detection bbox (full body), NOT face bbox.
    # If only face bbox is available, estimate body from face landmarks.
    person_height_ratio = person_bbox[3] / img_shape[0]  # normalised height
    if person_height_ratio > 0.80: return "intimate"      # head+shoulders fill frame
    if person_height_ratio > 0.60: return "personal"       # waist up
    if person_height_ratio > 0.40: return "social"         # knees up / medium shot
    if person_height_ratio > 0.20: return "public"         # full figure
    return "very_public"                                    # figure + wide environment

def compute_modality_score(profile: ModalityProfile, orientation: str = "naturalistic"):
    """Compute modality score relative to a coding orientation.
    Kress & vL, 2006, pp.160-175, esp. Fig. 5.5 (p.166).

    The SAME marker value means different things in different orientations:
    - Naturalistic: moderate values = highest modality (photographic norm)
    - Sensory:      high saturation/detail = high modality (pleasure principle)
    - Technological: low colour/texture = high modality (blueprint effectiveness)
    - Abstract:     reduction to essentials = high modality (academic/scientific)

    Each scale is non-linear: highest modality is NOT at the extreme but at
    the culturally-defined 'norm' for that orientation (p.160, Fig. 5.4).
    """
    markers = [profile.colour_saturation, profile.colour_differentiation,
               profile.colour_modulation, profile.contextualization,
               profile.representation, profile.depth,
               profile.illumination, profile.brightness]

    if orientation == "naturalistic":
        # Highest modality at moderate values (photographic standard)
        # Distance from ~0.6-0.7 midpoint reduces modality
        return 1.0 - np.mean([abs(m - 0.65) for m in markers]) / 0.65
    elif orientation == "sensory":
        # High values = high modality (maximal sensory impact)
        return np.mean(markers)
    elif orientation == "technological":
        # Low colour/texture = high modality (functional effectiveness)
        return 1.0 - np.mean(markers)
    elif orientation == "abstract":
        # Reduction = high modality; but some markers invert
        return 1.0 - np.mean([profile.colour_saturation,
                               profile.contextualization,
                               profile.representation,
                               profile.depth])
    return np.mean(markers)  # fallback
```

### 8.3 Compositional Analysis (`backend/api/routes/compositional.py`)

```python
def classify_composition_type(saliency_map, zones):
    """First step: determine if composition is Centred or Polarized.
    Kress & vL, 2006, pp.194-210, esp. Fig. 6.15 (p.197) and Fig. 6.21 (p.210).

    Centred: dominant visual weight in the centre of the image.
    Polarized: visual weight distributed along axes (left-right and/or top-bottom).
    """
    centre_weight = get_centre_zone_weight(saliency_map)
    peripheral_weights = get_peripheral_weights(saliency_map)
    lr_asymmetry = abs(peripheral_weights["left"] - peripheral_weights["right"])
    tb_asymmetry = abs(peripheral_weights["top"] - peripheral_weights["bottom"])

    if centre_weight > 0.4 * sum(peripheral_weights.values()):
        comp_type = "centred"
        # Detect subtypes: Circular, Triptych, Centre-Margin (pp.194-199)
        if is_triptych_structure(zones):
            subtype = "triptych"
        elif is_circular_arrangement(zones):
            subtype = "circular"
        else:
            subtype = "centre_margin"
    else:
        comp_type = "polarized"
        subtype = None

    return comp_type, subtype

def assign_semiotic_labels(zones, n_rows, n_cols, composition_type, reading_direction="ltr"):
    """Assign semiotic labels based on composition type and cultural reading direction.
    Kress & vL, 2006, pp.180-214.

    IMPORTANT: In RTL cultures (Arabic, Hebrew), Given and New are REVERSED
    (p.181, Fig. 6.3 — Sony English vs Arabic website comparison).
    """
    # Determine label mapping based on reading direction
    if reading_direction == "ltr":
        left_label, right_label = "Given", "New"       # p.180-181
    else:  # rtl
        left_label, right_label = "New", "Given"       # p.181

    for zone in zones:
        col, row = zone["col"], zone["row"]
        labels = []

        if composition_type == "polarized":
            # Horizontal axis: Given/New (pp.179-185)
            if col == 0:                        labels.append(left_label)
            elif col == n_cols - 1:             labels.append(right_label)
            # Vertical axis: Ideal/Real (pp.186-193)
            if row == 0:                        labels.append("Ideal")
            elif row == n_rows - 1:             labels.append("Real")
        elif composition_type == "centred":
            # Centre/Margin structure (pp.194-197)
            if n_rows == 3 and n_cols == 3:
                if row == 1 and col == 1:
                    labels = ["Centre"]         # Mediator / nucleus
                else:
                    labels = ["Margin"]
                    # In polarized-centred hybrids, margins can also carry
                    # Given/New/Ideal/Real labels (Fig. 6.15, p.197)
                    if col == 0: labels.append(left_label)
                    elif col == n_cols - 1: labels.append(right_label)
                    if row == 0: labels.append("Ideal")
                    elif row == n_rows - 1: labels.append("Real")

        zone["semiotic_label"] = " / ".join(labels) or "Margin"
    return zones
```

### 8.4 Semiotic Interpretation (LLM Cascade)

The interpretation step uses the **LLM cascade** described in Section 9.4.
It works at three quality levels:

1. **With LLM + image** (GPT-4o, Gemini, Pixtral): sends the image + extracted features → rich, contextual academic text
2. **With LLM, text only** (if image sending fails): sends only extracted features → good text, less image-specific
3. **Rule-based local** (no API key): generates deterministic structured text from templates → always available

```python
# Called from each analysis route:
interpretation = await generate_interpretation(
    analysis_type="representational",   # or "interactive", "compositional", "full"
    data=analysis_results,              # dict of extracted features
    img_base64=img_base64,              # optional: image for multimodal LLMs
    preferred_llm=settings.interpretation_llm  # "auto", "gemini", "openai", etc.
)
```

---

## 9. Vision API Integration

### 9.1 Unified Dispatcher (`backend/core/vision_api.py`)

```python
async def call_vision_api(img_path, features, api="local"):
    """
    Unified dispatcher. Returns standardised response regardless of backend.
    features: list of "objects" | "faces" | "labels" | "text" | "persons"

    DEFAULT is "local" — the app works fully offline with no API keys.
    Cloud APIs (google, openai, aws) are optional enhancements.
    """
    match api:
        case "local":   return await _call_local_models(img_path, features)
        case "google":  return await _call_google_vision(img_path, features)
        case "openai":  return await _call_openai_vision(img_path, features)
        case "aws":     return await _call_aws_rekognition(img_path, features)

# Standardised "objects" output (same format for ALL backends):
# [{ "label": str, "confidence": float, "bbox": [x1,y1,x2,y2] normalised 0-1,
#    "is_human": bool, "is_animal": bool }]

# Standardised "faces" output:
# [{ "face_id": int, "face_bbox": [x1,y1,x2,y2], "person_bbox": [x1,y1,x2,y2] | null,
#    "pan_angle": float, "tilt_angle": float, "roll_angle": float,
#    "emotions": { "joy": float, "sorrow": float, "anger": float, ... } }]

# Standardised "persons" output (for social distance — body-based):
# [{ "person_id": int, "bbox": [x1,y1,x2,y2],
#    "keypoints": [[x,y,conf], ...] | null,   # 17 COCO keypoints if available
#    "associated_face_id": int | null }]
```

### 9.2 Local Backend — Full Offline Mode (`backend/core/local_models.py`)

**This is the DEFAULT backend.** No API keys, no internet connection required.

```python
from ultralytics import YOLO
import mediapipe as mp
import onnxruntime as ort
import numpy as np
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"

class LocalModels:
    """Singleton — loaded once at app startup, shared across requests."""

    def __init__(self):
        self._yolo_detect = None
        self._yolo_pose = None
        self._face_mesh = None
        self._emotion_session = None

    def load(self):
        """Load all models. Called during FastAPI lifespan startup."""
        # Object detection: YOLOv8n (COCO 80 classes)
        self._yolo_detect = YOLO(str(MODEL_DIR / "yolov8n.pt"))

        # Person detection + body keypoints: YOLOv8n-pose (17 COCO keypoints)
        self._yolo_pose = YOLO(str(MODEL_DIR / "yolov8n-pose.pt"))

        # Face mesh: MediaPipe (468 landmarks → pan/tilt/roll estimation)
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=20,
            refine_landmarks=True,     # includes iris landmarks for gaze
            min_detection_confidence=0.5
        )

        # Emotion recognition: FER+ ONNX model
        self._emotion_session = ort.InferenceSession(
            str(MODEL_DIR / "emotion-ferplus-8.onnx")
        )

    async def detect_objects(self, img: np.ndarray) -> list[dict]:
        """YOLOv8 object detection → standardised participant list."""
        results = self._yolo_detect(img, verbose=False)[0]
        participants = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id]
            x1, y1, x2, y2 = box.xyxyn[0].tolist()  # normalised [0-1]
            participants.append({
                "label": label,
                "confidence": float(box.conf[0]),
                "bbox": [x1, y1, x2, y2],
                "is_human": label == "person",
                "is_animal": label in ("cat", "dog", "horse", "bird", "cow",
                                       "sheep", "elephant", "bear", "zebra", "giraffe"),
            })
        return participants

    async def detect_persons(self, img: np.ndarray) -> list[dict]:
        """YOLOv8-pose: full body bboxes + 17 COCO keypoints.
        Used for body-based social distance (Kress & vL, pp.124-128)."""
        results = self._yolo_pose(img, verbose=False)[0]
        persons = []
        for i, box in enumerate(results.boxes):
            if int(box.cls[0]) != 0:  # class 0 = person
                continue
            x1, y1, x2, y2 = box.xyxyn[0].tolist()
            kpts = results.keypoints[i].xyn[0].tolist() if results.keypoints else None
            persons.append({
                "person_id": i,
                "bbox": [x1, y1, x2, y2],
                "keypoints": kpts,     # 17 keypoints: nose, eyes, ears, shoulders, ...
                "confidence": float(box.conf[0]),
            })
        return persons

    async def detect_faces(self, img_rgb: np.ndarray) -> list[dict]:
        """MediaPipe Face Mesh → face bbox, head pose (pan/tilt/roll), gaze direction.

        Gaze estimation from iris landmarks:
        MediaPipe refine_landmarks=True provides 10 iris points (landmarks 468-477).
        Combined with the 6-point head pose model (nose tip, chin, eye corners,
        mouth corners), we compute pan_angle and tilt_angle.

        Demand/Offer rule (Kress & vL, p.117):
          |pan_angle| < 15° AND |tilt_angle| < 15° → "demand" (direct address)
          otherwise → "offer" (subject of contemplation)
        """
        results = self._face_mesh.process(img_rgb)
        faces = []
        if not results.multi_face_landmarks:
            return faces

        h, w = img_rgb.shape[:2]
        for i, face_lm in enumerate(results.multi_face_landmarks):
            # Extract face bounding box from landmarks
            xs = [lm.x for lm in face_lm.landmark]
            ys = [lm.y for lm in face_lm.landmark]
            face_bbox = [min(xs), min(ys), max(xs), max(ys)]

            # Head pose estimation from 6 canonical points
            pan, tilt, roll = estimate_head_pose(face_lm.landmark, w, h)

            # Emotion from cropped face via FER+ ONNX
            emotions = self._predict_emotions(img_rgb, face_bbox, w, h)

            faces.append({
                "face_id": i,
                "face_bbox": face_bbox,
                "pan_angle": pan,
                "tilt_angle": tilt,
                "roll_angle": roll,
                "gaze_type": "demand" if abs(pan) < 15 and abs(tilt) < 15 else "offer",
                "emotions": emotions,
            })
        return faces

    def _predict_emotions(self, img_rgb, face_bbox, w, h) -> dict:
        """FER+ emotion recognition on cropped face."""
        x1, y1, x2, y2 = [int(v * d) for v, d in zip(face_bbox, [w, h, w, h])]
        face_crop = img_rgb[max(0,y1):y2, max(0,x1):x2]
        # Preprocess: resize to 64x64, grayscale, normalise
        import cv2
        face_gray = cv2.cvtColor(cv2.resize(face_crop, (64, 64)), cv2.COLOR_RGB2GRAY)
        input_tensor = face_gray.astype(np.float32).reshape(1, 1, 64, 64)
        probs = self._emotion_session.run(None, {"Input3": input_tensor})[0][0]
        probs = np.exp(probs) / np.exp(probs).sum()  # softmax
        labels = ["neutral", "happiness", "surprise", "sadness",
                  "anger", "disgust", "fear", "contempt"]
        return {l: float(p) for l, p in zip(labels, probs)}


def estimate_head_pose(landmarks, img_w, img_h):
    """Estimate pan (yaw), tilt (pitch), roll from MediaPipe 468 landmarks.
    Uses solvePnP with a canonical 3D face model."""
    import cv2
    # 6 canonical 2D-3D point correspondences
    model_points = np.array([
        (0.0, 0.0, 0.0),        # nose tip
        (0.0, -330.0, -65.0),   # chin
        (-225.0, 170.0, -135.0), # left eye corner
        (225.0, 170.0, -135.0),  # right eye corner
        (-150.0, -150.0, -125.0),# left mouth corner
        (150.0, -150.0, -125.0), # right mouth corner
    ], dtype=np.float64)

    # Corresponding MediaPipe landmark indices
    indices = [1, 152, 33, 263, 61, 291]
    image_points = np.array([
        (landmarks[i].x * img_w, landmarks[i].y * img_h) for i in indices
    ], dtype=np.float64)

    focal_length = img_w
    camera_matrix = np.array([
        [focal_length, 0, img_w / 2],
        [0, focal_length, img_h / 2],
        [0, 0, 1]
    ], dtype=np.float64)

    _, rotation_vec, _ = cv2.solvePnP(model_points, image_points,
                                       camera_matrix, np.zeros((4, 1)))
    rotation_mat, _ = cv2.Rodrigues(rotation_vec)
    angles = cv2.decomposeProjectionMatrix(
        np.hstack((rotation_mat, np.zeros((3, 1))))
    )[6]

    pan = float(angles[1, 0])   # yaw: left-right
    tilt = float(angles[0, 0])  # pitch: up-down
    roll = float(angles[2, 0])  # roll: head tilt
    return pan, tilt, roll
```

### 9.3 Local Interpretation — Rule-Based (`backend/core/local_interpretation.py`)

When no OpenAI API key is available, the app generates **structured semiotic text**
using rule-based templates instead of GPT-4o. The interpretation is less nuanced
but academically correct and reproducible.

```python
def generate_local_interpretation(analysis_type: str, data: dict) -> str:
    """Generate rule-based semiotic interpretation without LLM.

    Uses template sentences derived from Kress & van Leeuwen's terminology.
    Output is structured, citable, and deterministic.
    """
    match analysis_type:
        case "representational":
            return _interpret_representational(data)
        case "interactive":
            return _interpret_interactive(data)
        case "compositional":
            return _interpret_compositional(data)
        case "full":
            return "\n\n".join([
                _interpret_representational(data.get("representational", {})),
                _interpret_interactive(data.get("interactive", {})),
                _interpret_compositional(data.get("compositional", {})),
            ])

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
                    "(Kress & van Leeuwen, 2006, p.74)."
                )
            case "reactional":
                parts.append(
                    "The structure is reactional: the primary vector is formed "
                    "by an eyeline, connecting a Reacter to a Phenomenon "
                    "(Kress & van Leeuwen, 2006, p.67)."
                )
            case "non_transactional":
                parts.append(
                    "The structure is non-transactional: the Actor initiates "
                    "a vector but no identifiable Goal is present, leaving "
                    "the action open-ended (Kress & van Leeuwen, 2006, p.75)."
                )
            case "bidirectional":
                parts.append(
                    "The structure is bidirectional: two participants act on "
                    "each other reciprocally (Kress & van Leeuwen, 2006, p.66)."
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
            f"{demands} 'demand' (direct gaze at the viewer) and {offers} 'offer' "
            f"(gaze directed elsewhere). "
        )
        if demands > offers:
            parts.append(
                "The dominant mode is 'demand': the represented participant(s) "
                "address the viewer directly, creating an imaginary social relation "
                "(Kress & van Leeuwen, 2006, p.117-118)."
            )
        else:
            parts.append(
                "The dominant mode is 'offer': the represented participants are "
                "presented as objects of contemplation for the viewer's dispassionate "
                "scrutiny (Kress & van Leeuwen, 2006, p.119)."
            )
    else:
        parts.append(
            "No human faces are detected. The image functions as an 'offer', "
            "presenting its content impersonally to the viewer."
        )

    va = data.get("vertical_angle", "eye_level")
    ha = data.get("horizontal_angle", "frontal")
    parts.append(
        f"The vertical angle is {va.replace('_', ' ')}, suggesting "
        f"{'viewer power over the subject' if va == 'high' else 'equality between viewer and subject' if va == 'eye_level' else 'subject power over the viewer'} "
        f"(p.140). The horizontal angle is {ha}, encoding "
        f"{'involvement and identification' if ha == 'frontal' else 'detachment and otherness'} "
        f"(p.136)."
    )

    ms = data.get("modality_score", 0)
    co = data.get("coding_orientation", "naturalistic")
    parts.append(
        f"The modality score is {ms:.2f} under {co} coding orientation "
        f"(Kress & van Leeuwen, 2006, pp.165-166)."
    )

    return " ".join(parts)

def _interpret_compositional(data: dict) -> str:
    parts = []
    comp_type = data.get("composition_type", "polarized")
    dom = data.get("dominant_structure", "mixed")

    parts.append(
        f"The composition is {comp_type}. "
    )

    if comp_type == "centred":
        sub = data.get("centred_subtype", "centre_margin")
        parts.append(
            f"The structure is {sub.replace('_', '-')}: a central element acts as "
            f"the nucleus of information, with marginal elements in a subordinate "
            f"role (Kress & van Leeuwen, 2006, pp.194-197)."
        )
    else:
        axes = data.get("polarization_axes", [])
        if "given_new" in axes:
            parts.append(
                "A Given-New (left-right) axis is present: the left side presents "
                "familiar, established information, while the right presents the "
                "message, the 'issue' (pp.180-181)."
            )
        if "ideal_real" in axes:
            parts.append(
                "An Ideal-Real (top-bottom) axis is present: the top presents "
                "the generalised, aspirational essence, while the bottom shows "
                "practical, specific, evidential detail (pp.186-187)."
            )

    framing = data.get("framing", {})
    disc = framing.get("disconnection_score", 0)
    parts.append(
        f"Framing analysis shows a disconnection score of {disc:.2f} "
        f"({'strong separation between elements' if disc > 0.6 else 'moderate framing' if disc > 0.3 else 'weak framing, elements presented as connected'}), "
        f"(pp.203-204)."
    )

    rp = data.get("reading_path", {})
    if rp:
        shape = rp.get("path_shape", "irregular")
        parts.append(
            f"The predicted reading path follows a {shape.replace('_', ' ')} "
            f"pattern (pp.204-208)."
        )

    return " ".join(parts)
```

### 9.4 Interpretation Dispatcher — LLM Cascade

The app uses a **priority cascade** for semiotic text interpretation:

1. **OpenAI GPT-4o** (if `OPENAI_API_KEY` set) — best quality, paid
2. **Google Gemini 2.0 Flash** (if `GEMINI_API_KEY` set) — **FREE tier**, vision support, excellent quality
3. **Mistral Pixtral** (if `MISTRAL_API_KEY` set) — free tier, vision support
4. **Rule-based local** (always available) — no API key, deterministic, academically correct

The user can override the cascade in Settings by explicitly selecting a backend.

```python
# backend/core/vision_api.py — interpretation dispatcher

import os, httpx, json

SEMIOTIC_PROMPT = """You are an expert in social semiotics specialising in
Kress and van Leeuwen's visual grammar (Reading Images, 2006).

Extracted features:
{features_json}

Provide a {analysis_type} analysis covering:
- How meaning is constructed through this dimension
- Specific visual elements that carry semiotic weight
- The communicative strategy implied
- Reference to Kress & van Leeuwen with page numbers where possible

Write in academic English, approximately 150-200 words."""


async def generate_interpretation(analysis_type: str, data: dict,
                                   img_base64: str | None = None,
                                   preferred_llm: str = "auto") -> str:
    """Generate semiotic interpretation using the best available LLM.

    preferred_llm: "auto" (cascade), "openai", "gemini", "mistral", "local"
    """
    features_json = json.dumps(data, indent=2, default=str)
    prompt = SEMIOTIC_PROMPT.format(features_json=features_json,
                                     analysis_type=analysis_type)

    if preferred_llm == "auto":
        # Priority cascade
        for backend in ["openai", "gemini", "mistral", "local"]:
            result = await _try_llm(backend, prompt, img_base64)
            if result:
                return result
        # Should never reach here — local always works
        from core.local_interpretation import generate_local_interpretation
        return generate_local_interpretation(analysis_type, data)
    else:
        result = await _try_llm(preferred_llm, prompt, img_base64)
        if result:
            return result
        # Fallback to local if preferred LLM fails
        from core.local_interpretation import generate_local_interpretation
        return generate_local_interpretation(analysis_type, data)


async def _try_llm(backend: str, prompt: str, img_base64: str | None) -> str | None:
    """Try a specific LLM backend. Returns None if key missing or call fails."""
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
                # Parse analysis_type from prompt (or pass as param)
                return generate_local_interpretation("full", {})
    except Exception:
        return None


async def _call_openai_llm(prompt: str, img_base64: str | None) -> str | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    async with httpx.AsyncClient() as client:
        content = []
        if img_base64:
            content.append({"type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}})
        content.append({"type": "text", "text": prompt})
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "gpt-4o", "messages": [{"role": "user", "content": content}],
                  "max_tokens": 500},
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_gemini_llm(prompt: str, img_base64: str | None) -> str | None:
    """Google Gemini 2.0 Flash — FREE tier: 15 RPM, 1M tokens/day.
    Supports vision (image input). Excellent quality for semiotic analysis."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    async with httpx.AsyncClient() as client:
        parts = []
        if img_base64:
            parts.append({"inline_data": {"mime_type": "image/jpeg",
                                           "data": img_base64}})
        parts.append({"text": prompt})
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={key}",
            json={"contents": [{"parts": parts}],
                  "generationConfig": {"maxOutputTokens": 500}},
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _call_mistral_llm(prompt: str, img_base64: str | None) -> str | None:
    """Mistral Pixtral — free tier available, supports vision."""
    key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not key:
        return None
    async with httpx.AsyncClient() as client:
        content = []
        if img_base64:
            content.append({"type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}})
        content.append({"type": "text", "text": prompt})
        resp = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "pixtral-12b-2409",
                  "messages": [{"role": "user", "content": content}],
                  "max_tokens": 500},
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
```

### 9.5 Model Download Script (`backend/models/download_models.py`)

```python
"""Download all required local models on first run.
Called automatically during app startup if models are missing."""

import urllib.request
from pathlib import Path

MODEL_DIR = Path(__file__).parent
MODELS = {
    "yolov8n.pt": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt",
    "yolov8n-pose.pt": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n-pose.pt",
    "emotion-ferplus-8.onnx": "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx",
    "midas_v21_small_256.onnx": "https://github.com/isl-org/MiDaS/releases/download/v2_1/midas_v21_small_256.onnx",
}

def ensure_models():
    """Download any missing model files."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in MODELS.items():
        path = MODEL_DIR / filename
        if not path.exists():
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, path)
            print(f"  → saved to {path} ({path.stat().st_size / 1e6:.1f} MB)")

if __name__ == "__main__":
    ensure_models()
```

### 9.6 Feature Comparison: Local vs Cloud

**Detection backends:**

| Feature | Local (default) | Google Vision | AWS Rekognition |
|---|---|---|---|
| Object detection | YOLOv8n (80 COCO classes) | 10K+ classes | 10K+ classes |
| Face detection | MediaPipe (468 landmarks) | Face + landmarks | Face + 27 landmarks |
| Gaze estimation (Demand/Offer) | MediaPipe iris + head pose | Face orientation angles | Head pose (pitch/yaw/roll) |
| Body detection (social distance) | YOLOv8n-pose (17 keypoints) | N/A | N/A |
| Emotion recognition | FER+ ONNX (7 emotions) | Joy/sorrow/anger/surprise | 8 emotions + confidence |
| Depth estimation | MiDaS v2.1 small | N/A | N/A |
| **Internet required** | **No** | Yes | Yes |
| **API key required** | **No** | Yes | Yes |
| **Latency** | ~1-3s | ~2-5s | ~2-4s |
| **Cost per image** | **Free** | ~$0.003 | ~$0.002 |

**LLM interpretation backends (cascade priority):**

| LLM | Free tier | Vision | Quality | How to enable |
|---|---|---|---|---|
| **Rule-based local** | Always free | N/A | Structured, deterministic | Always available (fallback) |
| **Google Gemini 2.0 Flash** | 15 RPM, 1M tok/day | Yes | Excellent | Set `GEMINI_API_KEY` — **recommended free option** |
| **Mistral Pixtral** | Limited free tier | Yes | Good | Set `MISTRAL_API_KEY` |
| **OpenAI GPT-4o** | No free tier | Yes | Best | Set `OPENAI_API_KEY` — paid |

The cascade (`auto` mode) tries each LLM in order: OpenAI → Gemini → Mistral → Local.
Users who want better interpretation without paying can get a **free Gemini API key**
from Google AI Studio and set it in the app Settings panel.

---

## 10. Frontend Architecture

### 10.1 Global State (`frontend/src/store/analysisStore.ts`)

```typescript
import { create } from 'zustand'

interface AnalysisStore {
  imageId:          string | null
  imageMeta:        ImageMeta | null
  representational: RepresentationalResult | null
  interactive:      InteractiveResult | null
  compositional:    CompositionalResult | null
  isLoading:        Record<string, boolean>
  activeTab:        'upload' | 'representational' | 'interactive' |
                    'compositional' | 'dashboard' | 'report'
  settings:         AppSettings
  setImage:         (id: string, meta: ImageMeta) => void
  setResult:        (type: string, result: any) => void
  setLoading:       (type: string, val: boolean) => void
  setActiveTab:     (tab: string) => void
  updateSettings:   (s: Partial<AppSettings>) => void
  resetAll:         () => void
}
```

### 10.2 API Client (`frontend/src/api/client.ts`)

```typescript
// Desktop: FastAPI runs locally on port 8000
// SaaS:    VITE_API_URL environment variable points to cloud backend
const BASE_URL = import.meta.env.VITE_API_URL
  ?? (window.__TAURI__ ? 'http://localhost:8000' : '/api')

export const apiClient = axios.create({ baseURL: BASE_URL })
```

### 10.3 Image Annotation Components

Use **Konva.js** for all canvas overlays:

```
VectorOverlay.tsx       — Konva.Arrow for each detected vector
                          horizontal=blue | vertical=red | diagonal=orange

GazeOverlay.tsx         — face bboxes + gaze direction arrows
                          "Demand" = red border | "Offer" = grey border

SemioticGrid.tsx        — grid with semiotic zone labels
                          adapts to Centred vs Polarized composition type
                          cells colour-coded by information_value_score
                          hover tooltip shows zone scores + semiotic labels

SaliencyHeatmap.tsx     — saliency map as semi-transparent overlay
                          toggle on/off | colour scale: blue->yellow->red

ReadingPathOverlay.tsx  — animated polyline connecting salience waypoints
                          numbered waypoints (1→2→3...) showing reading order
                          path shape classification label (circular, Z-pattern, etc.)

ModalityRadar.tsx       — Plotly.js radar chart with 8 modality axes
                          shows profile shape, NOT a single score
                          overlay of "ideal" shape for selected coding orientation
```

### 10.4 App Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  SemioVis                    [Settings]  [Help]      │
├──────────────┬──────────────────────────────────────────────────────┤
│  [thumbnail] │  Upload | Representational | Interactive |           │
│  filename    │  Compositional | Dashboard | Report                  │
│  800x600 px  │ ┌──────────────────────────────────────────────────┐ │
│  JPEG        │ │                                                  │ │
│  ──────────  │ │           Active Panel Content                   │ │
│  [Upload]    │ │     (annotated image + charts + tables)          │ │
│  [Analyse ▶] │ │                                                  │ │
│              │ └──────────────────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────────────┘
```

---

## 11. Desktop Build (Tauri v2)

### 11.1 Architecture

```
Tauri App
├── Embedded WebView  →  serves React production build (dist/)
└── Rust sidecar      →  spawns FastAPI binary on app startup
      src/sidecar.rs:
        - find a free port (default 8000)
        - spawn ./bin/semiovis_api  (PyInstaller binary)
        - pass port via env: API_PORT=<port>
        - kill sidecar process on app exit
```

### 11.2 PyInstaller Bundle

```bash
# desktop/build-scripts/bundle_backend.py
pyinstaller backend/main.py \
    --name semiovis_api \
    --onefile \
    --hidden-import=semiovis_core \
    --add-binary="backend/cpp/build/semiovis_core*.so:." \
    --distpath desktop/src-tauri/bin/
```

### 11.3 Build Commands

```bash
# 1. Build C++ core
cd backend/cpp && cmake -B build && cmake --build build

# 2. Dev mode
cd backend  && uvicorn main:app --reload --port 8000 &
cd frontend && npm run dev

# 3. Build React
cd frontend && npm run build

# 4. Package desktop (all platforms via CI)
cd desktop && npm run tauri build
# Output:
#   macOS:   SemioVis.dmg
#   Windows: SemioVis_setup.exe
#   Linux:   SemioVis.AppImage  /  .deb
```

---

## 12. SaaS Deployment

### 12.1 Docker Compose (`docker-compose.yml`)

```yaml
version: "3.9"
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - APP_ENV=production
      - REDIS_URL=redis://redis:6379/0
    depends_on: [redis]
    volumes: [uploads:/tmp/semiovis_uploads]

  worker:
    build: .
    command: celery -A workers.celery_app worker --loglevel=info
    depends_on: [redis]

  redis:
    image: redis:7-alpine

  frontend:
    build: frontend/
    ports: ["3000:80"]    # nginx serves React build

volumes:
  uploads:
```

### 12.2 Deployment Targets

| Platform | Notes |
|---|---|
| **Fly.io** | `fly deploy` — simplest, free tier available |
| **Railway** | `railway up` — auto-detects Dockerfile |
| **Render** | connect GitHub — auto-deploy on push |
| **Kubernetes** | `kubectl apply -f infra/k8s/` — full scaling |

### 12.3 Nginx Config

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;           # React build

    location /api/ {
        proxy_pass http://api:8000/api/;  # FastAPI backend
    }

    location / {
        try_files $uri $uri/ /index.html; # SPA fallback
    }
}
```

---

## 13. Report Generation (`backend/core/report_generator.py`)

```python
async def generate_report(image_id, results, format):
    context = build_report_context(image_id, results)
    match format:
        case "pdf":   return render_pdf(context)    # reportlab
        case "docx":  return render_docx(context)   # python-docx
        case "html":  return render_html(context)   # Jinja2 template
```

**Report sections:**
1. Image metadata and thumbnail
2. Representational Analysis — annotated image, vector table, narrative/conceptual classification, interpretation
3. Interactive Analysis — face overlay, 8-axis modality radar chart, coding orientation note, perspective diagram, social distance (body-based)
4. Compositional Analysis — Centred/Polarized classification, semiotic grid, saliency heatmap, reading path diagram, framing breakdown (connection vs disconnection means), colour palette
5. Integrated Semiotic Interpretation (GPT-4o, ~300 words)
6. Summary table — all quantitative indicators (including modality profile, composition type, framing scores)
7. Reference diagrams — Fig. 4.23 (Interactive meanings), Fig. 6.15 (Visual space), Fig. 6.21 (Composition system) with the analysed image's position highlighted
8. Reference: Kress, G., & van Leeuwen, T. (2006). *Reading Images: The Grammar of Visual Design* (2nd ed.). Routledge.

---

## 14. Settings Panel

```typescript
interface AppSettings {
  // --- Detection backend ---
  detectionBackend:   'local' | 'google' | 'aws'   // default: 'local' (no API key)
  // --- LLM Interpretation backend ---
  interpretationLLM:  'auto' | 'openai' | 'gemini' | 'mistral' | 'local'  // default: 'auto' (cascade)
  // --- Analysis settings ---
  saliencyMethod:     'spectral' | 'itti'
  gridSize:           '2x2' | '3x3'
  language:           'en'                 // UI language: English only
  vectorMinLength:    number               // default: 50
  vectorThreshold:    number               // default: 100
  overlayOpacity:     number               // saliency heatmap opacity [0-1]
  codingOrientation:  'naturalistic' | 'sensory' | 'technological' | 'abstract'
  readingDirection:   'ltr' | 'rtl'        // reverses Given/New axis for RTL cultures
  // --- API Keys (all optional) ---
  apiKeys: {
    gemini:  string    // FREE: Google Gemini — 15 RPM, 1M tokens/day, vision support
    openai:  string    // Paid: GPT-4o — best quality
    mistral: string    // Free tier: Pixtral — vision support
    google_vision: string  // Google Cloud Vision — object/face detection
    aws_id:  string    // AWS Rekognition
    aws_key: string
  }
}
```

Settings are persisted in `localStorage` (frontend) and passed per-request to the backend.

---

## 15. Testing

### 15.1 Backend (`tests/backend/`)

```python
# test_saliency.py
def test_saliency_output_shape():
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    sal = cpp_core.compute_saliency_spectral(img)
    assert sal.shape == (100, 100)
    assert sal.min() >= 0.0 and sal.max() <= 1.0

def test_detect_vectors_returns_list():
    img_gray = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
    result = cpp_core.detect_vectors(img_gray)
    assert isinstance(result, list)
    if result:
        assert all(k in result[0] for k in ["x1","y1","x2","y2","angle","strength"])

# test_api_routes.py (FastAPI TestClient)
def test_upload_endpoint():
    with open("tests/fixtures/portrait.jpg", "rb") as f:
        response = client.post("/api/upload", files={"file": f})
    assert response.status_code == 200
    assert "image_id" in response.json()
```

### 15.2 Frontend (`tests/frontend/`)

Use **Vitest** + **React Testing Library**:

```typescript
test('renders 9 zones for 3x3 grid', () => {
  render(<SemioticGrid zones={mockZones(3, 3)} />)
  expect(screen.getAllByTestId('grid-zone')).toHaveLength(9)
})
```

### 15.3 Test Fixture Images (`tests/fixtures/`)

| File | Purpose |
|---|---|
| `portrait_demand.jpg` | Direct gaze → tests "Demand" classification |
| `advertisement.jpg` | Clear Given/New layout → tests compositional grid |
| `diagram.png` | Taxonomic structure → tests conceptual classification |
| `action_scene.jpg` | Diagonal vectors → tests transactional narrative |
| `abstract_art.png` | Low modality (naturalistic orientation) → tests 8-scale modality profile |
| `centred_composition.jpg` | Strong centre element → tests Centred vs Polarized classification |
| `triptych_layout.jpg` | Three-panel structure → tests Triptych detection |
| `technical_diagram.png` | Technological coding orientation → tests modality under non-naturalistic coding |
| `rtl_arabic_ad.jpg` | Arabic-language advertisement → tests RTL Given/New reversal |

---

## 16. Build Order

```
Step 1   Repo setup: folder structure, pyproject.toml, package.json, CMakeLists.txt
Step 2   C++ core: implement and unit-test all functions in backend/cpp/
Step 3   pybind11 bindings: bindings.cpp + CMake build + Python smoke tests
Step 4   FastAPI skeleton: main.py, routes, Pydantic models (mock responses)
Step 5   Image upload route + image_utils.py
Step 6   Compositional analysis (no external API dependency)
Step 7   Vision API wrapper: vision_api.py — Google Vision as primary backend
Step 8   Representational analysis
Step 9   Interactive analysis
Step 10  GPT-4o interpretation integration
Step 11  React frontend: layout, upload, all three analysis panels
Step 12  Report generation (PDF + DOCX)
Step 13  Tauri desktop bundling + PyInstaller packaging
Step 14  Docker Compose + SaaS deployment configuration
Step 15  Full test suite + README + OpenAPI docs review
```

---

## 17. Documentation

- All Python functions: **Google-style docstrings**
- All C++ functions: **Doxygen** comments
- FastAPI auto-generates **OpenAPI / Swagger UI** at `/docs`
- `README.md`: installation guide, screenshots, quick-start for both desktop and SaaS
- `docs/theory.md`: mapping of each implementation to Kress & van Leeuwen chapters

---

## 18. Theoretical Reference Map

| Analysis | Kress & van Leeuwen (2006) | Key concepts implemented |
|---|---|---|
| Representational | Ch. 2 (Narrative representations), Ch. 3 (Conceptual representations) | Vectors, Actor/Goal, transactional/non-transactional/bidirectional action, reactional, conversion, mental/verbal processes, classificational/analytical/symbolic structures |
| Interactive | Ch. 4 (Representation and interaction), Ch. 5 (Modality: designing models of reality) | Demand/Offer, social distance (body-based), power angle, involvement angle, 8-scale modality profile, coding orientations |
| Compositional | Ch. 6 (The meaning of composition) | Given/New, Ideal/Real, Centre/Margin, Triptych, Centred vs Polarized detection, salience, framing/connection, reading path |
| Materiality | Ch. 7 (Materiality and meaning) | Production technology classification (hand/recording/synthesizing), surface/medium analysis — NOT "colour grammar" (colour is distributed across Ch. 5 and Ch. 6) |

**IMPORTANT**: Ch. 7 is "Materiality and meaning" (surfaces, production technologies, media), NOT "The grammar of colour". Colour analysis is covered within Ch. 5 (modality markers: saturation, differentiation, modulation) and Ch. 6 (colour as compositional connector/disconnector). Always cite specific page numbers in code comments when a classification rule is derived from the book.

---

*CLAUDE.md — SemioVis v2.1*
*Stack: Python 3.11 + FastAPI + pybind11 + OpenCV + React 18 + Tauri v2*
*Deployment: Desktop (Mac / Win / Linux) + SaaS (Docker / Fly.io)*
*UI Language: English*