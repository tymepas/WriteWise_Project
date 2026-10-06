# WriteWise — AI Writing Platform PRD

## Problem Statement
WriteWise is an AI-powered writing platform for professionals and job seekers. It combines general writing tools (grammar, paraphrase, summarize, humanize) with job-focused intelligence (email generation, tone rewriting) powered by the OpenAI API.

## Architecture
- **Frontend**: React 18, CRA 5 + CRACO, Tailwind CSS, Shadcn UI, Lucide React
- **Backend**: FastAPI, Python (stateless)
- **AI**: OpenAI Responses API via the official `openai` SDK (`OPENAI_API_KEY`, `OPENAI_MODEL`, default `gpt-5.6-terra`)
- **Database**: None (the Emergent version logged per-request metadata to MongoDB; removed Sep 2026)
- **Hosting**: Standalone and self-hosted; no Emergent dependencies (migrated Sep 2026)

## Writing Modes (FROZEN — do not modify prompts)

| Mode | Behavior |
|------|----------|
| Auto | Intent-based routing. Smart rewrite by default. Routes to email if input is job-related or email-like. |
| Grammar | Fixes errors, smooths awkward phrasing. Preserves meaning and tone. |
| Email | Professional email with Subject line. Structured: opening, body, close. Natural not templated. |
| Tone | Rewrites in specified tone. Matches register of original. |
| Rewrite | Tightens clarity and flow. Removes redundancy. Does not add ideas. |
| Paraphrase | 5 styles: Standard, Fluency, Formal, Simple, Creative. Same meaning, different shape. |
| Summarize | Short (2-3 sentences) or Bullet Points (4-6 bullets). |
| Expand | Adds useful context and detail. No filler. |
| Shorten | Cuts to core message. Preserves tone and intent. |
| Humanize | Matches original register. Professional stays professional. Casual becomes conversational. |
| Prompt | (Oct 2026) Turns a rough natural-language message into a clear, LLM-ready request, preserving intent. Clarify and organize, never reinterpret. Own instructions in backend/prompt_mode.py; URLs masked, validated and restored; secrets redacted. |

## AI Prompt Status: FROZEN (Apr 2026)
- SYSTEM_MESSAGE: tone-matching, directness, no em dashes, intent preservation
- All 10 mode prompts: finalized and stable
- Global rules: intent protection, tone-context matching, no meta-commentary
- Do not modify prompts without explicit user approval

## Key Features
- Personalization Panel (Experience, Target Role, Skills)
- Output Variations (3 versions: Professional, Confident, Friendly)
- Why You're a Good Fit bullets (email + job post)
- Output Evaluation scores (Clarity, Professionalism, Personalization) + suggestion
- Quick Templates: Job Application, Follow-up Email, Cold Outreach, Referral Request
- Regenerate button
- Copy to clipboard (with fallback)
- WriteWise SVG logo with gradient W icon
- Loading card with animated W icon
- Dynamic loading messages per mode

## Deployment Status
- Sep 2026: migrated off Emergent to a standalone React + FastAPI + OpenAI stack
- Verified locally on Node 20.19.4 / npm 10.8.2 and Python 3.12
- Secrets live only in backend/.env (git-ignored)

## Backlog

### P1 — Next priorities
- [ ] Generation history (store and display past results per session)
- [ ] Word / character count on textarea
- [ ] Download output as .txt

### P2 — Nice to have
- [ ] LinkedIn message quick template
- [ ] Thank-you note template
- [ ] Export as .docx
- [ ] Share output via link
