# WriteWise

**WriteWise** is an AI-powered writing platform built for job seekers and professionals. It combines general writing tools (like QuillBot) with job-focused intelligence, powered by the OpenAI API.

WriteWise is a standalone, self-hosted app: a React frontend talks to a Python FastAPI backend, and the backend calls OpenAI. There is no login and no database.

```
Browser → React frontend (localhost:3000) → FastAPI backend (localhost:8001) → OpenAI API
```

Fix grammar, rewrite content, generate emails, paraphrase text, summarize documents, and more — all in one place.

---

## Features

### 9 Writing Modes

| Mode | What it does |
|------|-------------|
| **Auto** | AI detects your intent and acts on it automatically |
| **Grammar** | Fixes grammar and spelling without changing your voice |
| **Email** | Drafts professional emails and personalized job application emails |
| **Tone** | Changes how the text sounds: Professional, Casual, Friendly, Diplomatic, Formal, Confident, Persuasive, or Empathetic |
| **Rewrite** | Improves how the text is structured and expressed, with an optional goal: Clear & Concise, More Direct, More Polished, More Persuasive, Simplify, or Keep My Style |
| **Paraphrase** | Rewrites with the same meaning in 5 styles: Standard, Fluency, Formal, Simple, Creative |
| **Summarize** | Extracts key points as a short summary or bullet points |
| **Expand / Shorten** | Adds depth or trims text down to what matters |
| **Humanize** | Removes AI-like phrasing and makes text sound naturally written |

### Smart Features

- **Personalization Panel** — Enter your experience, target role, and skills. The AI uses this to personalize outputs, especially emails and rewrites
- **Output Variations** — Generate 3 versions at once: Professional, Confident, and Friendly
- **Why You're a Good Fit** — For job postings, auto-generates 2-3 bullet points explaining your fit
- **Output Evaluation** — Scores output on Clarity, Professionalism, and Personalization (1-10) with an improvement suggestion
- **Quick Templates** — One-click starters for Job Application, Follow-up Email, Cold Outreach, and Referral Request
- **Regenerate** — Re-run the same request for a fresh output
- **Copy to Clipboard** — One-click copy with fallback support

### UX Details

- Dynamic placeholders and context hints per mode
- Dynamic loading messages ("Paraphrasing...", "Summarizing...", "Humanizing..."...)
- Button label changes contextually ("Expand" or "Shorten")
- "Try with Example" CTA auto-fills a real job posting and switches to Email mode
- No em dashes or double hyphens in any AI output — enforced at the system prompt level

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Create React App 5 + CRACO, Tailwind CSS, Shadcn UI, Lucide React |
| Backend | FastAPI, Python |
| AI | OpenAI Responses API via the official `openai` Python SDK (model set by `OPENAI_MODEL`, default `gpt-5.6-terra`) |
| Storage | None. Requests are stateless and nothing is persisted |
| Fonts | IBM Plex Sans, JetBrains Mono |

---

## Project Structure

```
writewise/
├── api/
│   ├── index.py           # Vercel entrypoint; re-exports the FastAPI app from backend/server.py
│   └── requirements.txt   # Runtime Python dependencies (used by Vercel and by backend/requirements.txt)
├── backend/
│   ├── server.py          # FastAPI app, all 10 writing modes, prompt construction, OpenAI call
│   ├── requirements.txt   # Runtime deps (via api/requirements.txt) + uvicorn and test tools
│   ├── .env.example       # Template for backend/.env
│   └── .env               # OPENAI_API_KEY, OPENAI_MODEL, CORS_ORIGINS (not committed)
│
├── frontend/
│   ├── src/
│   │   ├── App.js                        # Main app, state, mode logic
│   │   ├── App.css                       # All styles (dark theme)
│   │   └── components/
│   │       ├── QuickTemplates.jsx        # 4 quick-start template chips
│   │       ├── PersonalizationPanel.jsx  # Collapsible experience/role/skills inputs
│   │       ├── TabOptions.jsx            # Mode-specific sub-options (pills)
│   │       └── OutputSection.jsx         # Output cards, scores, why-good-fit
│   ├── public/
│   │   └── images/bg-texture.png         # Background texture
│   ├── package.json
│   ├── package-lock.json
│   ├── .env.example       # Template for frontend/.env
│   └── .env               # REACT_APP_BACKEND_URL (not committed)
│
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js 20.x (tested with 20.19.4) and npm 10.x (tested with 10.8.2)
- Python 3.10+ (tested with 3.12)
- An OpenAI API key

No database is required.

### 1. Clone the repository

```bash
git clone https://github.com/tymepas/WriteWise_Project.git
cd WriteWise_Project
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env` and fill in your key:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.6-terra
CORS_ORIGINS=http://localhost:3000
```

Start the backend (from the `backend` directory):

```bash
uvicorn server:app --host 127.0.0.1 --port 8001 --reload
```

Check it is running: `http://localhost:8001/api/` should return `{"message": "WriteWise API"}`.

### 3. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
```

Copy `frontend/.env.example` to `frontend/.env`:

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

Start the development server:

```bash
npm start
```

The app will be available at `http://localhost:3000`.

To create a production build in `frontend/build/`:

```bash
npm run build
```

`REACT_APP_BACKEND_URL` is baked into the bundle at build time. When it is not set, the frontend calls the API on its own origin (`/api/...`), which is how the Vercel deployment works.

---

## Deploying to Vercel

WriteWise deploys as a single Vercel project: the React build is served as static files and the FastAPI app runs as a Python function on the same domain.

```
/          → frontend/build (static React app)
/api/*     → api/index.py → FastAPI app from backend/server.py
```

1. Import the GitHub repository into Vercel and keep the **Root Directory** as the repository root. `vercel.json` sets the install command, build command, output directory and the `/api/*` rewrite, so no build settings need to be changed in the dashboard.
2. Add these **Environment Variables** in the Vercel project settings:
   - `OPENAI_API_KEY`: your OpenAI key (mark it as sensitive)
   - `OPENAI_MODEL`: `gpt-5.6-terra`
   - `CORS_ORIGINS`: your deployment URL, e.g. `https://writewise.vercel.app` (the app itself is same-origin and does not need CORS; this only limits other websites)
3. Do **not** set `REACT_APP_BACKEND_URL` on Vercel, so the frontend calls `/api` on the same domain.
4. Deploy.

The Python runtime version is pinned by `api/.python-version` (3.12), and the Python function installs only `api/requirements.txt`.

---

## API Reference

### `POST /api/generate`

Generate writing output based on the selected mode.

**Request body:**

```json
{
  "mode": "email",
  "input": "Software Engineer role at TechCorp. Need 3 years React experience.",
  "context": "Friendly and direct tone",
  "experience": "4 years React developer",
  "target_role": "Frontend Engineer",
  "skills": "React, TypeScript, Node.js",
  "variations": false,
  "paraphrase_mode": "standard",
  "summary_type": "short"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | string | Yes | One of: `auto`, `grammar`, `email`, `tone`, `rewrite`, `paraphrase`, `summarize`, `expand`, `shorten`, `humanize` |
| `input` | string | Yes | The text to process |
| `context` | string | No | Extra instructions (e.g. "Keep it concise for a client email") |
| `experience` | string | No | User's work experience (for personalization) |
| `target_role` | string | No | Job role being targeted |
| `skills` | string | No | Comma-separated skills |
| `variations` | boolean | No | If true, returns 3 variations instead of 1 |
| `paraphrase_mode` | string | No | `standard`, `fluency`, `formal`, `simple`, `creative` |
| `summary_type` | string | No | `short` or `bullets` |
| `tone` | string | No | Tone mode only: `professional`, `casual`, `friendly`, `diplomatic`, `formal`, `confident`, `persuasive`, `empathetic`. If omitted, the tone is taken from `context` (default `professional`) |
| `rewrite_goal` | string | No | Rewrite mode only: `clear_concise`, `more_direct`, `more_polished`, `more_persuasive`, `simplify`, `keep_style`. If omitted, the default rewrite is used |

**Response:**

```json
{
  "output": "Subject: Frontend Engineer Application...",
  "variations": null,
  "mode": "email",
  "detected_mode": null,
  "why_good_fit": [
    "4 years of React experience directly matches the job requirement",
    "TypeScript proficiency aligns with their modern frontend stack"
  ],
  "evaluation": {
    "clarity": 9,
    "professionalism": 9,
    "personalization": 8,
    "suggestion": "Consider adding a specific project or achievement to stand out."
  }
}
```

### `GET /api/`

Health check. Returns `{ "message": "WriteWise API" }`.

---

## Environment Variables

### Backend (`/backend/.env`)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key. Required. Used only by the backend and never sent to the browser |
| `OPENAI_MODEL` | OpenAI model to use. Optional, defaults to `gpt-5.6-terra` |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated), e.g. `http://localhost:3000` |

### Frontend (`/frontend/.env`)

| Variable | Description |
|----------|-------------|
| `REACT_APP_BACKEND_URL` | Backend API base URL, e.g. `http://localhost:8001`. Do not put any API keys in the frontend `.env`: everything in it is visible in the browser |

`.env` files are git-ignored; only the `.env.example` templates are committed.

---

## Provider Migration Note

WriteWise was originally generated on the Emergent platform, where the backend called Anthropic's `claude-sonnet-4-5-20250929` through Emergent's `emergentintegrations` wrapper and logged request metadata to MongoDB. The standalone version calls OpenAI directly with the official SDK, keeps the same prompts, request/response shape and output parsing, and stores nothing. The backend asks OpenAI for JSON-mode output so the model's response always parses into the structure the frontend expects. Output wording may differ from the original model.

---

## Writing Mode Details

### Auto Mode
Detects the best mode automatically from your input. Supports detection of: grammar errors, email intent, tone requests, paraphrase needs, summarization, and humanization.

### Email Mode
If input is a job posting, generates a personalized job application email. If input is rough text, polishes it into a professional email. Always includes a subject line. Uses your experience, target role, and skills for personalization.

### Paraphrase Styles
- **Standard** — Natural rewrite with varied wording
- **Fluency** — Smooth, easy-to-read version
- **Formal** — Professional and academic register
- **Simple** — Plain language, shorter sentences
- **Creative** — Inventive rewriting with fresh phrasing

### Summarize Formats
- **Short Summary** — 2 to 3 sentence overview
- **Bullet Points** — 4 to 6 key points

---

## Design

- Dark theme (`#09090B` background)
- IBM Plex Sans for body text
- JetBrains Mono for labels, badges, and code-style UI
- Scrollable tab row for all 9 modes
- Minimal, distraction-free single-page layout
- Fade-in animations on output render
- Animated score bars on evaluation display

---

## Roadmap

- [ ] Generation history with saved sessions
- [ ] Word and character count on the textarea
- [ ] Download output as `.txt`
- [ ] LinkedIn message quick template
- [ ] Thank-you note template
- [ ] Export as `.docx`
- [ ] Share output via link

---

## License

MIT
