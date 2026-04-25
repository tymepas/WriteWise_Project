# WriteWise — AI Writing Platform PRD

## Problem Statement
Transform the AI Writing Assistant into WriteWise, a full-featured writing platform similar to QuillBot, optimized for job seekers and professionals.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI (single-page, component-based)
- **Backend**: FastAPI + Motor (MongoDB) + emergentintegrations (Claude Sonnet 4.5)
- **AI**: Claude Sonnet 4.5 via Emergent Universal LLM Key

## User Personas
- Job seekers applying for roles (primary)
- Professionals needing to polish written communication (secondary)
- Students improving academic writing (tertiary)

## What's Been Implemented

### Phase 1 — MVP (Feb 2026)
- 4 writing modes: Grammar, Email, Tone, Rewrite
- Claude Sonnet 4.5 integration
- Dark theme UI

### Phase 2 — Enhanced (Feb 2026)
- Auto mode (default), Personalization panel
- Output variations (3 versions), Why Good Fit bullets
- Output evaluation scores, Quick templates, Regenerate button

### Phase 3 — WriteWise Platform (Feb 2026)

#### New Modes (Backend + Frontend)
- **Paraphrase** with 5 styles: Standard, Fluency, Formal, Simple, Creative
- **Summarize** with 2 formats: Short Summary (2-3 sentences), Bullet Points (4-6 bullets)
- **Expand**: adds detail, depth, and context
- **Shorten**: trims to core message only
- **Humanize**: removes AI-like phrasing, makes text conversational

#### Backend Updates
- VALID_MODES expanded to 10: auto, grammar, email, tone, rewrite, paraphrase, summarize, expand, shorten, humanize
- GenerateRequest: new fields paraphrase_mode, summary_type
- SYSTEM_MESSAGE: enforces no em dashes, no double hyphens, natural human tone
- build_mode_task(): modular per-mode prompt construction
- Anti-em-dash rule in every prompt

#### Frontend Updates
- 9 tabs (scrollable): Auto, Grammar, Email, Tone, Rewrite, Paraphrase, Summarize, Expand/Shorten, Humanize
- TabOptions component: renders mode-specific pill sub-options
- Dynamic button labels: Expand/Shorten shows "Expand" or "Shorten"
- Dynamic loading messages per mode: "Paraphrasing...", "Summarizing...", "Humanizing...", etc.
- Visibility rules:
  - Variations toggle: only for auto, email, rewrite, tone, paraphrase
  - Personalization panel: only for auto, email, rewrite, tone, humanize
- Context placeholder changes per mode
- QuickTemplates: fixed em dashes in template text

## Backlog / Next Tasks

### P0 (Done)
- [x] All 9 writing modes fully functional
- [x] Dynamic tab sub-options (style/format/action pills)
- [x] Anti-em-dash output enforcement
- [x] Human-like output tone
- [x] Dynamic loading messages

### P1 (Next)
- [ ] Generation history (store and display past results)
- [ ] Word/character count on textarea
- [ ] Download output as .txt

### P2 (Nice to have)
- [ ] LinkedIn message template
- [ ] Thank-you note template
- [ ] Share output via link
- [ ] Export as .docx
