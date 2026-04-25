# AI Writing Assistant — PRD

## Problem Statement
Build an AI writing assistant web app with 4 modes: Grammar correction, Email generation (professional emails/job application emails), Tone rewriting, and General rewriting. Powered by Claude Sonnet 4.5 (Anthropic). No login required.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI (single-page app)
- **Backend**: FastAPI + Motor (MongoDB) + emergentintegrations (Claude Sonnet 4.5)
- **AI**: Claude Sonnet 4.5 via Emergent Universal LLM Key

## User Personas
- Job seekers (students and professionals applying for roles)
- Need to polish emails, fix grammar, improve writing tone

## Core Requirements (Static)
1. 4 writing modes: Grammar, Email, Tone, Rewrite
2. AI-powered generation via Claude Sonnet 4.5
3. No authentication — open access
4. Dark theme, minimal & clean UI
5. Copy to clipboard feature
6. Target: Job seekers

## What's Been Implemented (Feb 2026)

### Backend
- `POST /api/generate` — accepts `{mode, input, context}`, returns `{output, mode}`
- Mode-specific prompts for Grammar, Email, Tone, Rewrite
- Claude Sonnet 4.5 via `emergentintegrations` library
- EMERGENT_LLM_KEY configured in `.env`
- Logs generation metadata (mode, input_length, session_id) to MongoDB

### Frontend
- Single-page app with full dark theme (`#09090B` background)
- 4 mode tabs (Grammar, Email, Tone, Rewrite) using Shadcn Tabs
- Large textarea for input, optional context/tone input field
- Generate button (white CTA)
- Output display card with fade-in animation
- Copy to clipboard (with `execCommand` fallback)
- Sonner toast notifications
- IBM Plex Sans + JetBrains Mono fonts
- Background texture image (subtle opacity)

## Backlog / Next Tasks

### P0 (Core, done)
- [x] Grammar correction mode
- [x] Email generation mode  
- [x] Tone rewriting mode
- [x] General rewriting mode
- [x] Copy to clipboard
- [x] Dark theme UI
- [x] Claude Sonnet 4.5 integration

### P1 (Next priorities)
- [ ] Generation history — store and display past results
- [ ] Character/word count display
- [ ] Download output as .txt

### P2 (Nice to have)
- [ ] User accounts / saved sessions
- [ ] Multiple email templates (follow-up, cover letter, etc.)
- [ ] Share output via link
- [ ] Export as .docx
