import dotenv
import os
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory

dotenv.load_dotenv()

from pydantic import BaseModel,Field
from typing import List

class DirectorConsultation(BaseModel):
    style_tip: str = Field(description="A tip on how to adapt the director's signature filmmaking style.")
    trademark_interval: str = Field(description="A description of a signature interval block typical for this director's style.")

class Shot(BaseModel):
    shotnumber:int
    visual:str=Field(description="A brief description of the visual content of the shot.")
    cameraangle:str=Field(description="The camera angle used in the shot, e.g., close-up, wide shot, aerial view.")
    audio_cue:str=Field(description="Any significant audio cues present in the shot, such as dialogue, sound effects, or music.")

class TrailerPackage(BaseModel):
    structure: str = Field(description="The 3-act breakdown of the trailer")
    voice_over: str = Field(description="The script for the narrator it should be in tamil and that tamil is not pure it should be a tamil in a way that it is used in common")
    music_mood: str = Field(description="Instrumentation, tempo, and vibe")
    fonrstyle: str = Field(description="The font style to be used in the trailer")
    title: str = Field(description="The title of the movie in tamil and english that is good make it catchy and appealing")
    shot_list: List[Shot]
    director_consultation: DirectorConsultation



prompt =ChatPromptTemplate.from_messages([
    ("system",    """You are a Kollywood Trailer Editor who is an expert in creating engaging and captivating trailers for Tamil movies.
    Your task is to analyze the provided movie plot and generate a detailed trailer structure that includes a 3-act breakdown, voice-over script, music mood, and a shot list with descriptions of visuals, camera angles, and audio cues using the synopsis of the movie also use the conservation hsitory as well"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", """
    CONTEEXT FROM DATABASE: {context}
    MOVIE SYNOPSIS: {synopsis}
    ADDITIONAL STYLE GUIDELINES: {instructions}
    """)
])

# LLM Integration with Groq and Gemini

model=ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key=os.getenv("GEMINI_API_KEY"),temperature=0.7)

def _detect_specific_mode(user_input: str) -> str | None:
    """Keyword-based fallback: return 'specific' if user clearly wants one thing only."""
    lower = user_input.lower().strip()
    specific_phrases = [
        "give me a title", "just a title", "only a title", "only title",
        "just give title", "just give a title", "give title", "give a title",
        "title for", "suggest a title", "suggest title", "movie title",
        "give me a bgm", "just the bgm", "only bgm", "music mood",
        "just a font", "only font", "font style",
        "just the cast", "only cast", "cast idea",
    ]
    for phrase in specific_phrases:
        if phrase in lower:
            return "specific"
    if re.search(r"\b(title|bgm|font|cast)\s+(only|please|pls)\b", lower):
        return "specific"
    # Broader: "title" + narrowing word (just/give/only) = specific
    if "title" in lower and re.search(r"\b(just|give|only|suggest)\b", lower):
        return "specific"
    return None


def segregate_intent(user_input, history):
    # Fast path: keyword-based detection for clearly specific requests
    detected = _detect_specific_mode(user_input)
   
    if detected == "specific":
        style_match = re.search(r"(\w+)\s+style", user_input, re.I)
        return {
            "synopsis": user_input,
            "mode": "specific",
            "target": "title" if "title" in user_input.lower() else "bgm" if "bgm" in user_input.lower() or "music" in user_input.lower() else "other",
            "style": style_match.group(1) if style_match else "",
            "instructions": "",
        }

    parser_prompt = f"""
    Analyze this user request: "{user_input}"

    CRITICAL: mode must be "specific" when the user asks for ONLY one small thing:
    - "Give me a title" / "just a title" / "title for X" -> mode: "specific", target: "title"
    - "Just the BGM" / "music mood" -> mode: "specific", target: "bgm"
    - "Font style only" -> mode: "specific", target: "font"
    mode must be "full" ONLY when they want a complete trailer, script, or full breakdown.

    Return ONLY valid JSON (no markdown):
    {{"synopsis": "extracted plot or context", "mode": "specific" or "full", "target": "title" or "bgm" or "script" or "font", "style": "extracted style", "instructions": "any other notes"}}
    """
    raw_response = model.invoke(parser_prompt).content
    clean_json = re.sub(r"```json|```", "", raw_response).strip()
    return json.loads(clean_json)

def generate_trailer_package(user_input: str, chat_history: ChatMessageHistory = None) -> TrailerPackage:
    if chat_history is None:
        chat_history = ChatMessageHistory()
    parsed = segregate_intent(user_input, chat_history.messages)
    print(f"[DEBUG] prompt={repr(user_input)} mode={parsed.get('mode')} target={parsed.get('target')}")
    search_query = parsed.get('synopsis') or user_input
    if parsed['mode'] == 'specific':
        target = parsed.get('target', 'other')
        if target == 'title':
            specific_prompt = f"""Context: {search_query}
            User request: {user_input}
            Provide ONLY a catchy movie title. No explanation, no structure, no other content.
            If Kollywood/Tamil: give title in Tamil and English. Style: {parsed.get('style', 'general')}.
            Output: just the title(s), nothing else."""
        elif target == 'bgm':
            specific_prompt = f"""Context: {search_query} User request: {user_input}
            Provide ONLY the music mood/BGM description. No explanation, no other content. Be brief."""
        else:
            specific_prompt = f"Context: {search_query}\nHistory: {chat_history.messages}\nUser: {user_input}\nAnswer ONLY the specific request briefly."
        response = model.invoke(specific_prompt).content
        print(response)
        chat_history.add_user_message(user_input)
        chat_history.add_ai_message(response)
        return response
    else:
        structeredllm = model.with_structured_output(TrailerPackage)
        chain = prompt | structeredllm
        response = chain.invoke({
            "chat_history": chat_history.messages,
            "synopsis": parsed['synopsis'],
            "instructions": f"Style: {parsed.get('style', 'General')}. Extra: {parsed.get('instructions', 'None')}"
        })
        
        _print_formatted_output(response)
        
        chat_history.add_user_message(user_input)
        chat_history.add_ai_message(f"Generated trailer: {response.title}")
                
        return response

def _print_formatted_output(response):
    data = response.model_dump()
    for key, value in data.items():
        if key == "director_consultation": continue
        print(f"\n{key.replace('_', ' ').upper()}")
        if isinstance(value, list):
            i=1
            for item in value:
                print(f"Shot {item.get('shot_number', i)}:\n{item.get('visual')}")
                print(f"Camera Angle: {item.get('cameraangle')}")
                print(f"Audio Cue: {item.get('audio_cue')}")
                i+=1
        else:
            print(value)
    
    print("\nDIRECTOR CONSULTATION")
    print(f"Tip: {response.director_consultation.style_tip}")
    print(f"Interval: {response.director_consultation.trademark_interval}")