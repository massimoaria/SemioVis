"""POST /api/analyse/full — Full analysis combining all three dimensions."""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from api.routes.representational import analyse_representational, RepresentationalRequest
from api.routes.interactive import analyse_interactive, InteractiveRequest
from api.routes.compositional import analyse_compositional, CompositionalRequest

router = APIRouter()


class FullAnalysisRequest(BaseModel):
    image_id: str
    api_backend: str = "local"
    coding_orientation: str = "naturalistic"
    saliency_method: str = "spectral"
    grid_size: str = "3x3"
    reading_direction: str = "ltr"


@router.post("/full")
async def analyse_full(req: FullAnalysisRequest, request: Request):
    """Run all three analyses and return combined results."""
    rep_req = RepresentationalRequest(image_id=req.image_id, api_backend=req.api_backend)
    int_req = InteractiveRequest(
        image_id=req.image_id,
        api_backend=req.api_backend,
        coding_orientation=req.coding_orientation,
    )
    comp_req = CompositionalRequest(
        image_id=req.image_id,
        saliency_method=req.saliency_method,
        grid_size=req.grid_size,
        reading_direction=req.reading_direction,
    )

    representational = await analyse_representational(rep_req, request)
    interactive = await analyse_interactive(int_req, request)
    compositional = await analyse_compositional(comp_req, request)

    return {
        "representational": representational.model_dump(),
        "interactive": interactive.model_dump(),
        "compositional": compositional.model_dump(),
    }
