from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List, Optional
from fastapi import Body, Form, HTTPException
from fastapi.responses import JSONResponse
from app.models import (
    InterviewStartRequest, 
    InterviewAnswerRequest, 
    StartInterviewRequest, 
    NextQuestionRequest
)
from app.LLM.llm_service import generate_first_question, evaluate_and_continue, generate_interview_report, extract_text_from_pdf, summarize_resume
from app.LLM.llm_sst import transcribe_audio
from app.config.supabase import get_supabase
import uuid
from datetime import datetime
import re


load_dotenv()
app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
# console.log("FRONTEND_URL", FRONTEND_URL);
# console.log("allow_origins_list", allow_origins_list);
allow_origins_list = ["http://localhost:5173"]  # For local testing

if FRONTEND_URL != "http://localhost:5173":
    allow_origins_list.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# 🚀 Start Interview
@app.post("/interview/start")
def start_interview(data: InterviewStartRequest):

    question = generate_first_question(
        role=data.role,
        experience=data.experience
    )

    return {"question": question}


# 🔄 Continue Interview
@app.post("/interview/answer")
def answer_interview(data: InterviewAnswerRequest):

    # End condition - generate final summary after 10 questions
    if data.question_count >= 9:
        summary = generate_final_summary(
            role=data.role,
            experience=data.experience,
            history=[msg.dict() for msg in data.history]
        )
        return {"response": summary}

    result = evaluate_and_continue(
        role=data.role,
        jd="", # Assuming no JD for this old endpoint
        resume_summary="",
        history=[msg.dict() for msg in data.history]
    )

    return {"response": result}


# 📅 Create Interview Endpoint
@app.post("/create-interview")
async def create_interview(
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    role: str = Form(...),
    jd: str = Form(...),
    cutoff_score: float = Form(7.0),
    resume: UploadFile = File(...),
    hr_id: str = Form(None),
    hr_name: str = Form(None),
    hr_email: str = Form(None)
):
    try:
        supabase = get_supabase()
        
        # 1. Process Resume
        resume_bytes = await resume.read()
        resume_text = extract_text_from_pdf(resume_bytes)
        resume_summary = summarize_resume(resume_text)
        
        # 2. Upload Resume to Supabase Storage
        file_ext = resume.filename.split('.')[-1]
        file_path = f"resumes/{uuid.uuid4()}.{file_ext}"
        
        # Ensure bucket exists or just try to upload
        storage_res = supabase.storage.from_('resumes').upload(
            file_path, 
            resume_bytes,
            {"content-type": "application/pdf"}
        )
        
        # Get public URL
        resume_url_res = supabase.storage.from_('resumes').get_public_url(file_path)
        resume_file_url = resume_url_res["publicURL"] if isinstance(resume_url_res, dict) and "publicURL" in resume_url_res else resume_url_res
        
        # 3. Store Candidate
        candidate_data = {
            "name": candidate_name,
            "email": candidate_email,
            "resume_file_url": resume_file_url,
            "resume_text": resume_text,
            "resume_summary": resume_summary
        }
        
        candidate_res = supabase.table('candidates').insert(candidate_data).execute()
        
        if not candidate_res.data:
            raise Exception(f"Failed to insert candidate: {candidate_res}")
            
        candidate_id = candidate_res.data[0]['id']
        print(f"✅ Candidate created: {candidate_id}")
        
        # 4. Handle HR User (Upsert)
        if hr_id:
            hr_record = {"id": hr_id, "name": hr_name, "email": hr_email}
            # UPSERT: Insert or update HR info
            supabase.table('hr_users').upsert(hr_record).execute()
        else:
            # Fallback: find any HR user
            hr_res = supabase.table('hr_users').select('id').limit(1).execute()
            hr_id = hr_res.data[0]['id'] if hr_res.data else None
            
        if not hr_id:
            raise Exception("No HR user ID provided, and no existing HR users found.")

        session_data = {
            "hr_id": hr_id,
            "candidate_id": candidate_id,
            "role": role,
            "job_description": jd,
            "cutoff_score": cutoff_score,
            "status": "scheduled"
        }
        
        session_res = supabase.table('interview_sessions').insert(session_data).execute()
        if not session_res.data:
             raise Exception(f"Failed to create session: {session_res}")
             
        session_id = session_res.data[0]['id']
        print(f"✅ Session created: {session_id}")
        
        # 5. Generate Link
        interview_link = f"{FRONTEND_URL}/interview/{session_id}"
        
        # 6. Send Email (Placeholder logic)
        print(f"📧 Sending interview link to {candidate_email}: {interview_link}")
        
        return {
            "message": "Interview created successfully",
            "session_id": session_id,
            "interview_link": interview_link
        }
        
    except Exception as e:
        print(f"❌ Error creating interview: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# 🔍 Get Interview Session Data
@app.get("/interview/{session_id}")
async def get_interview_session(session_id: str):
    try:
        supabase = get_supabase()
        
        # 1. Fetch Session
        session_res = supabase.table('interview_sessions').select('*').eq('id', session_id).execute()
        if not session_res.data:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        session = session_res.data[0]
        
        # 2. Fetch Candidate
        candidate_res = supabase.table('candidates').select('*').eq('id', session['candidate_id']).execute()
        candidate = candidate_res.data[0] if candidate_res.data else {}
        
        return {
            "session": session,
            "candidate": {
                "name": candidate.get("name"),
                "resume_summary": candidate.get("resume_summary")
            },
            "role": session.get("role"),
            "jd": session.get("job_description")
        }
    except Exception as e:
        print(f"❌ Error fetching session: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 🎯 Start Interview (Session Based)
@app.post("/start-interview")
async def start_interview_session(data: StartInterviewRequest):
    try:
        supabase = get_supabase()
        
        # 1. Get session info
        session_res = supabase.table('interview_sessions').select('*').eq('id', data.session_id).execute()
        if not session_res.data:
             return JSONResponse(status_code=404, content={"error": "Session not found"})
        session = session_res.data[0]
        
        # 2. Get candidate context
        candidate_res = supabase.table('candidates').select('*').eq('id', session['candidate_id']).execute()
        candidate = candidate_res.data[0] if candidate_res.data else {}
        
        # 3. Generate first question with FULL context
        question = generate_first_question(
            role=session['role'],
            jd=session.get('job_description', ''),
            resume_summary=candidate.get('resume_summary', '')
        )
        
        # 4. Update status to 'in_progress'
        supabase.table('interview_sessions').update({"status": "in_progress", "started_at": datetime.now().isoformat()}).eq('id', data.session_id).execute()
        
        return {"question": question}
    except Exception as e:
        print(f"❌ Error starting interview: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 🔄 Next Question (Session Based)
@app.post("/next-question")
async def next_question_session(data: NextQuestionRequest):
    try:
        supabase = get_supabase()
        
        # 1. Store previous interaction
        supabase.table('interview_responses').insert({
            "session_id": data.session_id,
            "question": data.previous_question,
            "answer": data.answer
        }).execute()
        
        # 2. Fetch all past responses to build history
        responses_res = supabase.table('interview_responses').select('*').eq('session_id', data.session_id).order('created_at').execute()
        history = []
        for r in responses_res.data:
            history.append({"role": "assistant", "content": r["question"]})
            history.append({"role": "user", "content": r["answer"]})
        
        # 3. Get session and candidate info
        session_res = supabase.table('interview_sessions').select('*').eq('id', data.session_id).execute()
        if not session_res.data:
             return JSONResponse(status_code=404, content={"error": "Session not found"})
        session = session_res.data[0]
        
        candidate_res = supabase.table('candidates').select('*').eq('id', session['candidate_id']).execute()
        candidate = candidate_res.data[0] if candidate_res.data else {}

        # 4. Handle completion check (Example: end after 10 questions)
        if len(responses_res.data) >= 2:
            print(f"🏁 Interview completed for session {data.session_id}. Generating report...")
            
            # Generate Report
            report_text = generate_interview_report(
                role=session['role'],
                jd=session.get('job_description', ''),
                resume_summary=candidate.get('resume_summary', ''),
                history=history
            )
            print(f"📄 Full AI Report Generated:\n{report_text}\n{'='*30}")
            
            # Simple Parsing
            report_data = {
                "session_id": data.session_id,
                "summary": "",
                "overall_score": 0.0,
                "strengths": "",
                "weaknesses": "",
                "recommendation": ""
            }
            
            import json
            try:
                # Clean JSON string (remove markdown blocks if present)
                clean_json = report_text.strip()
                if clean_json.startswith("```"):
                    # Extract content between triple backticks
                    lines = clean_json.split("\n")
                    if lines[0].startswith("```"): lines = lines[1:]
                    if lines[-1].startswith("```"): lines = lines[:-1]
                    clean_json = "\n".join(lines).strip()
                
                # Parse JSON
                parsed_report = json.loads(clean_json)
                
                # Update report_data with parsed values
                report_data["overall_score"] = float(parsed_report.get("overall_score", 0.0))
                report_data["strengths"] = str(parsed_report.get("strengths", ""))
                report_data["weaknesses"] = str(parsed_report.get("weaknesses", ""))
                report_data["recommendation"] = str(parsed_report.get("recommendation", ""))
                report_data["summary"] = str(parsed_report.get("summary", ""))

            except Exception as parse_err:
                print(f"⚠️ Error parsing JSON report: {parse_err}")
                report_data["summary"] = report_text # Fallback

            # Store Report
            supabase.table('interview_reports').insert(report_data).execute()
            print(f"✅ Report stored for session {data.session_id}")

            # Update Session Status
            supabase.table('interview_sessions').update({
                "status": "completed", 
                "ended_at": datetime.now().isoformat()
            }).eq('id', data.session_id).execute()
            
            return {
                "type": "completed",
                "session_id": data.session_id
            }

        # 5. Generate next question/evaluate with FULL context
        result = evaluate_and_continue(
            role=session['role'],
            jd=session.get('job_description', ''),
            resume_summary=candidate.get('resume_summary', ''),
            history=history
        )
        
        return {
            "type": "question",
            "question": result
        }
        
    except Exception as e:
        print(f"❌ Error in next question: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 📄 Get Interview Report
@app.get("/interview-report/{session_id}")
async def get_interview_report(session_id: str):
    try:
        supabase = get_supabase()
        res = supabase.table('interview_reports').select('*').eq('session_id', session_id).single().execute()
        if not res.data:
            return JSONResponse(status_code=404, content={"error": "Report not found"})
        return res.data
    except Exception as e:
        print(f"❌ Error fetching report: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# 📋 Get All Interviews (History)
@app.get("/interviews")
async def get_all_interviews(hr_id: Optional[str] = None):
    try:
        supabase = get_supabase()
        # Explicitly select the child table columns. Supabase returns these as a list in the JSON.
        query = supabase.table('interview_sessions').select('*, candidates(name, email), interview_reports(overall_score)')
        
        if hr_id:
            query = query.eq('hr_id', hr_id)
            
        res = query.order('created_at', desc=True).execute()
        return res.data
    except Exception as e:
        print(f"❌ Error fetching interviews: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
