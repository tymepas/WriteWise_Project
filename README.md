# WriteWise

**WriteWise** is an AI-powered writing platform built for job seekers and professionals. It combines general writing tools (like QuillBot) with job-focused intelligence, powered by Claude Sonnet 4.5.

Fix grammar, rewrite content, generate emails, paraphrase text, summarize documents, and more — all in one place.

---

## Features

### 9 Writing Modes

| Mode | What it does |
|------|-------------|
| **Auto** | AI detects your intent and acts on it automatically |
| **Grammar** | Fixes grammar and spelling without changing your voice |
| **Email** | Drafts professional emails and personalized job application emails |
| **Tone** | Rewrites text in a specified tone (formal, friendly, confident, polite) |
| **Rewrite** | Improves clarity, flow, and impact |
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
| Frontend | React 19, Tailwind CSS, Shadcn UI, Lucide React |
| Backend | FastAPI, Python |
| Database | MongoDB (Motor async driver) |
| AI | Claude Sonnet 4.5 via `emergentintegrations` |
| Fonts | IBM Plex Sans, JetBrains Mono |

---

## Project Structure

```
writewise/
├── backend/
│   ├── server.py          # FastAPI app, all 10 writing modes, prompt construction
│   ├── requirements.txt
│   └── .env               # MONGO_URL, DB_NAME, EMERGENT_LLM_KEY
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
│   ├── package.json
│   └── .env               # REACT_APP_BACKEND_URL
│
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB (local or Atlas)
- Emergent Universal LLM Key (for Claude Sonnet 4.5)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/writewise.git
cd writewise
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `/backend`:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=writewise
EMERGENT_LLM_KEY=your_emergent_llm_key_here
CORS_ORIGINS=http://localhost:3000
```

Start the backend:

```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend setup

```bash
cd frontend
yarn install
```

Create a `.env` file in `/frontend`:

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

Start the frontend:

```bash
yarn start
```

The app will be available at `http://localhost:3000`.

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
| `context` | string | No | Extra instructions or tone guidance |
| `experience` | string | No | User's work experience (for personalization) |
| `target_role` | string | No | Job role being targeted |
| `skills` | string | No | Comma-separated skills |
| `variations` | boolean | No | If true, returns 3 variations instead of 1 |
| `paraphrase_mode` | string | No | `standard`, `fluency`, `formal`, `simple`, `creative` |
| `summary_type` | string | No | `short` or `bullets` |

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
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | MongoDB database name |
| `EMERGENT_LLM_KEY` | Emergent Universal LLM Key for Claude Sonnet 4.5 |
| `CORS_ORIGINS` | Allowed origins (comma-separated) |

### Frontend (`/frontend/.env`)

| Variable | Description |
|----------|-------------|
| `REACT_APP_BACKEND_URL` | Backend API base URL |

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
