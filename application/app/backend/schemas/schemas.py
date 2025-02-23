from pydantic import BaseModel
from typing import List

class BackendError(BaseModel):
    code: str
    msg: str
    status: str

class Conversation(BaseModel):
    question: str
    answer: str

class ImageConversation(BaseModel):
    question: str
    question_translated: str
    answer_urls: list = []

class Question(BaseModel):
    question: str
    history: List[Conversation] = []
    session_id: str
    oid_hashed: str
    apply_pseudonymization: bool = True

class ImageQuestion(BaseModel):
    question: str
    history: List[ImageConversation] = []
    session_id: str
    oid_hashed: str

class DocQuestion(BaseModel):
    doc_context:str
    doc_question:str
    session_id:str
    oid_hashed:str
    history: List[Conversation] = []
    llm_model_name:str = "gemini-1.0-pro-001"

class ProvidedDocQuestion(BaseModel):
    doc_question:str
    session_id:str
    oid_hashed:str
    doc_key:str
    history: List[Conversation] = []
    llm_model_name:str = "gemini-1.0-pro-001"
    doc_key:str

class Answer(BaseModel):
    question: str
    answer: str
    history: List[Conversation]
    errors: List[BackendError]
    info: str = ""

class GroundContent(BaseModel):
    page: int
    content: str

class Citation(BaseModel):
    id: int
    name: str
    link: str
    path: str
    content: List[GroundContent]


class AnswerWithQuotes(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    history: List[Conversation]
    errors: List[BackendError]
    info: str = ""

class HealthCheck(BaseModel):
    status: str = "OK"

class UnhealthyCheck(BaseModel):
    status: str = "Really not okay!"

class ImageAnswer(BaseModel):
    original_prompt: str
    en_prompt: str
    images: List
    history: List[ImageConversation]
    errors: List[BackendError]

class FileBytes(BaseModel):
    bytes_data: str

class ExcelProcessed(BaseModel):
    table_data: str
