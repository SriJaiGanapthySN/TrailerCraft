from firebase_admin import firestore
from config.firebase_init import db
from langchain_classic.memory import ChatMessageHistory


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
        .where("uid", "==", uid)
        .where("session_id", "==", session_id)
        .order_by("createdAt")
        .stream()
    )

    return [doc.to_dict() for doc in docs]


def load_chat_history_for_session(uid: str, session_id: str) -> ChatMessageHistory:
    """
    Load past generations from Firestore and reconstruct a
    LangChain ChatMessageHistory so the LLM can continue the conversation.
    """
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
