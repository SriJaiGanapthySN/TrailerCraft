from firebase_admin import firestore
from google.cloud.firestore import FieldFilter
from config.firebase_init import db
from langchain_community.chat_message_histories import ChatMessageHistory


def save_generation(uid: str, session_id: str, prompt: str, response: dict):
    db.collection("generations").add({
        "uid": uid,
        "session_id": session_id,
        "prompt": prompt,
        "response": response,
        "createdAt": firestore.SERVER_TIMESTAMP
    })


def get_session_history(uid: str, session_id: str):
    docs = (
        db.collection("generations")
        .where(filter=FieldFilter("uid", "==", uid))
        .where(filter=FieldFilter("session_id", "==", session_id))
        .order_by("createdAt")
        .stream()
    )

    return [doc.to_dict() for doc in docs]


def load_chat_history_for_session(uid: str, session_id: str) -> ChatMessageHistory:
    history = ChatMessageHistory()
    past_generations = get_session_history(uid, session_id)

    for gen in past_generations:
        history.add_user_message(gen.get("prompt", ""))
        response = gen.get("response", {})
        if isinstance(response, dict):
            title = response.get("title", "")
            structure = response.get("structure", "")
            history.add_ai_message(
                f"Generated trailer: {title}. Structure: {structure}"
            )
        else:
            history.add_ai_message(str(response))

    return history
