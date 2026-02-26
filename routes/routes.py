from google.cloud.firestore import FieldFilter
from config.firebase_init import db
from models.request import Request
from fastapi import APIRouter, Depends, HTTPException
from config.auth import get_current_user
from services.session_service import create_session, validate_session
from services.history_service import save_generation, load_chat_history_for_session, get_session_history
router = APIRouter()

@router.post("/generate")
def generate_trailer(request: Request,user=Depends(get_current_user)):
    uid = user["uid"]
    try:
        validate_session(uid, request.session_id)
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

    chat_history = load_chat_history_for_session(uid, request.session_id)

    from main import generate_trailer_package
    result = generate_trailer_package(request.prompt, chat_history)

    if isinstance(result, str):
        response_data = {"mode": "specific", "message": result}
    else:
        response_data = {"mode": "full", **result.model_dump()}

    save_generation(
        uid=uid,
        session_id=request.session_id,
        prompt=request.prompt,
        response=response_data
    )
    return response_data


@router.post("/sessions")
def create_new_session(user=Depends(get_current_user)):
    session_id = create_session(user["uid"])
    return {"session_id": session_id}

@router.get("/sessions")
def list_sessions(user=Depends(get_current_user)):
    docs = (
        db.collection("sessions")
        .where(filter=FieldFilter("uid", "==", user["uid"]))
        .order_by("createdAt", direction="DESCENDING")
        .stream()
    )

    return [
        {"session_id": doc.id, **doc.to_dict()}
        for doc in docs
    ]

@router.get("/sessions/{session_id}/history")
def get_history(session_id: str, user=Depends(get_current_user)):
    uid = user["uid"]
    try:
        validate_session(uid, session_id)
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

    history = get_session_history(uid, session_id)
    return {"session_id": session_id, "history": history}

