from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
import re
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

import prompt_mode
from secret_redaction import redact_secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-5.6-terra"

# A max-length (12,000 character) rewrite needs roughly 4,000 output tokens,
# plus a few hundred for reasoning and the JSON wrapper.
MAX_OUTPUT_TOKENS = 6000
# Keeps retries inside Vercel's 300 s function limit.
OPENAI_TIMEOUT_SECONDS = 90
OPENAI_MAX_RETRIES = 1

MAX_INPUT_CHARS = 12_000
MAX_CONTEXT_CHARS = 2_000
MAX_EXPERIENCE_CHARS = 1_000
MAX_TARGET_ROLE_CHARS = 300
MAX_SKILLS_CHARS = 1_000
MAX_OPTION_CHARS = 50

FIELD_LABELS = {
    "input": "Your text",
    "context": "Additional context",
    "experience": "Experience",
    "target_role": "Target role",
    "skills": "Skills",
    "mode": "Mode",
    "variations": "Multiple versions",
    "paraphrase_mode": "Paraphrase style",
    "summary_type": "Summary format",
    "tone": "Tone",
    "rewrite_goal": "Rewrite goal",
}

# Created on first use so the server can start (and report a clear error) without a key.
openai_client: Optional[AsyncOpenAI] = None

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VALID_MODES = {
    "auto", "grammar", "email", "tone", "rewrite",
    "paraphrase", "summarize", "expand", "shorten", "humanize", "prompt"
}

UNEXPECTED_RESPONSE = "The AI service returned an unexpected response. Please try again."

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
    "Never invent facts about the user: no experience, skills, employers, education, qualifications, "
    "achievements or metrics they did not provide. Never invent names or write bracketed placeholders such as [Your Name]. "

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
                                   "and any real urgency. State problems, delays and missed deadlines neutrally "
                                   "instead of leaving them out"),
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


SUMMARY_TYPES = ("short", "bullets")

CONTROLLED_OPTIONS = {
    "paraphrase_mode": tuple(PARAPHRASE_STYLES),
    "summary_type": SUMMARY_TYPES,
    "tone": tuple(TONES),
    "rewrite_goal": tuple(REWRITE_GOALS),
}

AUTO_DETECTED_MODES = {"email", "rewrite"}


class GenerateRequest(BaseModel):
    mode: str = Field(max_length=MAX_OPTION_CHARS)
    input: str = Field(max_length=MAX_INPUT_CHARS)
    context: Optional[str] = Field(default=None, max_length=MAX_CONTEXT_CHARS)
    experience: Optional[str] = Field(default=None, max_length=MAX_EXPERIENCE_CHARS)
    target_role: Optional[str] = Field(default=None, max_length=MAX_TARGET_ROLE_CHARS)
    skills: Optional[str] = Field(default=None, max_length=MAX_SKILLS_CHARS)
    variations: bool = False
    paraphrase_mode: Optional[str] = Field(default=None, max_length=MAX_OPTION_CHARS)
    summary_type: Optional[str] = Field(default=None, max_length=MAX_OPTION_CHARS)
    tone: Optional[str] = Field(default=None, max_length=MAX_OPTION_CHARS)
    rewrite_goal: Optional[str] = Field(default=None, max_length=MAX_OPTION_CHARS)

    # Controlled options must be one of the known values so they never become
    # free-form prompt text. Missing or empty values keep the default behaviour.
    @field_validator("paraphrase_mode", "summary_type", "tone", "rewrite_goal")
    @classmethod
    def check_option(cls, value: Optional[str], info) -> Optional[str]:
        if value is None or not value.strip():
            return None
        normalized = value.strip().lower()
        allowed = CONTROLLED_OPTIONS[info.field_name]
        if normalized not in allowed:
            raise ValueError(f"must be one of: {', '.join(allowed)}")
        return normalized


class EvaluationScore(BaseModel):
    clarity: int
    professionalism: int
    # None when no User Profile was given, since there was nothing to personalize.
    personalization: Optional[int] = None
    suggestion: Optional[str] = None


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
    # Prompt mode only: how many possible secrets were removed before calling OpenAI; None when none.
    secrets_redacted: Optional[int] = None


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
            "Use the user profile to make it genuinely specific, not just slot-filled. "
            "Describe the user's background only with facts from the User Profile or the user's own words in the Input. "
            "A job posting's requirements describe the role, not the user: never present them as the user's experience or skills. "
            "If the user's background is not provided, express interest and fit for the role without claiming any specific "
            "experience, skills or qualifications."
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
                "Tone changes the style, never the facts. Keep every number, count, date, deadline, time, amount and name, "
                "how many times something has already been asked, every concrete request, and any important context. "
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

    personalization_schema = "<integer 1-10>" if profile_section else "null"
    evaluation_schema = (
        '{"clarity": <integer 1-10>, "professionalism": <integer 1-10>, '
        f'"personalization": {personalization_schema}, "suggestion": "<one specific, actionable improvement>"}}'
    )

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
            f'  "evaluation": {evaluation_schema}\n'
            '}'
        )
    else:
        output_schema = (
            '{\n'
            '  "detected_mode": "<detected mode if auto, else null>",\n'
            '  "output": "<generated text>",\n'
            '  "why_good_fit": ["<bullet 1>", "<bullet 2>"] or null,\n'
            f'  "evaluation": {evaluation_schema}\n'
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
        "- Facts about the user: Only state the user's experience, years, skills, tools, qualifications, employers, "
        "education, certifications, achievements or metrics if they are explicitly given in the User Profile or written "
        "by the user about themselves in the Input. A job posting's requirements describe the role, not the user: never "
        "present or imply them as the user's experience or skills. This rule limits what you claim, not what you write: "
        "a job posting still gets an application email, written without unsupported claims.\n"
        "- why_good_fit: Include 2 to 3 bullet strings only if this is email mode AND input clearly looks like "
        "a job posting (has role title, requirements, or company info) AND the user supplied their own background in "
        "the User Profile or the Input. Each bullet must connect a specific fact the user supplied to a specific "
        "requirement of the role. Never describe the role alone and never use facts the user did not supply. "
        "Write each bullet without a subject or addressed to 'you'; never write 'the user'. "
        "Otherwise set to null.\n"
        "- Names and placeholders: Never invent names or identities. Do not write bracketed placeholders such as "
        "[Your Name], [Company Name], [Hiring Manager] or [Job Title] unless that exact placeholder appears in the Input. "
        "If the user's name is not given, end the email with a closing such as 'Best regards,' and no name. Use a "
        "company name, role title or person's name only if it appears in the Input; otherwise use a neutral greeting "
        "such as 'Dear Hiring Team,'.\n"
        "- evaluation: Score the output honestly; do not reuse example numbers. "
        "evaluation.personalization: Score 8 to 10 only if the user profile was meaningfully woven into the output; "
        "use null when there is no User Profile.\n"
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


def parse_score(value) -> Optional[int]:
    """Return a 1-10 integer score, or None if the model did not give a valid one."""
    if isinstance(value, bool):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    if isinstance(value, int) and 1 <= value <= 10:
        return value
    return None


def parse_evaluation(ev, has_profile: bool) -> Optional[EvaluationScore]:
    """Keep only scores the model actually gave; never fill in defaults."""
    if not isinstance(ev, dict):
        return None
    clarity = parse_score(ev.get("clarity"))
    professionalism = parse_score(ev.get("professionalism"))
    if clarity is None or professionalism is None:
        return None
    suggestion = ev.get("suggestion")
    if not isinstance(suggestion, str) or not suggestion.strip() or re.fullmatch(r"\s*<[^>]*>\s*", suggestion):
        suggestion = None
    return EvaluationScore(
        clarity=clarity,
        professionalism=professionalism,
        personalization=parse_score(ev.get("personalization")) if has_profile else None,
        suggestion=suggestion.strip() if suggestion else None,
    )


PLACEHOLDER_LINE = re.compile(r"^\s*\[[^\[\]\n]{1,60}\]\s*$")


def remove_invented_placeholder_lines(text: str, user_text: str) -> str:
    """Drop lines that are only a bracketed placeholder (e.g. "[Your Name]") the user did not write."""
    if not isinstance(text, str):
        return text
    lines = [
        line for line in text.split("\n")
        if not (PLACEHOLDER_LINE.match(line) and line.strip() not in user_text)
    ]
    return "\n".join(lines).rstrip()


def log_openai_error(e: Exception, req: GenerateRequest) -> None:
    # Log enough to debug in production without the user's text.
    logger.error(
        "OpenAI error: type=%s status=%s code=%s request_id=%s mode=%s input_chars=%d",
        type(e).__name__, getattr(e, "status_code", None), getattr(e, "code", None),
        getattr(e, "request_id", None), req.mode, len(req.input),
    )


def describe_validation_error(err: dict) -> str:
    loc = [part for part in err.get("loc", ()) if part != "body"]
    field = str(loc[0]) if loc else None
    label = FIELD_LABELS.get(field, "The request")
    if err.get("type") == "string_too_long":
        limit = err.get("ctx", {}).get("max_length")
        value = err.get("input")
        length = f" ({len(value):,} characters)" if isinstance(value, str) else ""
        return f"{label} is too long{length}. The maximum is {limit:,} characters."
    if err.get("type") == "missing":
        return f"{label} is required."
    if err.get("type") == "json_invalid":
        return "The request is not valid JSON."
    if err.get("type") == "value_error":
        reason = str(err.get("msg", "")).removeprefix("Value error, ")
        return f"{label} {reason}."
    return f"{label} is not valid."


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = list(dict.fromkeys(describe_validation_error(err) for err in exc.errors()))
    return JSONResponse(status_code=400, content={"detail": " ".join(messages) or "Invalid request."})


async def request_model(instructions: str, prompt: str, req: GenerateRequest) -> str:
    """One OpenAI call. Returns the raw text, or raises an HTTPException for a cut-off response."""
    response = await openai_client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=prompt,
        # The prompts already demand raw JSON; JSON mode guarantees it is well-formed.
        text={"format": {"type": "json_object"}},
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )

    # A cut-off response is not valid JSON, so never show it as a result.
    if response.status == "incomplete":
        reason = getattr(response.incomplete_details, "reason", None)
        logger.warning(
            "OpenAI response incomplete: reason=%s mode=%s input_chars=%d variations=%s",
            reason, req.mode, len(req.input), req.variations,
        )
        if reason == "max_output_tokens":
            raise HTTPException(
                status_code=422,
                detail="The result was too long to generate in full. "
                       "Try a shorter text, or turn off Multiple versions.",
            )
        if reason == "content_filter":
            raise HTTPException(
                status_code=422,
                detail="This text could not be processed by the AI service. Please try different text.",
            )
        raise HTTPException(
            status_code=502,
            detail="The AI service could not complete this request. Please try again.",
        )

    return response.output_text


def refined_text(raw_response: str, masked_input: str) -> str:
    """The refined message from a Prompt mode response, still containing link placeholders."""
    try:
        # Plain JSON first: the lenient parser strips ``` everywhere, which would remove
        # code blocks the user put in their message.
        data = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        try:
            data = parse_model_response(raw_response)
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.warning("JSON parse failed: %s", type(e).__name__)
            data = None
    text = prompt_mode.clean_output(data.get("output"), masked_input) if isinstance(data, dict) else ""
    if not text:
        logger.warning("Model response had no usable text: mode=prompt")
        raise HTTPException(status_code=502, detail=UNEXPECTED_RESPONSE)
    return text


async def generate_prompt_mode(req: GenerateRequest) -> GenerateResponse:
    """Refine a rough message into a clear request for another AI, keeping its meaning."""
    # Obvious secrets never reach OpenAI. Only the kind and count are logged, never the values.
    user_text, kinds = redact_secrets(req.input)
    if kinds:
        logger.warning("Redacted %d possible secret(s) before calling OpenAI: kinds=%s mode=prompt",
                       len(kinds), ",".join(sorted(set(kinds))))

    # Context, profile and variations are not used: Prompt mode refines only the message itself.
    masked_input, urls = prompt_mode.mask_urls(user_text)
    text = refined_text(
        await request_model(prompt_mode.SYSTEM_MESSAGE, prompt_mode.build_prompt(masked_input), req),
        masked_input,
    )

    # Links are restored only where the model placed them. If it dropped, invented or repeated a
    # placeholder, ask once more; never guess where a link belongs.
    problem = prompt_mode.link_problem(text, masked_input)
    if problem:
        logger.warning("Prompt mode link placeholders not kept, retrying once: %s urls=%d", problem, len(urls))
        text = refined_text(
            await request_model(prompt_mode.SYSTEM_MESSAGE, prompt_mode.build_retry_prompt(masked_input, problem), req),
            masked_input,
        )
        problem = prompt_mode.link_problem(text, masked_input)
        if problem:
            logger.warning("Prompt mode link placeholders not kept after retry: %s urls=%d", problem, len(urls))
            raise HTTPException(
                status_code=502,
                detail="WriteWise could not keep your links intact this time. Please try again.",
            )

    output = remove_invented_placeholder_lines(prompt_mode.restore_urls(text, urls), user_text)
    if not output.strip():
        raise HTTPException(status_code=502, detail=UNEXPECTED_RESPONSE)
    return GenerateResponse(output=output, mode=req.mode, secrets_redacted=len(kinds) or None)


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
        openai_client = AsyncOpenAI(
            api_key=api_key,
            timeout=OPENAI_TIMEOUT_SECONDS,
            max_retries=OPENAI_MAX_RETRIES,
        )

    try:
        if req.mode == "prompt":
            return await generate_prompt_mode(req)

        raw_response = await request_model(SYSTEM_MESSAGE, build_prompt(req), req)

        try:
            data = parse_model_response(raw_response)
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            data = None
            logger.warning("JSON parse failed: %s", type(e).__name__)
        if not isinstance(data, dict):
            logger.warning("Model response was not a JSON object: mode=%s", req.mode)
            raise HTTPException(
                status_code=502,
                detail="The AI service returned an unexpected response. Please try again.",
            )

        has_profile = bool(build_profile_section(req))
        evaluation = parse_evaluation(data.get("evaluation"), has_profile)

        # Everything the user typed, so placeholders they wrote themselves are kept.
        user_text = " ".join(filter(None, [req.input, req.context, req.experience, req.target_role, req.skills]))

        variations = None
        if req.variations and isinstance(data.get("variations"), list):
            variations = [
                VariationOutput(label=v["label"], output=remove_invented_placeholder_lines(v["output"], user_text))
                for v in data["variations"]
                if isinstance(v, dict) and isinstance(v.get("label"), str) and isinstance(v.get("output"), str)
            ] or None

        why_good_fit = data.get("why_good_fit")
        if isinstance(why_good_fit, list):
            why_good_fit = [b for b in why_good_fit if isinstance(b, str) and b.strip()] or None
        else:
            why_good_fit = None

        output = data.get("output") if not req.variations else None
        if output is not None:
            output = remove_invented_placeholder_lines(str(output), user_text)

        if not (output and output.strip()) and not variations:
            logger.warning("Model response had no usable text: mode=%s variations=%s", req.mode, req.variations)
            raise HTTPException(
                status_code=502,
                detail="The AI service returned an unexpected response. Please try again.",
            )

        detected_mode = data.get("detected_mode") if req.mode == "auto" else None
        if detected_mode not in AUTO_DETECTED_MODES:
            detected_mode = None

        return GenerateResponse(
            output=output,
            variations=variations,
            mode=req.mode,
            detected_mode=detected_mode,
            why_good_fit=why_good_fit,
            evaluation=evaluation,
        )

    except HTTPException:
        raise
    except AuthenticationError:
        logger.error("Generation error: OpenAI rejected the API key.")
        raise HTTPException(status_code=500, detail="LLM API key is invalid.")
    except (PermissionDeniedError, NotFoundError) as e:
        # For example, the configured OPENAI_MODEL is unavailable to this API key.
        log_openai_error(e, req)
        raise HTTPException(status_code=500, detail="The AI service is not configured correctly.")
    except RateLimitError as e:
        log_openai_error(e, req)
        raise HTTPException(status_code=429, detail="WriteWise is busy right now. Please try again in a moment.")
    except BadRequestError as e:
        log_openai_error(e, req)
        raise HTTPException(status_code=502, detail="The AI service could not process this request.")
    except APIStatusError as e:
        log_openai_error(e, req)
        raise HTTPException(status_code=502, detail="The AI service had a problem. Please try again.")
    except APITimeoutError as e:
        log_openai_error(e, req)
        raise HTTPException(status_code=504, detail="The AI service took too long to respond. Please try again.")
    except APIConnectionError as e:
        log_openai_error(e, req)
        raise HTTPException(status_code=503, detail="Could not reach the AI service. Please try again.")
    except Exception:
        logger.exception("Generation error: mode=%s", req.mode)
        raise HTTPException(status_code=500, detail="Something went wrong while generating. Please try again.")


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
