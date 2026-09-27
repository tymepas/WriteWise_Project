from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
import re
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List
from openai import AsyncOpenAI, AuthenticationError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-5.6-terra"

# Created on first use so the server can start (and report a clear error) without a key.
openai_client: Optional[AsyncOpenAI] = None

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

    "Every word of output text must follow these standards: "
    "Write like a thoughtful human. Vary sentence length. Prefer clarity and directness. "
    "Cut words that add length without adding meaning. "
    "Match the tone and register of the context. A professional email should stay professional. "
    "A casual message can be conversational. Do not flatten everything to the same casual register. "
    "Improve expression, never alter the user's intended meaning. "
    "Never use em dashes or double hyphens. Use a comma or full stop instead. "
    "Output must be ready to use immediately. No placeholders, no meta-commentary. "

    "All evaluation scores are integers 1 to 10. Suggestion is one direct, actionable sentence."
)

PARAPHRASE_STYLES = {
    "standard": "varied wording and sentence structure, same register as the original",
    "fluency":  "smoother flow and easier reading, fix anything that sounds clunky",
    "formal":   "professional and academic register, precise word choices",
    "simple":   "plain everyday language, short sentences, no jargon",
    "creative": "fresh and inventive phrasing, different angle on the same idea",
}

TONES = {
    "professional": ("professional", "clear, respectful and businesslike, suitable for work"),
    "casual":       ("casual", "relaxed and conversational, like talking to a colleague you know well; contractions are fine"),
    "friendly":     ("friendly", "warm, positive and approachable"),
    "diplomatic":   ("diplomatic", "tactful and courteous. Turn demands, blame and confrontational or accusatory "
                                   "phrasing into respectful, cooperative requests, while keeping the same request "
                                   "and any real urgency"),
    "formal":       ("formal", "formal register with precise wording, no contractions or slang"),
    "confident":    ("confident", "assured and decisive, with no hedging or apologetic language"),
    "persuasive":   ("persuasive", "makes a compelling case with clear reasons and a clear ask, without inventing facts"),
    "empathetic":   ("empathetic", "acknowledges the reader's situation and feelings with genuine care"),
}

REWRITE_GOALS = {
    "clear_concise":   "Make it clear and concise. Tighten the structure, cut anything that does not earn its place, "
                       "and prefer shorter over longer wherever meaning allows.",
    "more_direct":     "Make it more direct. Lead with the main point, use active voice, and remove hedging, filler "
                       "and qualifiers that weaken the message.",
    "more_polished":   "Make it more polished. Improve word choice, flow and transitions so it reads as carefully "
                       "written, without making it longer than it needs to be.",
    "more_persuasive": "Make it more persuasive. Strengthen the main argument or request, make the reason or benefit "
                       "clear, and end with a clear point or ask. Do not invent facts, numbers or claims.",
    "simplify":        "Simplify it. Use plain everyday words and shorter sentences. Keep every key point.",
    "keep_style":      "Keep the writer's own style and voice. Fix awkward phrasing, repetition and unclear structure, "
                       "but keep their word choices, rhythm and level of formality wherever they already work.",
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
    tone: Optional[str] = None
    rewrite_goal: Optional[str] = None


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
            "Read the input and decide what it needs most, then do that. "
            "Use your judgement: "
            "If it has grammar issues, fix them as part of improving the text. "
            "If it looks like a job posting or an email request, write a professional email with a Subject: line. "
            "If it is a draft or rough idea, rewrite it for clarity and flow. "
            "If it sounds robotic or stiff, make it more natural. "
            "The default action is to improve the writing so it reads clearly, sounds human, and gets to the point. "
            "Set detected_mode to 'email' if you wrote an email, otherwise set it to 'rewrite'. "
            "Always produce a meaningfully improved version. Never return the text unchanged."
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
            "Keep the structure clear: a focused opening, a body that makes the case, and a short close. "
            "Open with something specific to the context. Skip all cliches. "
            "Sound like a real professional, not a template. Natural and structured at the same time. "
            "Use the user profile to make it genuinely specific, not just slot-filled."
            f"{tone_hint}"
        )

    elif mode == "tone":
        tone = TONES.get((req.tone or "").strip().lower())
        if tone:
            label, desc = tone
            return (
                f"Rewrite in a {label} tone: {desc}. "
                f"The selected {label} tone takes priority over the tone of the original text. "
                f"Change wording, phrasing and sentence structure as much as needed so the result clearly sounds {label}. "
                "Keep the same meaning, facts and requests. "
                "Do not add ideas or remove any. "
                "Make it sound like someone who naturally speaks that way wrote it, "
                "not like a tone example from a writing guide. "
                "Output only the rewritten text."
            )
        # Older clients sent the tone in the context field.
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
        goal = REWRITE_GOALS.get((req.rewrite_goal or "").strip().lower())
        if goal:
            return (
                "Rewrite to improve how this is structured and expressed. "
                f"Goal: {goal} "
                "Keep the meaning and the overall tone of the original; this is not a tone change. "
                "Keep the voice natural and the result easy to read. "
                "Do not add ideas that were not in the original. "
                "Output only the rewritten text."
            )
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
            "Cut this down to its core message. "
            "Remove words and phrases that do not add meaning. "
            "Keep enough to preserve the tone and intent. "
            "Do not strip it so bare that it loses clarity or sounds abrupt. "
            "Output only the shortened text."
        )

    elif mode == "humanize":
        return (
            "Rewrite this so it sounds like a real person wrote it. "
            "Keep the meaning exactly the same. "
            "Replace stiff or corporate phrasing with natural, everyday language. "
            "Vary the sentence rhythm. Some sentences can be short. Others longer where it helps. "
            "Read it back and ask: would someone actually say this? If not, change it. "
            "Do not make it too casual unless the original is casual. Match the general register. "
            "Output only the rewritten text."
        )


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
        "- Preserve the user's original intent strictly. Improve how it is expressed, not what it means.\n"
        "- Match the tone of the context. Professional inputs stay professional. Casual inputs can be conversational.\n"
        "- why_good_fit: Include 2 to 3 bullet strings only if this is email mode AND input clearly looks like "
        "a job posting (has role title, requirements, or company info). Each bullet must be specific and concrete, "
        "not generic. Otherwise set to null.\n"
        "- evaluation.personalization: Score 8 to 10 only if the user profile was meaningfully woven into the output.\n"
        "- evaluation.suggestion: One direct, actionable improvement. No fluff.\n"
        "- For variations: Professional means polished and structured. Confident means direct and assertive. "
        "Friendly means warm and approachable. Each must feel genuinely different, not just word-swapped.\n"
        "- NEVER use em dashes or double hyphens anywhere in any output.\n"
        "- Every output must be ready to use immediately. No meta-commentary, no notes, no explanations.\n\n"
        f"Respond ONLY with this JSON (no markdown, no backticks):\n{output_schema}"
    )


def parse_model_response(raw: str) -> dict:
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

    global openai_client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM API key not configured.")
    if openai_client is None:
        openai_client = AsyncOpenAI(api_key=api_key)

    prompt = build_prompt(req)

    try:
        response = await openai_client.responses.create(
            model=OPENAI_MODEL,
            instructions=SYSTEM_MESSAGE,
            input=prompt,
            # The prompts already demand raw JSON; JSON mode guarantees it is well-formed.
            text={"format": {"type": "json_object"}},
        )
        raw_response = response.output_text

        try:
            data = parse_model_response(raw_response)
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
    except AuthenticationError:
        logger.error("Generation error: OpenAI rejected the API key.")
        raise HTTPException(status_code=500, detail="LLM API key is invalid.")
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
async def shutdown_openai_client():
    if openai_client is not None:
        await openai_client.close()
