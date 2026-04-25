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

VALID_MODES = {"auto", "grammar", "email", "tone", "rewrite"}

SYSTEM_MESSAGE = (
    "You are an advanced AI writing assistant specialized in helping job seekers. "
    "Always respond with valid raw JSON only — no markdown, no code blocks, no extra text. "
    "Output must be directly parseable with json.loads(). "
    "All scores are integers 1–10. Suggestion is 1–2 sentences max."
)


class GenerateRequest(BaseModel):
    mode: str
    input: str
    context: Optional[str] = None
    experience: Optional[str] = None
    target_role: Optional[str] = None
    skills: Optional[str] = None
    variations: bool = False


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


def build_prompt(req: GenerateRequest) -> str:
    # Build personalization context
    profile_parts = []
    if req.experience:
        profile_parts.append(f"Experience: {req.experience}")
    if req.target_role:
        profile_parts.append(f"Target Role: {req.target_role}")
    if req.skills:
        profile_parts.append(f"Skills: {req.skills}")

    profile_section = ""
    if profile_parts:
        profile_section = "User Profile:\n" + "\n".join(f"- {p}" for p in profile_parts) + "\n\n"

    context_line = f"\nExtra Instructions: {req.context.strip()}" if req.context and req.context.strip() else ""
    mode = req.mode

    if mode == "auto":
        mode_task = (
            "Detect the best processing mode for this text:\n"
            '- "grammar": text has grammar/spelling errors needing correction\n'
            '- "email": input is a job posting, email request, or needs to become a professional email\n'
            '- "tone": context mentions a specific tone to apply\n'
            '- "rewrite": text needs clarity/flow improvement\n'
            "Then apply the appropriate transformation."
        )
    elif mode == "grammar":
        mode_task = "Fix all grammar and spelling errors. Preserve meaning and tone exactly."
    elif mode == "email":
        tone_hint = f" Use a {req.context.strip()} tone." if req.context and req.context.strip() else ""
        mode_task = (
            "Write a professional email. If input is a job posting, write a personalized job application email. "
            "If rough text, polish it into a professional email. "
            "Start with 'Subject:' on the first line. 120–180 words. Specific, human-like, avoid generic openers."
            f"{tone_hint}"
        )
    elif mode == "tone":
        target_tone = req.context.strip() if req.context and req.context.strip() else "professional"
        mode_task = f"Rewrite in a {target_tone} tone. Preserve the original meaning exactly."
    elif mode == "rewrite":
        mode_task = "Improve clarity, readability, and flow. Remove redundancy. Make it concise and impactful."
    else:
        mode_task = "Improve the text."

    if req.variations:
        output_schema = (
            '{\n'
            '  "detected_mode": "<mode if auto, else null>",\n'
            '  "variations": [\n'
            '    {"label": "Professional", "output": "<formal, polished version>"},\n'
            '    {"label": "Confident", "output": "<assertive, strong first-person version>"},\n'
            '    {"label": "Friendly", "output": "<warm, approachable version>"}\n'
            '  ],\n'
            '  "why_good_fit": ["<bullet 1>", "<bullet 2>"] or null,\n'
            '  "evaluation": {"clarity": 8, "professionalism": 9, "personalization": 7, "suggestion": "<1-2 line tip>"}\n'
            '}'
        )
    else:
        output_schema = (
            '{\n'
            '  "detected_mode": "<mode if auto, else null>",\n'
            '  "output": "<generated text>",\n'
            '  "why_good_fit": ["<bullet 1>", "<bullet 2>"] or null,\n'
            '  "evaluation": {"clarity": 8, "professionalism": 9, "personalization": 7, "suggestion": "<1-2 line tip>"}\n'
            '}'
        )

    prompt = (
        f"{profile_section}"
        f"Task: {mode_task}\n\n"
        f"Input:\n{req.input}"
        f"{context_line}\n\n"
        "Rules:\n"
        "- why_good_fit: Include 2–3 bullet strings ONLY if mode is email AND the input clearly "
        "resembles a job posting (contains role/company/requirements). Otherwise set to null.\n"
        "- evaluation.personalization: Score higher (8–10) if user profile was meaningfully incorporated.\n"
        "- For variations: Professional = formal/polished; Confident = assertive/direct; Friendly = warm/conversational\n"
        "- All output text must be clean, ready to use, and human-like.\n\n"
        f"Respond ONLY with this JSON (no markdown, no backticks):\n{output_schema}"
    )
    return prompt


def parse_claude_response(raw: str) -> dict:
    cleaned = re.sub(r'```(?:json)?\s*', '', raw)
    cleaned = re.sub(r'```', '', cleaned).strip()
    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    return json.loads(cleaned)


@api_router.get("/")
async def root():
    return {"message": "AI Writing Assistant API"}


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
            detected_mode=data.get("detected_mode"),
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
