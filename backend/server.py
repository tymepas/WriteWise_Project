from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import json
import re
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VALID_MODES = {
    "auto", "grammar", "email", "tone", "rewrite",
    "paraphrase", "summarize", "expand", "shorten", "humanize"
}

SYSTEM_MESSAGE = (
    "You are WriteWise, a sharp AI writing assistant for professionals and job seekers. "
    "Always respond with valid raw JSON only. No markdown, no code blocks, no extra text outside the JSON. "

    "Every word of output text must follow these rules: "
    "1. Never use em dashes or double hyphens. Use a comma or full stop instead. "
    "2. Write like a sharp, thoughtful human, not a corporate document or a chatbot. "
    "3. Vary sentence length. Mix short punchy sentences with longer ones. Never make every sentence the same shape. "
    "4. Cut dead weight. Remove: 'It is important to note', 'In conclusion', 'As mentioned', "
    "'I am writing to express', 'I am pleased to', 'I believe I would be a great fit', "
    "'leverage', 'synergy', 'utilize', 'furthermore', 'in order to', 'it goes without saying'. "
    "5. Say things directly. If it can be shorter, make it shorter. "
    "6. Do not over-explain obvious things. Trust the reader. "
    "7. Avoid parallel sentence structures that feel mechanical or AI-generated. "
    "8. Output must be ready to copy and use immediately. No placeholders, no meta-commentary, no notes. "

    "All evaluation scores are integers 1 to 10. Suggestion is one direct, actionable sentence."
)

PARAPHRASE_STYLES = {
    "standard": "varied wording and sentence structure, same register as the original",
    "fluency":  "smoother flow and easier reading, fix anything that sounds clunky",
    "formal":   "professional and academic register, precise word choices",
    "simple":   "plain everyday language, short sentences, no jargon",
    "creative": "fresh and inventive phrasing, different angle on the same idea",
}


class GenerateRequest(BaseModel):
    mode: str
    input: str
    context: Optional[str] = None
    experience: Optional[str] = None
    target_role: Optional[str] = None
    skills: Optional[str] = None
    variations: bool = False
    paraphrase_mode: Optional[str] = None
    summary_type: Optional[str] = None


class EvaluationScore(BaseModel):
    clarity: int
    professionalism: int
    personalization: int
    suggestion: str


class VariationOutput(BaseModel):
    label: str
    output: str


class GenerateResponse(BaseModel):
    output: Optional[str] = None
    variations: Optional[List[VariationOutput]] = None
    mode: str
    detected_mode: Optional[str] = None
    why_good_fit: Optional[List[str]] = None
    evaluation: Optional[EvaluationScore] = None


def build_profile_section(req: GenerateRequest) -> str:
    parts = []
    if req.experience:
        parts.append(f"Experience: {req.experience}")
    if req.target_role:
        parts.append(f"Target Role: {req.target_role}")
    if req.skills:
        parts.append(f"Skills: {req.skills}")
    if parts:
        return "User Profile:\n" + "\n".join(f"- {p}" for p in parts) + "\n\n"
    return ""


def build_mode_task(req: GenerateRequest) -> str:
    mode = req.mode
    ctx = req.context.strip() if req.context and req.context.strip() else ""

    if mode == "auto":
        return (
            "Rewrite this text to improve clarity, flow, and readability. "
            "Fix grammar naturally as part of the rewrite. "
            "Remove repetition and awkward phrasing. Keep the output tight and purposeful. "
            "Sound like a thoughtful human wrote it. Do not make it overly formal or overly casual. "
            "Exception: if the input is clearly a job posting, a request to write an email, or contains "
            "email-like content, write a professional email with a Subject: line instead. "
            "In that case, set detected_mode to 'email'. Otherwise set detected_mode to 'rewrite'. "
            "Either way, always improve the text. Never return it unchanged."
        )

    elif mode == "grammar":
        return (
            "Fix all grammar and spelling errors. "
            "While fixing, smooth out any phrasing that sounds awkward or unnatural. "
            "Do not change the meaning, structure, or tone beyond what grammar requires. "
            "Output only the corrected text."
        )

    elif mode == "email":
        tone_hint = f" Write in a {ctx} tone." if ctx else ""
        return (
            "Write a professional email based on the input. "
            "If the input is a job posting, write a targeted job application email. "
            "If it is rough text or a request, shape it into a polished, ready-to-send email. "
            "Start with 'Subject:' on the first line. "
            "Keep it 120 to 180 words. "
            "Open with something specific to the context. Skip all cliches. "
            "Make it sound like a real person wrote it, not a template. "
            "Use the user profile to make it genuinely specific, not just slot-filled."
            f"{tone_hint}"
        )

    elif mode == "tone":
        target = ctx if ctx else "professional"
        return (
            f"Rewrite in a {target} tone. "
            "Keep the exact meaning. "
            "Do not add ideas or remove any. "
            "Make it sound like someone who naturally speaks that way wrote it, "
            "not like a tone example from a writing guide. "
            "Output only the rewritten text."
        )

    elif mode == "rewrite":
        return (
            "Rewrite for clarity and impact. "
            "Tighten the structure. Cut anything that does not earn its place. "
            "Say things more directly. Prefer shorter over longer wherever meaning allows. "
            "Keep the voice natural and the result easy to read. "
            "Do not add ideas that were not in the original. "
            "Output only the rewritten text."
        )

    elif mode == "paraphrase":
        style_key = (req.paraphrase_mode or "standard").lower()
        style_desc = PARAPHRASE_STYLES.get(style_key, PARAPHRASE_STYLES["standard"])
        return (
            f"Paraphrase using a {style_key} style: {style_desc}. "
            "Change the wording and sentence shapes. Keep the meaning exactly the same. "
            "Do not add ideas or lose any. "
            "Output only the paraphrased text."
        )

    elif mode == "summarize":
        fmt = (req.summary_type or "short").lower()
        if fmt == "bullets":
            return (
                "Summarize as 4 to 6 bullet points. "
                "Start each with '- '. "
                "Most important points only. Keep each bullet tight and scannable. "
                "No padding, no repetition. "
                "Output only the bullet points."
            )
        else:
            return (
                "Write a 2 to 3 sentence summary. "
                "Hit the key points only. "
                "No fluff, no qualifications, no throat-clearing. "
                "Output only the summary."
            )

    elif mode == "expand":
        return (
            "Expand this text by adding context and detail that genuinely helps the reader. "
            "Only add things that earn their place. "
            "Do not pad it out, do not over-explain obvious things, do not repeat yourself. "
            "Keep the structure tight and the voice human. "
            "Output only the expanded text."
        )

    elif mode == "shorten":
        return (
            "Cut this down to the core message. "
            "Remove every word that is not essential. "
            "Do not paraphrase beyond what trimming requires. "
            "Keep what matters. Drop what does not. "
            "Output only the shortened text."
        )

    elif mode == "humanize":
        return (
            "Rewrite this to sound like a real person wrote it. "
            "Remove corporate language, AI-like phrasing, and overly formal structure. "
            "Make the sentences move naturally. Vary the rhythm. "
            "Be direct. Cut anything that sounds like it was written to impress rather than communicate. "
            "Output only the rewritten text."
        )

    return "Improve the text."


def build_prompt(req: GenerateRequest) -> str:
    profile_section = build_profile_section(req)
    mode_task = build_mode_task(req)
    context_line = f"\nExtra Instructions: {req.context.strip()}" if req.context and req.context.strip() else ""

    is_email_related = req.mode in ("email", "auto")
    show_why_fit = is_email_related
    show_eval = True

    if req.variations:
        output_schema = (
            '{\n'
            '  "detected_mode": "<detected mode if auto, else null>",\n'
            '  "variations": [\n'
            '    {"label": "Professional", "output": "<formal, polished version>"},\n'
            '    {"label": "Confident", "output": "<assertive, direct first-person version>"},\n'
            '    {"label": "Friendly", "output": "<warm, approachable version>"}\n'
            '  ],\n'
            '  "why_good_fit": ["<bullet 1>", "<bullet 2>"] or null,\n'
            '  "evaluation": {"clarity": 8, "professionalism": 9, "personalization": 7, "suggestion": "<tip>"}\n'
            '}'
        )
    else:
        output_schema = (
            '{\n'
            '  "detected_mode": "<detected mode if auto, else null>",\n'
            '  "output": "<generated text>",\n'
            '  "why_good_fit": ["<bullet 1>", "<bullet 2>"] or null,\n'
            '  "evaluation": {"clarity": 8, "professionalism": 9, "personalization": 7, "suggestion": "<tip>"}\n'
            '}'
        )

    return (
        f"{profile_section}"
        f"Task: {mode_task}\n\n"
        f"Input:\n{req.input}"
        f"{context_line}\n\n"
        "Rules:\n"
        "- why_good_fit: Include 2 to 3 bullet strings only if this is email mode AND input clearly looks like "
        "a job posting (has role title, requirements, or company info). Each bullet must be specific and concrete, "
        "not generic. Otherwise set to null.\n"
        "- evaluation.personalization: Score 8 to 10 only if the user profile was meaningfully woven into the output.\n"
        "- evaluation.suggestion: One direct, actionable improvement. No fluff.\n"
        "- For variations: Professional means polished and formal. Confident means direct and assertive. "
        "Friendly means warm and approachable. Each must feel genuinely different, not just word-swapped.\n"
        "- NEVER use em dashes or double hyphens anywhere in any output.\n"
        "- Every output must be ready to use immediately. No meta-commentary, no notes, no explanations.\n\n"
        f"Respond ONLY with this JSON (no markdown, no backticks):\n{output_schema}"
    )


def parse_claude_response(raw: str) -> dict:
    cleaned = re.sub(r'```(?:json)?\s*', '', raw)
    cleaned = re.sub(r'```', '', cleaned).strip()
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


@api_router.get("/")
async def root():
    return {"message": "WriteWise API"}


@api_router.post("/generate", response_model=GenerateResponse)
async def generate_text(req: GenerateRequest):
    if req.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}.")
    if not req.input or not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM API key not configured.")

    session_id = str(uuid.uuid4())
    prompt = build_prompt(req)

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=SYSTEM_MESSAGE,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        raw_response = await chat.send_message(UserMessage(text=prompt))

        try:
            data = parse_claude_response(raw_response)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"JSON parse failed: {e}. Using raw as output.")
            data = {"output": raw_response, "evaluation": None, "why_good_fit": None, "detected_mode": None}

        evaluation = None
        if data.get("evaluation"):
            ev = data["evaluation"]
            try:
                evaluation = EvaluationScore(
                    clarity=int(ev.get("clarity", 7)),
                    professionalism=int(ev.get("professionalism", 7)),
                    personalization=int(ev.get("personalization", 7)),
                    suggestion=str(ev.get("suggestion", "")),
                )
            except Exception:
                pass

        variations = None
        if req.variations and data.get("variations"):
            variations = [
                VariationOutput(label=v["label"], output=v["output"])
                for v in data["variations"]
                if isinstance(v, dict) and "label" in v and "output" in v
            ]

        why_good_fit = data.get("why_good_fit")
        if why_good_fit and not isinstance(why_good_fit, list):
            why_good_fit = None

        await db.generations.insert_one({
            "mode": req.mode,
            "detected_mode": data.get("detected_mode"),
            "variations": req.variations,
            "session_id": session_id,
        })

        return GenerateResponse(
            output=data.get("output") if not req.variations else None,
            variations=variations,
            mode=req.mode,
            detected_mode=data.get("detected_mode") if req.mode == "auto" else None,
            why_good_fit=why_good_fit,
            evaluation=evaluation,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
