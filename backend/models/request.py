from pydantic import BaseModel

class Request(BaseModel):
    session_id:str
    prompt:str