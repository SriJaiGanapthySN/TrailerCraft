import uuid
from firebase_admin import firestore
from config.firebase_init import db

def create_session(uid: str) -> str:
    session_id = str(uuid.uuid4())

    db.collection("sessions").document(session_id).set({
        "uid": uid,
        "createdAt": firestore.SERVER_TIMESTAMP
    })

    return session_id


def validate_session(uid: str, session_id: str):
    ref = db.collection("sessions").document(session_id)
    doc = ref.get()

    if not doc.exists:
        raise ValueError("Session not found")

    if doc.to_dict()["uid"] != uid:
        raise PermissionError("Unauthorized session")
