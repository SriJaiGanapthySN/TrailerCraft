from models.request import TrailerRequest
from fastapi import APIRouter
from main import generate_trailer_package
router = APIRouter()

@router.post("/generate")
def generate_trailer(request: TrailerRequest):
    trailer_package = generate_trailer_package(request.user_input)
    return trailer_package
