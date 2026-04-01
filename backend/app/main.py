from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
from app.LLM.llm_service import generate_first_question
from app.LLM.llm_sst import transcribe_audio
from app.routes.interviewRoutes import router as interview_router
from app.models import InterviewStartRequest

load_dotenv()
app = FastAPI()

FRONTEND_URLS = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
allow_origins_list = ["http://localhost:5173"]

for url in FRONTEND_URLS:
    clean_url = url.strip()
    if clean_url and clean_url not in allow_origins_list:
        allow_origins_list.append(clean_url)

# Print for debugging in Render logs
print(f"🌍 Allowed Origins: {allow_origins_list}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(interview_router)

@app.get("/")
def root():
    return {"message": "EDITH Backend Running 🚀"}

# 🎤 STT Endpoint
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    file_bytes = await file.read()
    text = transcribe_audio(
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
    )
    return {"text": text}

# 🚀 Basic Start Interview (Legacy, used for simple tests)
@app.post("/interview/start")
def start_interview(data: InterviewStartRequest):
    question = generate_first_question(
        role=data.role,
        experience=data.experience
    )
    return {"question": question}

