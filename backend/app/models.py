from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class Message(BaseModel):
    role: str
    content: str


class InterviewStartRequest(BaseModel):
    role: str
    experience: int
    

class InterviewAnswerRequest(BaseModel):
    role: str
    experience: int
    history: List[Message]
    question_count: int


class CreateInterviewRequest(BaseModel):
    candidate_email: EmailStr
    candidate_name: str
    role: str
    jd: str
    cutoff_score: float = 7.0


class StartInterviewRequest(BaseModel):
    session_id: str


class NextQuestionRequest(BaseModel):
    session_id: str
    answer: str