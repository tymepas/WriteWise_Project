from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
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

SYSTEM_MESSAGE = (
    "You are an advanced AI writing assistant with strong expertise in professional communication. "
    "Generate high-quality, clean, ready-to-use output. Avoid robotic or generic phrasing. "
    "Keep output natural and human-like. Do not repeat the input unless necessary."
)

MODE_PROMPTS = {
    "grammar": (
        "Correct all grammar and spelling mistakes in the following text. "
        "Do NOT change the meaning, tone, or structure. Output only the corrected text with no explanations.\n\n"
        "Text:\n{input}"
    ),
    "email": (
        "Generate a professional, well-structured email based on the following input.\n"
        "Rules:\n"
        "- If the input is a job posting or description, create a personalized job application email.\n"
        "- If the input is rough text, convert it into a polished professional email.\n"
        "- Include a subject line at the very top in format: Subject: <subject line>\n"
        "- Use clear paragraph structure.\n"
        "- Keep length between 120–180 words.\n"
        "- Avoid generic phrases like 'I am writing to express'.\n"
        "- Make it specific and human-like, using details from the input.\n\n"
        "Input:\n{input}"
        "{context_section}"
    ),
    "tone": (
        "Rewrite the following text in the specified tone. Preserve the original meaning completely. "
        "Output only the rewritten text with no explanations.\n\n"
        "Tone: {tone}\n\n"
        "Text:\n{input}"
    ),
    "rewrite": (
        "Rewrite the following text to improve clarity, readability, and flow. "
        "Make it more structured and impactful. Remove redundancy. Keep it concise and easy to understand. "
        "Output only the rewritten text with no explanations.\n\n"
        "Text:\n{input}"
        "{context_section}"
    ),
}


class GenerateRequest(BaseModel):
    mode: str
    input: str
    context: Optional[str] = None


class GenerateResponse(BaseModel):
    output: str
    mode: str


@api_router.get("/")
async def root():
    return {"message": "AI Writing Assistant API"}


@api_router.post("/generate", response_model=GenerateResponse)
async def generate_text(req: GenerateRequest):
    if req.mode not in MODE_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}. Use grammar, email, tone, or rewrite.")

    if not req.input or not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM API key not configured.")

    session_id = str(uuid.uuid4())

    template = MODE_PROMPTS[req.mode]

    if req.mode == "tone":
        tone = req.context.strip() if req.context and req.context.strip() else "professional"
        prompt = template.format(input=req.input.strip(), tone=tone)
    elif req.mode in ("email", "rewrite"):
        context_section = f"\n\nAdditional context: {req.context.strip()}" if req.context and req.context.strip() else ""
        prompt = template.format(input=req.input.strip(), context_section=context_section)
    else:
        prompt = template.format(input=req.input.strip())

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=SYSTEM_MESSAGE,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)

        await db.generations.insert_one({
            "mode": req.mode,
            "input_length": len(req.input),
            "session_id": session_id,
        })

        return GenerateResponse(output=response, mode=req.mode)

    except Exception as e:
        logger.error(f"LLM generation error: {e}")
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
