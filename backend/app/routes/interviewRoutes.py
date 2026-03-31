from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
from datetime import datetime
from app.models import InterviewAnswerRequest, StartInterviewRequest, NextQuestionRequest
from app.LLM.llm_service import generate_first_question, evaluate_and_continue, generate_interview_report, extract_text_from_pdf, summarize_resume
from app.config.supabase import get_supabase
import os
import resend

router = APIRouter()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

def send_interview_email(to_email: str, candidate_name: str, role: str, interview_link: str):
    if not RESEND_API_KEY:
        print("⚠️ Resend API Key is missing, skipping email.")
        return
    
    html_content = f"""
    <div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 15px; border-top: 5px solid #2563eb;'>
        <h1 style='color: #2563eb; font-size: 24px; font-weight: 800;'>EDITH AI</h1>
        <p>Dear {candidate_name},</p>
        <p>You have been invited for an interview for the <strong>{role}</strong> position.</p>
        <div style='text-align: center; margin: 30px 0;'>
            <a href='{interview_link}' style='background-color: #000; color: #fff; padding: 15px 30px; text-decoration: none; border-radius: 10px; font-weight: bold;'>Start Interview Now</a>
        </div>
        <p style='color: #666; font-size: 13px;'>This interview is powered by EDITH AI. Please ensure you have a working microphone and a stable internet connection before starting.</p>
        <hr style='border: none; border-top: 1px solid #eee; margin: 20px 0;'>
        <p style='color: #aaa; font-size: 11px;'>If you're having trouble with the button, copy and paste this link into your browser: <br> {interview_link}</p>
    </div>
    """

    try:
        params = {
            "from": "EDITH AI <onboarding@resend.dev>",
            "to": to_email,
            "subject": f"Interview Invitation: {role}",
            "html": html_content,
        }
        res = resend.Emails.send(params)
        print(f"📧 Email sent successfully via Resend: {res}")
    except Exception as e:
        print(f"❌ Failed to send email via Resend: {str(e)}")

# 🔄 Continue Interview
@router.post("/interview/answer")
def answer_interview(data: InterviewAnswerRequest):
    result = evaluate_and_continue(
        role=data.role,
        jd="", 
        resume_summary="",
        history=[msg.dict() for msg in data.history]
    )
    return {"response": result}


# 📅 Create Interview Endpoint
@router.post("/create-interview")
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
        resume_bytes = await resume.read()
        resume_text = extract_text_from_pdf(resume_bytes)
        resume_summary = summarize_resume(resume_text)
        
        file_ext = resume.filename.split('.')[-1]
        file_path = f"resumes/{uuid.uuid4()}.{file_ext}"
        
        supabase.storage.from_('resumes').upload(
            file_path, 
            resume_bytes,
            {"content-type": "application/pdf"}
        )
        
        resume_url_res = supabase.storage.from_('resumes').get_public_url(file_path)
        resume_file_url = resume_url_res["publicURL"] if isinstance(resume_url_res, dict) and "publicURL" in resume_url_res else resume_url_res
        
        candidate_data = {
            "name": candidate_name,
            "email": candidate_email,
            "resume_file_url": resume_file_url,
            "resume_text": resume_text,
            "resume_summary": resume_summary
        }
        
        candidate_res = supabase.table('candidates').insert(candidate_data).execute()
        if not candidate_res.data: raise Exception("Failed to insert candidate")
        candidate_id = candidate_res.data[0]['id']
        
        if hr_id:
            supabase.table('hr_users').upsert({"id": hr_id, "name": hr_name, "email": hr_email}).execute()
        else:
            hr_res = supabase.table('hr_users').select('id').limit(1).execute()
            hr_id = hr_res.data[0]['id'] if hr_res.data else None
            
        if not hr_id: raise Exception("No HR user found.")

        session_res = supabase.table('interview_sessions').insert({
            "hr_id": hr_id, "candidate_id": candidate_id, "role": role,
            "job_description": jd, "cutoff_score": cutoff_score, "status": "scheduled"
        }).execute()
        
        session_id = session_res.data[0]['id']
        interview_link = f"{FRONTEND_URL}/interview/{session_id}"
        
        # 5. Send Professional Email via Resend
        send_interview_email(
            to_email=candidate_email,
            candidate_name=candidate_name,
            role=role,
            interview_link=interview_link
        )
        
        return {"message": "Interview created successfully", "session_id": session_id, "interview_link": interview_link}
        
    except Exception as e:
        print(f"❌ Error creating interview: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 🔍 Get Interview Session Data
@router.get("/interview/{session_id}")
async def get_interview_session(session_id: str):
    try:
        supabase = get_supabase()
        session_res = supabase.table('interview_sessions').select('*').eq('id', session_id).execute()
        if not session_res.data: return JSONResponse(status_code=404, content={"error": "Session not found"})
        session = session_res.data[0]
        
        candidate_res = supabase.table('candidates').select('*').eq('id', session['candidate_id']).execute()
        candidate = candidate_res.data[0] if candidate_res.data else {}
        
        return {
            "session": session,
            "candidate": {"name": candidate.get("name"), "resume_summary": candidate.get("resume_summary")},
            "role": session.get("role"), "jd": session.get("job_description")
        }
    except Exception as e:
        print(f"❌ Error fetching session: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 🎯 Start Interview (Session Based)
@router.post("/start-interview")
async def start_interview_session(data: StartInterviewRequest):
    try:
        supabase = get_supabase()
        session_res = supabase.table('interview_sessions').select('*').eq('id', data.session_id).execute()
        if not session_res.data: return JSONResponse(status_code=404, content={"error": "Session not found"})
        session = session_res.data[0]
        
        candidate_res = supabase.table('candidates').select('*').eq('id', session['candidate_id']).execute()
        candidate = candidate_res.data[0] if candidate_res.data else {}
        
        question = generate_first_question(
            role=session['role'],
            jd=session.get('job_description', ''),
            resume_summary=candidate.get('resume_summary', '')
        )
        
        supabase.table('interview_sessions').update({"status": "in_progress", "started_at": datetime.now().isoformat()}).eq('id', data.session_id).execute()
        return {"question": question}
    except Exception as e:
        print(f"❌ Error starting interview: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 🔄 Next Question (Session Based)
@router.post("/next-question")
async def next_question_session(data: NextQuestionRequest):
    try:
        supabase = get_supabase()
        supabase.table('interview_responses').insert({
            "session_id": data.session_id, "question": data.previous_question, "answer": data.answer
        }).execute()
        
        responses_res = supabase.table('interview_responses').select('*').eq('session_id', data.session_id).order('created_at').execute()
        history = []
        for r in responses_res.data:
            history.append({"role": "assistant", "content": r["question"]})
            history.append({"role": "user", "content": r["answer"]})
        
        session_res = supabase.table('interview_sessions').select('*').eq('id', data.session_id).execute()
        session = session_res.data[0]
        candidate_res = supabase.table('candidates').select('*').eq('id', session['candidate_id']).execute()
        candidate = candidate_res.data[0] if candidate_res.data else {}

        if len(responses_res.data) >= 10: # Standard 10 questions
            report_text = generate_interview_report(
                role=session['role'], jd=session.get('job_description', ''),
                resume_summary=candidate.get('resume_summary', ''), history=history
            )
            
            import json
            try:
                clean_json = report_text.strip()
                if clean_json.startswith("```"):
                    lines = clean_json.split("\n")
                    if lines[0].startswith("```"): lines = lines[1:]
                    if lines[-1].startswith("```"): lines = lines[:-1]
                    clean_json = "\n".join(lines).strip()
                
                parsed_report = json.loads(clean_json)
                report_data = {
                    "session_id": data.session_id,
                    "overall_score": float(parsed_report.get("overall_score", 0.0)),
                    "strengths": str(parsed_report.get("strengths", "")),
                    "weaknesses": str(parsed_report.get("weaknesses", "")),
                    "recommendation": str(parsed_report.get("recommendation", "")),
                    "summary": str(parsed_report.get("summary", ""))
                }
                supabase.table('interview_reports').insert(report_data).execute()
                supabase.table('interview_sessions').update({"status": "completed", "ended_at": datetime.now().isoformat()}).eq('id', data.session_id).execute()
                return {"type": "completed", "session_id": data.session_id}
            except Exception as e:
                print(f"⚠️ Report parsing failed: {e}")
                return {"type": "completed", "session_id": data.session_id, "raw_report": report_text}

        result = evaluate_and_continue(
            role=session['role'], jd=session.get('job_description', ''),
            resume_summary=candidate.get('resume_summary', ''), history=history
        )
        return {"type": "question", "question": result}
    except Exception as e:
        print(f"❌ Error in next question: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 📄 Get Interview Report
@router.get("/interview-report/{session_id}")
async def get_interview_report(session_id: str):
    try:
        supabase = get_supabase()
        res = supabase.table('interview_reports').select('*').eq('session_id', session_id).single().execute()
        return res.data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 📋 Get All Interviews (History)
@router.get("/interviews")
async def get_all_interviews(hr_id: Optional[str] = None):
    try:
        supabase = get_supabase()
        query = supabase.table('interview_sessions').select('*, candidates(name, email), interview_reports(overall_score)')
        if hr_id: query = query.eq('hr_id', hr_id)
        res = query.order('created_at', desc=True).execute()
        return res.data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
