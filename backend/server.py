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
    "You are WriteWise, a smart AI writing assistant for professionals and job seekers. "
    "Always respond with valid raw JSON only. No markdown, no code blocks, no extra text outside the JSON. "
    "CRITICAL writing rules that apply to every word of output text: "
    "Never use em dashes or double hyphens. Replace them with commas or full stops. "
    "Write naturally and conversationally. Vary sentence length. "
    "Avoid AI-sounding patterns like overuse of formal connectors, perfectly balanced sentences, or repetitive structure. "
    "Sound human. Imperfect is better than robotic. "
    "All scores are integers 1 to 10. Suggestion is 1 to 2 sentences max."
)

PARAPHRASE_STYLES = {
    "standard": "natural rewrite with varied wording and sentence structure",
    "fluency": "smooth, easy-to-read version with improved flow",
    "formal": "professional and academic register",
    "simple": "plain language with shorter sentences, easy to understand",
    "creative": "inventive rewriting with fresh, vivid phrasing",
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
            "Detect the best processing mode for this input:\n"
            '- "grammar": text has grammar or spelling errors needing correction\n'
            '- "email": input is a job posting, email request, or needs to become a professional email\n'
            '- "tone": context mentions a specific tone to apply\n'
            '- "rewrite": text needs clarity or flow improvement\n'
            '- "paraphrase": user wants the same meaning in different words\n'
            '- "summarize": user wants a shorter summary or key points\n'
            '- "humanize": text sounds robotic or AI-generated\n'
            "Then apply the appropriate transformation."
        )
    elif mode == "grammar":
        return "Fix all grammar and spelling errors. Preserve meaning and tone exactly. No explanations."
    elif mode == "email":
        tone_hint = f" Use a {ctx} tone." if ctx else ""
        return (
            "Write a professional email. If input is a job posting, write a personalized job application email. "
            "If rough text, polish it into a professional email. "
            "Start with 'Subject:' on the first line. Keep it 120 to 180 words. "
            "Be specific and human. Do not start with 'I am writing to' or similar cliches."
            f"{tone_hint}"
        )
    elif mode == "tone":
        target = ctx if ctx else "professional"
        return f"Rewrite in a {target} tone. Keep the original meaning exactly. Output only the rewritten text."
    elif mode == "rewrite":
        return "Improve clarity, readability, and flow. Remove redundancy. Make it concise and impactful. Output only the rewritten text."
    elif mode == "paraphrase":
        style_key = (req.paraphrase_mode or "standard").lower()
        style_desc = PARAPHRASE_STYLES.get(style_key, PARAPHRASE_STYLES["standard"])
        return (
            f"Paraphrase the following text using a {style_key} style: {style_desc}. "
            "Preserve the original meaning but change structure and wording. Output only the paraphrased text."
        )
    elif mode == "summarize":
        fmt = (req.summary_type or "short").lower()
        if fmt == "bullets":
            return (
                "Summarize the following text as 4 to 6 clear bullet points. "
                "Start each bullet with a dash and a space. Capture the most important information. "
                "Output only the bullet points."
            )
        else:
            return (
                "Write a 2 to 3 sentence summary of the following text. "
                "Be concise and capture the key points. Output only the summary."
            )
    elif mode == "expand":
        return (
            "Expand the following text by adding relevant detail, depth, and context. "
            "Make it more complete and informative while keeping a natural, conversational tone. "
            "Output only the expanded text."
        )
    elif mode == "shorten":
        return (
            "Shorten the following text to its core message. "
            "Remove redundancy and unnecessary words. Keep only what truly matters. "
            "Output only the shortened text."
        )
    elif mode == "humanize":
        return (
            "Rewrite the following text to sound natural and human. "
            "Remove AI-like phrasing, overly formal language, and robotic structure. "
            "Make it conversational and realistic. Vary sentence length naturally. "
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
        f"- why_good_fit: Include 2 to 3 bullet strings only if mode is email and input clearly resembles a job posting. Otherwise null.\n"
        "- evaluation.personalization: Score 8 to 10 if user profile was meaningfully used in the output.\n"
        "- For variations: Professional is formal and polished. Confident is assertive and direct. Friendly is warm and conversational.\n"
        "- NEVER use em dashes or double hyphens in any output text. Use commas or full stops instead.\n"
        "- All output must sound human and natural. Vary sentence length.\n\n"
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
