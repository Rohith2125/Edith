from groq import Groq
from app.config.settings import GROQ_API_KEY
from pypdf import PdfReader
import io


def get_client():
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY")
    return Groq(api_key=GROQ_API_KEY)

def _interviewer_system_prompt(role: str, jd: str = "", resume_summary: str = "") -> str:
    context = ""
    if resume_summary:
        context += f"\n- Candidate Background (from Resume): {resume_summary}"
    if jd:
        context += f"\n- Job Description: {jd}"

    return f"""\
You are EDITH, a senior technical interviewer.

## Context
- Target role: {role}{context}

## Objectives
- Run a structured, realistic technical interview.
- Ask exactly ONE question at a time and wait for the candidate's answer.
- Keep the interview aligned to the target role and experience level.
- Use the candidate's resume and job description to ask highly relevant, specific questions.

## Style guidelines
- Be concise, direct, and professional.
- Prefer practical, job-relevant questions over trivia.
- Avoid multi-part questions. If you need multiple aspects, ask the most important one first.
- Output ONLY plain text - no JSON, no markdown formatting, no code blocks.
- Write naturally as if speaking to the candidate.

## Output format
- For the first question: Output ONLY the question text (one clear sentence ending with a question mark).
- For subsequent questions: First provide a brief comment (1-2 sentences) on the candidate's previous answer, then ask the next question. Format: "[Brief comment on previous answer]. [Next question]"
"""


def generate_first_question(role: str, jd: str = "", resume_summary: str = ""):

    client = get_client()

    messages = [
        {
            "role": "system",
            "content": _interviewer_system_prompt(role=role, jd=jd, resume_summary=resume_summary)
        },
        {
            "role": "user",
            "content": "Start the interview now. Ask the first technical question based on the candidate's resume and the job role. Output ONLY the question text."
        }
    ]

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.7,
    )

    response_text = completion.choices[0].message.content.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
    return response_text


def evaluate_and_continue(role: str, jd: str = "", resume_summary: str = "", history: list = []):

    client = get_client()

    messages = [
        {
            "role": "system",
            "content": _interviewer_system_prompt(role=role, jd=jd, resume_summary=resume_summary)
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": "Briefly comment on my most recent answer (1-2 sentences), then ask the next single technical question. Output ONLY plain text - no JSON, no markdown, no formatting. Format: '[Brief comment]. [Next question]'",
        }
    )

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.7,
    )

    response_text = completion.choices[0].message.content.strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
    return response_text


def generate_interview_report(role: str, jd: str, resume_summary: str, history: list):

    client = get_client()

    messages = [
        {
            "role": "system",
            "content": f"""\
You are EDITH, a senior technical interviewer providing a final performance report for a candidate.

## Context
- Target role: {role}
- Job Description: {jd}
- Candidate Background: {resume_summary}

## Task
Review the entire interview conversation history and provide a structured final evaluation.

## Output Format (STRICT JSON)
You MUST return ONLY a valid JSON object. Do not include any other text or markdown blocks outside the JSON.
{{
  "overall_score": float (0-10),
  "strengths": "string (bullet points separated by semicolons)",
  "weaknesses": "string (bullet points separated by semicolons)",
  "recommendation": "string (Hire / No Hire / etc.)",
  "summary": "string (professional summary)"
}}

Be professional, objective, and specific.
"""
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": "The interview is complete. Generate the performance report now."
        }
    )

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.3, # Lower temperature for more consistent formatting
    )

    return completion.choices[0].message.content.strip()


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extracts all text from a PDF file byte stream."""
    try:
        reader = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""


def summarize_resume(resume_text: str) -> str:
    """Generates a concise professional summary of the extracted resume text."""
    if not resume_text:
        return "No text could be extracted from the resume."

    client = get_client()
    messages = [
        {
            "role": "system",
            "content": "You are an HR AI assistant. Your task is to provide a concise, professional summary (maximum 150 words) of a candidate's resume focusing on key skills, experience, and achievements."
        },
        {
            "role": "user",
            "content": f"Summarize this resume:\n\n{resume_text[:4000]}"  # Truncate to avoid token limits
        }
    ]

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.5,
    )

    return completion.choices[0].message.content.strip()
