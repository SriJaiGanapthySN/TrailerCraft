import dotenv
import os
import pandas as pd
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory

dotenv.load_dotenv()


data = pd.read_csv("dataset/Tamil_movies_dataset.csv")
df = pd.read_csv("dataset/tamil.csv") 

def generate_unified_profile(row):
    name = row.get('MovieName') or row.get('Title')
    genre = row.get('Genre')
    director = row.get('Director')
    actor = row.get('Actor') or row.get('Cast')
    year = row.get('Year') or row.get('Release Year')
    rating = row.get('Rating')
    plot = row.get('Plot', 'No plot available')

    return (
        f"Title: {name}\n"
        f"Genre: {genre}\n"
        f"Director: {director}\n"
        f"Actor: {actor}\n"
        f"Release Year: {year}\n"
        f"Rating: {rating}\n"
        f"Synopsis: {plot}\n"
    )

data["profile"] = data.apply(generate_unified_profile, axis=1)
docs_1 = [
    Document(
        page_content=row["profile"],
        metadata={
            "source": "Tamil_movies_dataset",
            "title": row.get('MovieName'),
            "genre": row.get('Genre'),
            "year": row.get('Year')
        }
    ) for _, row in data.iterrows()
]

df["profile"] = df.apply(generate_unified_profile, axis=1)
docs_2 = [
    Document(
        page_content=row["profile"],
        metadata={
            "source": "Tamil_dataset_2",
            "title": row.get('Title'),
            "genre": row.get('Genre'),
            "year": row.get('Release Year')
        }
    ) for _, row in df.iterrows()
]

documents = docs_1 + docs_2

print(f"Total documents prepared for TrailerCraft: {len(documents)}")



embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore=Chroma.from_documents(documents,embeddings,persist_directory="dataset/Tamil_movies_dataset_chroma")


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


retrivar = vectorstore.as_retriever(search_kwargs={"k": 10})

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

def segregate_intent(user_input, history):
    parser_prompt = f"""
    Analyze this user request: "{user_input}"
    
    Rules:
    - If the user asks for a specific tiny detail (just a title, just BGM, just a cast idea) without wanting a full script, set mode: "specific".
    - If the user asks for a trailer, a script, or a full story breakdown, set mode: "full".
    
    Return ONLY JSON: 
    {{
        "synopsis": "extracted plot", 
        "mode": "full" or "specific", 
        "target": "title" or "bgm" or "script",
        "style": "extracted style",
        "instructions": "any other notes"
    }}
    """
    raw_response = model.invoke(parser_prompt).content
    clean_json = re.sub(r"```json|```", "", raw_response).strip()
    return json.loads(clean_json)

def generate_trailer_package(user_input: str, chat_history: ChatMessageHistory = None) -> TrailerPackage:
    if chat_history is None:
        chat_history = ChatMessageHistory()
    parsed = segregate_intent(user_input, chat_history.messages)
    search_query = parsed.get('synopsis') or user_input
    relevant_docs = retrivar.invoke(search_query)
    context_data = "\n\n".join([doc.page_content for doc in relevant_docs])
    if parsed['mode'] == 'specific':
        specific_prompt = f"Context: {context_data}\nHistory: {chat_history.messages}\nUser: {user_input}\nAnswer ONLY the specific request briefly."
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
            "context": context_data,
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