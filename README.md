# SemioVis

**Visual Social Semiotics Analysis Tool**

SemioVis is a cross-platform application that performs automated semiotic analysis of images based on the analytical framework from:

> Kress, G., & van Leeuwen, T. (2006). *Reading Images: The Grammar of Visual Design* (2nd ed.). Routledge.

It extracts visual features using computer vision and machine learning, then interprets them through the three fundamental dimensions of visual grammar: **Representational**, **Interactive**, and **Compositional** meaning.

---

## Who is SemioVis for?

- **Researchers** in visual communication, media studies, multimodal discourse analysis, and social semiotics who need reproducible, data-driven image analysis
- **Students and educators** in communication, journalism, cultural studies, and linguistics who want to learn and teach Kress & van Leeuwen's framework with hands-on tools
- **Media analysts and content strategists** who evaluate how images construct meaning in advertising, news, branding, and public communication
- **Digital humanities scholars** working with large visual corpora who need scalable, consistent analytical workflows

---

## Analytical Framework

SemioVis implements the three metafunctions of visual grammar as described in *Reading Images* (2006):

### Representational Analysis (Ch. 2--3)

Identifies **what is being depicted** and the relationships between visual participants.

| Feature | Description | Reference |
|---|---|---|
| Narrative vs Conceptual | Classifies whether the image tells a story (vectors, action) or presents concepts (taxonomy, symbolism) | Ch. 2--3 |
| Narrative subtypes | Transactional, non-transactional, bidirectional, reactional, mental, verbal, conversion | pp. 66--75 |
| Conceptual subtypes | Classificational, analytical, symbolic | pp. 79--105 |
| Vector detection | Hough line detection to identify action vectors connecting participants | p. 74 |
| Participant identification | Object and person detection with role assignment (Actor, Goal, Reacter, Phenomenon) | pp. 74--75 |

### Interactive Analysis (Ch. 4--5)

Analyses **the relationship between the image and its viewer**.

| Feature | Description | Reference |
|---|---|---|
| Contact (Demand/Offer) | Gaze direction of represented participants: direct gaze = Demand, averted = Offer | p. 117 |
| Social distance | Body-based framing mapped to Hall's proxemics: intimate, personal, social, public | pp. 124--128 |
| Attitude (Involvement) | Horizontal angle: frontal = involvement, oblique = detachment | p. 136 |
| Power (Vertical angle) | High angle = viewer power, eye level = equality, low angle = subject power | p. 140 |
| Modality profile | 8 independent scales: colour saturation, colour differentiation, colour modulation, contextualization, representation detail, depth, illumination, brightness | pp. 160--163 |
| Coding orientation | Interpretation of modality relative to naturalistic, sensory, technological, or abstract standards | pp. 165--166 |
| Emotion recognition | 7 basic emotions per detected face (neutral, happiness, surprise, sadness, anger, disgust, fear, contempt) | -- |

### Compositional Analysis (Ch. 6)

Examines **how visual elements are arranged** to create coherent meaning.

| Feature | Description | Reference |
|---|---|---|
| Information value | Given/New (left--right), Ideal/Real (top--bottom), Centre/Margin zones | pp. 179--197 |
| Composition type | Centred (circular, triptych, centre-margin) vs Polarized (given-new, ideal-real axes) | pp. 194--210 |
| Salience | Saliency map computation (spectral residual or Itti-Koch) with per-zone visual weight | p. 202 |
| Framing | Connection vs disconnection analysis: frame lines, empty space, colour discontinuities, visual rhymes | pp. 203--204 |
| Reading path | Predicted visual scanning order based on salience peaks (linear, circular, Z-pattern, spiral) | pp. 204--208 |
| Colour palette | Dominant colours via k-means clustering with zone associations and temperature classification | Ch. 5--6 |
| RTL support | Given/New axis reversal for right-to-left reading cultures (Arabic, Hebrew) | p. 181 |

---

## Features

### Offline-first architecture
All core analysis runs locally with no internet connection and no API keys required. The app ships with lightweight ML models (~55 MB total) that are downloaded automatically on first run:

| Model | Size | Purpose |
|---|---|---|
| YOLOv8n | ~6 MB | Object detection (80 COCO classes) |
| YOLOv8n-pose | ~7 MB | Body keypoints for social distance |
| MediaPipe Face Mesh | ~2 MB | 468 facial landmarks, gaze estimation |
| FER+ (ONNX) | ~34 MB | Facial emotion recognition |
| MiDaS v2.1 small | ~5 MB | Monocular depth estimation |

### Optional LLM interpretation
When API keys are provided, SemioVis generates rich academic prose contextualising the extracted features. The interpretation cascade tries each backend in order until one succeeds:

1. **OpenAI GPT-4o** -- best quality (paid)
2. **Google Gemini 2.0 Flash** -- excellent quality, free tier (15 RPM, 1M tokens/day)
3. **Mistral Pixtral** -- good quality, free tier available
4. **Rule-based local** -- always available, deterministic, academically correct

### Interactive visualisations
- **Vector overlay** -- detected action vectors colour-coded by direction (horizontal, vertical, diagonal)
- **Gaze overlay** -- face bounding boxes with Demand (red) / Offer (grey) classification
- **8-axis modality radar** -- Plotly.js radar chart showing the full modality profile, not a single score
- **Semiotic grid** -- colour-coded spatial zones with information value labels (Given, New, Ideal, Real, Centre, Margin)
- **Saliency heatmap** -- toggleable semi-transparent overlay with blue-to-red colour scale
- **Reading path** -- animated polyline connecting salience waypoints in predicted scanning order
- **Colour palette** -- extracted dominant colours with proportions and zone associations

### Report generation
Export complete analysis as **PDF** or **DOCX** including annotated images, charts, quantitative tables, semiotic interpretation, and bibliographic reference.

### Cross-platform deployment
- **Desktop** (macOS, Windows, Linux) -- native app via Tauri v2, bundles the backend as a sidecar process
- **SaaS / Web** -- Docker Compose deployment with Celery + Redis for async task processing

---

## Installation

### Desktop app

Download the latest release for your platform from the [Releases](../../releases) page:

| Platform | Format |
|---|---|
| macOS (Apple Silicon) | `.dmg` |
| macOS (Intel) | `.dmg` |
| Linux | `.AppImage`, `.deb` |
| Windows | `.msi`, `.exe` |

**macOS: first launch setup**

Since SemioVis is not signed with an Apple Developer certificate, macOS will block it by default. After copying SemioVis.app to your Applications folder:

**Option A** -- Double-click the `Install SemioVis.command` script included in the DMG. It removes the quarantine flag automatically.

**Option B** -- Run this command in Terminal:
```bash
xattr -cr /Applications/SemioVis.app
```

**Option C** -- Right-click SemioVis.app, select "Open", then click "Open" again in the dialog. macOS will remember your choice for future launches.

### Development setup

**Prerequisites:** Python 3.11+, Node.js 20+, Rust (for Tauri), CMake, OpenCV, Eigen3

```bash
# Clone
git clone https://github.com/massimoaria/SemioVis.git
cd SemioVis

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python models/download_models.py          # download ML models (~55 MB)
uvicorn main:app --reload --port 8000 &

# Frontend
cd ../frontend
npm install
npm run dev                               # opens at http://localhost:5173

# (Optional) Build C++ core for faster analysis
cd ../backend/cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc || sysctl -n hw.ncpu)
```

### Docker (SaaS)

```bash
docker-compose up --build
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

---

## Configuration

All API keys are **optional**. Copy `.env.example` to `.env` and fill in only what you need:

```bash
# LLM interpretation (pick one or none for rule-based output)
GEMINI_API_KEY=...       # FREE: Google AI Studio
OPENAI_API_KEY=...       # Paid: OpenAI
MISTRAL_API_KEY=...      # Free tier: Mistral

# Vision detection (default is local YOLO + MediaPipe)
GOOGLE_VISION_KEY=...    # Google Cloud Vision
AWS_ACCESS_KEY_ID=...    # AWS Rekognition
AWS_SECRET_ACCESS_KEY=...
```

Settings can also be configured from the in-app Settings panel, which persists API keys and analysis preferences (saliency method, grid size, coding orientation, reading direction) in the browser.

---

## API

The FastAPI backend auto-generates interactive documentation at `/docs` (Swagger UI) and `/redoc`.

Key endpoints:

```
POST /api/upload                      Upload an image
POST /api/analyse/representational    Narrative/conceptual structure
POST /api/analyse/interactive         Contact, distance, attitude, modality
POST /api/analyse/compositional       Information value, salience, framing
POST /api/analyse/full                All three analyses combined
POST /api/report                      Generate PDF/DOCX report
```

---

## Technology stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, shadcn/ui, Zustand, Plotly.js, Konva.js |
| **Backend** | Python 3.11, FastAPI, Pydantic v2, OpenCV, NumPy, Pillow |
| **ML models** | YOLOv8 (Ultralytics), MediaPipe, ONNX Runtime, MiDaS |
| **C++ core** | C++17, OpenCV, Eigen3, pybind11, OpenMP |
| **Desktop** | Tauri v2 (Rust), PyInstaller |
| **Infrastructure** | Docker, Nginx, Redis, Celery |

---

## Reference

This application implements the analytical framework from:

Kress, G., & van Leeuwen, T. (2006). *Reading Images: The Grammar of Visual Design* (2nd ed.). Routledge.

All classification rules, thresholds, and terminology in the codebase are annotated with specific page references to this text.

---

## License

MIT
