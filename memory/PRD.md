# AI Writing Assistant — PRD

## Problem Statement
Build an AI writing assistant web app with 4 modes: Grammar correction, Email generation (professional emails/job application emails), Tone rewriting, and General rewriting. Powered by Claude Sonnet 4.5 (Anthropic). No login required.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI (single-page app, components-based)
- **Backend**: FastAPI + Motor (MongoDB) + emergentintegrations (Claude Sonnet 4.5)
- **AI**: Claude Sonnet 4.5 via Emergent Universal LLM Key (`sk-emergent-2EaE5662270F1F7FfD`)

## User Personas
- Job seekers (students and professionals applying for roles)
- Need to polish emails, fix grammar, improve writing tone

## Core Requirements (Static)
1. 5 writing modes: Auto (default), Grammar, Email, Tone, Rewrite
2. AI-powered generation via Claude Sonnet 4.5
3. No authentication — open access
4. Dark theme, minimal & clean UI
5. Copy to clipboard feature
6. Target: Job seekers

## What's Been Implemented

### Phase 1 — MVP (Feb 2026)
- `POST /api/generate` with 4 modes
- Claude Sonnet 4.5 integration
- Dark theme UI with Shadcn components

### Phase 2 — Enhanced (Feb 2026)
#### Backend
- **Auto Mode**: Claude detects intent (grammar/email/tone/rewrite) automatically
- **Personalization**: `experience`, `target_role`, `skills` fields in prompt
- **Output Variations**: 3 versions (Professional, Confident, Friendly) in single Claude call
- **Why Good Fit**: 2-3 bullet strings generated for email+job-post inputs
- **Output Evaluation**: Clarity, Professionalism, Personalization scores (1-10) + suggestion
- `detected_mode` only returned for Auto mode (filtered for other modes)
- Structured JSON parsing with fallback for malformed responses

#### Frontend
- **Auto Mode tab** as default (5 tabs total)
- **Quick Templates**: 4 clickable chips (Job Application, Follow-up, Cold Outreach, Referral)
- **Personalization Panel**: Collapsible with Experience, Target Role, Skills inputs
- **Multiple Versions toggle**: Switch to request 3 variations
- **OutputSection component**: Handles single output, 3 variation cards, why_good_fit, score bars
- **Regenerate button** on all output types
- **Evaluation scores** with animated progress bars
- **Detected mode badge** (only shown in Auto mode)

## Backlog / Next Tasks

### P0 (Core, done)
- [x] Grammar correction mode
- [x] Email generation mode
- [x] Tone rewriting mode
- [x] General rewriting mode
- [x] Auto mode (intent detection)
- [x] Copy to clipboard (with fallback)
- [x] Personalization (Experience, Target Role, Skills)
- [x] Output variations (3 versions)
- [x] Why Good Fit bullets
- [x] Evaluation scores
- [x] Quick templates (4)
- [x] Regenerate button

### P1 (Next priorities)
- [ ] Generation history — store and display past results
- [ ] Word/character count display on textarea
- [ ] Download output as .txt

### P2 (Nice to have)
- [ ] User accounts / saved sessions
- [ ] More template types (LinkedIn message, Thank-you note)
- [ ] Share output via link
- [ ] Export as .docx
