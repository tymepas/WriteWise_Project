"""Golden cases for Prompt mode, shared by the mocked tests and the live tests.

All examples are fictional. Each case lists semantic properties the refined message must have,
as case-insensitive regular expressions, instead of an exact expected string:

- must:        every pattern must match (facts, requests, constraints, exclusions, terms)
- must_not:    no pattern may match (invented content, abandoned instructions, doing the task)
- order:       patterns whose first matches must appear in this order (requested sequence, chronology)
- urls:        URLs that must appear byte for byte
- exact:       text that must appear exactly, case-sensitive (technical tokens kept as typed, or brand names
               after normal proofreading)
- max_ratio:   output length / input length, so refined messages do not grow into prompt templates
- max_chars:   absolute length limit for very short requests
- one_paragraph: True when a simple request must stay a single paragraph
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Case:
    id: str
    kind: str
    input: str
    must: List[str] = field(default_factory=list)
    must_not: List[str] = field(default_factory=list)
    order: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    exact: List[str] = field(default_factory=list)
    max_ratio: float = 1.35
    max_chars: Optional[int] = None
    one_paragraph: bool = False


CASES = [
    Case(
        "python_performance", "short-medium, technical, already tried",
        "hey i have a python script which works fine when i test it with a csv around 5000 rows but when i use "
        "around 500000 rows it becomes really slow and sometimes memory usage goes very high i already tried "
        "removing some columns but it didnt make much difference please explain what could be causing this and "
        "what should i check first",
        must=[r"python", r"csv", r"5,?000\b", r"500,?000", r"slow", r"memory", r"columns",
              r"tried", r"caus", r"check\w*\b.{0,15}first|first.{0,30}check"],
    ),
    Case(
        "data_merge", "short, technical, uncertainty",
        "i merged two datasets in pandas and before merge there were 120k rows and after merge there are 210k so "
        "i think duplicates are getting created can you explain why this happens and how i can find which records "
        "are causing it",
        must=[r"pandas", r"120(,000|k)", r"210(,000|k)", r"duplicat", r"\bthink\b|suspect|may be|might be|seems",
              r"why", r"(identify|find|which).{0,40}(records|rows)"],
        exact=["pandas"],
    ),
    Case(
        "power_bi_dashboard", "medium, business, constraints",
        "i am making a power bi dashboard for sales performance and right now i have revenue orders average order "
        "value and customer count i also have region product category and month filters but the dashboard looks "
        "too crowded and i dont know what should be on first page and what can move to second page please suggest "
        "a good layout but keep it for management users who want quick insights",
        must=[r"power bi", r"sales", r"revenue", r"orders", r"average order value", r"customer count", r"region",
              r"product category", r"month", r"crowded|cluttered", r"first page", r"second page", r"layout",
              r"management", r"quick"],
    ),
    Case(
        "job_application", "medium, business, multi-request",
        "i found a job which is asking for 3 to 6 years and i have 5 years but most of my experience is project "
        "management in market research and the role says business analyst plus some sql power bi and stakeholder "
        "management i know sql and power bi but i havent worked in a formal BA title please check the JD and my "
        "resume and tell me how strong the match is and which gaps i should be ready to explain",
        must=[r"3 ?(to|-|–) ?6|three to six", r"\b5 years|five years", r"project management", r"market research",
              r"business analyst|\bBA\b", r"sql", r"power bi", r"stakeholder", r"title",
              r"job description|\bJD\b", r"resume", r"match", r"gaps?"],
    ),
    Case(
        "resume_review", "short, already fairly clear, constraint",
        "check this resume for the job and tell me if there are any bullets which look too exaggerated i dont want "
        "to remove strong points but i also dont want to claim something which i cannot explain in interview",
        must=[r"resume", r"bullet", r"exaggerat|overstat|inflat", r"strong points", r"interview",
              r"(cannot|can't|unable to|not able to|couldn't).{0,20}(explain|defend|back up|justify)"],
        max_ratio=1.3,
    ),
    Case(
        "sql_query", "short, technical, constraint",
        "this query is giving the right result but it is taking almost 2 minutes even on a small table please "
        "explain what part is probably making it slow and show me how i can improve it without changing the result",
        must=[r"query", r"right|correct", r"(2|two) minutes", r"small table", r"slow|bottleneck",
              r"improve|optimi[sz]e|speed", r"without changing"],
        max_ratio=1.4,
    ),
    Case(
        "learning_plan", "medium, conversational, exclusion, knowledge level",
        "i know python sql and power bi at a basic to intermediate level and now i want to move towards genai "
        "applications i dont want a roadmap that is just theory i want something where i build small projects "
        "step by step and each project should teach me something useful like APIs RAG agents evaluation and "
        "deployment please create a practical learning path",
        must=[r"python", r"sql", r"power bi", r"basic", r"intermediate", r"genai|generative ai",
              r"theory", r"projects?", r"\bapis?\b", r"\brag\b", r"agents", r"evaluation", r"deployment",
              r"learning path"],
    ),
    Case(
        "course_comparison", "medium, conversational, exclusion",
        "i am confused between two courses one is mostly data science and machine learning and the other one is "
        "more about building AI applications with APIs agents and deployment i already know basic analytics and i "
        "want to move towards AI product or AI solution roles so dont just tell me which course is more popular "
        "compare them based on what i already know and where i want to go",
        must=[r"two courses", r"data science", r"machine learning", r"ai applications", r"\bapis?\b", r"agents",
              r"deployment", r"basic analytics|analytics", r"ai product", r"ai solution", r"popular", r"compar"],
    ),
    Case(
        "api_debugging", "medium, technical, already tried",
        "my application calls an external api and works from postman but when i call the same endpoint from my "
        "next js backend i get a 401 and sometimes 403 i have already checked that the url is correct so please "
        "help me figure out what else could be different between postman and my backend request and what logs or "
        "headers i should inspect",
        must=[r"external api|\bapi\b", r"postman", r"next\.?\s?js", r"401", r"403", r"already", r"url",
              r"differ", r"headers", r"logs"],
    ),
    Case(
        "meeting_followup", "medium, business, multi-request, exclusion, chronology",
        "i had a meeting with the team today and we discussed three things first the dashboard should launch next "
        "monday second we are not adding the export to excel feature in this release and third priyam will send "
        "the final data mapping by friday i wrote some notes but they are messy please turn them into a clean "
        "follow up message without changing the decisions",
        must=[r"meeting|met with", r"today", r"dashboard", r"monday", r"excel",
              r"(not|n't|no longer|exclud).{0,60}excel|excel.{0,80}(not|n't|exclud)",
              r"release", r"priyam", r"data mapping", r"friday", r"follow.?up", r"without changing"],
        order=[r"monday", r"excel", r"priyam"],
    ),
    Case(
        "laptop_research", "long, conversational, constraints, exclusions",
        "i am thinking about buying a laptop mainly for python development power bi sql and some local AI "
        "experiments i dont need gaming performance and i dont care much about how thin it is battery is useful "
        "but not the main thing i mostly use it at home and sometimes carry it to office my budget is around 90000 "
        "and i would prefer 16 gb minimum but if 32 gb is available in that range then better please compare some "
        "options and explain which one makes most sense for this use case",
        must=[r"laptop", r"python", r"power bi", r"sql", r"local ai", r"gaming", r"thin|portab|slim",
              r"battery", r"home", r"office", r"90,?000", r"16 ?gb", r"32 ?gb", r"compar",
              r"most sense|best (fit|suits)|which one"],
        must_not=[r"\$\s?90", r"90,?000 (usd|dollars)"],
        max_ratio=1.15,
    ),
    Case(
        "document_analysis", "long, business, multi-request, exclusion",
        "i have a policy document and a separate process document and i want to understand whether the actual "
        "process is following the policy there are probably some sections where the policy says one thing and the "
        "process document says something slightly different i want you to compare them section by section and "
        "identify the mismatches but dont assume that one is wrong just because they are different also if "
        "something is missing from one document please mention that separately",
        must=[r"policy", r"process", r"section", r"mismatch|differen", r"missing",
              r"(not|n't|without) assum", r"separate"],
        max_ratio=1.2,
    ),
    Case(
        "cloud_self_correction", "short, self-correction, order",
        "tell me which cloud is best for this project no actually first compare aws and azure for cost and then "
        "tell me which one you would pick for my situation",
        must=[r"\baws\b", r"azure", r"cost", r"pick|choose|recommend|select"],
        must_not=[r"which cloud is (the )?best", r"no actually"],
        order=[r"compar", r"pick|choose|recommend|select"],
        max_ratio=1.3,
    ),
    Case(
        "elastic_exclusion", "short, technical, decision, exclusion, scope",
        "we tested elastic for this prototype but we are not moving it to production right now so dont include "
        "production deployment recommendations yet just help me improve the search relevance",
        must=[r"\belastic\b", r"prototype", r"(not|n't).{0,40}production",
              r"(not|n't|without|exclud|avoid|skip).{0,40}(production )?deployment",
              r"search relevance|relevance"],
    ),
    Case(
        "rag_multi_question", "medium, technical, multi-request, numbers",
        "i built a small rag app and it can answer some questions correctly but for a few questions it gives "
        "answers which are not actually present in the documents i am using chunk size is 500 and top k is 3 right "
        "now i want to understand whether the problem is retrieval or generation and what experiments i should run "
        "before changing everything",
        must=[r"\brag\b", r"correct", r"(not|n't).{0,30}(present|in|found|contained|supported)|hallucinat",
              r"chunk size", r"\b500\b", r"top.?k", r"\b3\b|three", r"retrieval", r"generation",
              r"experiment", r"before"],
    ),
    Case(
        "very_simple", "very short, already clear",
        "make this email sound professional but not too formal",
        must=[r"email", r"professional", r"formal"],
        max_ratio=1.6, max_chars=90, one_paragraph=True,
    ),
    # Fictional cases for links, the instruction/content split, not doing the task, and corrections.
    Case(
        "docs_links", "short, links, constraint",
        "can you compare these two setup guides https://docs.example.com/v2/setup?lang=en#install and "
        "https://help.example.org/start/guide?ref=nav&utm_source=chat and tell me which one explains "
        "authentication more clearly, i only care about the auth part",
        must=[r"compar", r"guide", r"auth", r"only|just|focus"],
        urls=["https://docs.example.com/v2/setup?lang=en#install",
              "https://help.example.org/start/guide?ref=nav&utm_source=chat"],
        max_ratio=1.3,
    ),
    Case(
        "website_trust", "very short, link, do not perform",
        "Please review this website https://shop.example.net/about-us?id=42&src=ad and tell me whether it is "
        "trustworthy.",
        must=[r"website|site", r"trustworth"],
        must_not=[r"^\s*(yes|no)\b", r"\b(appears|seems|looks) (to be )?(legitimate|trustworthy|safe|reliable)"],
        urls=["https://shop.example.net/about-us?id=42&src=ad"],
        max_chars=160, one_paragraph=True,
    ),
    Case(
        "spreadsheet_task", "very short, already clear, do not perform",
        "Please analyze this spreadsheet and tell me which region is performing best.",
        must=[r"spreadsheet", r"region", r"best|top|strongest"],
        must_not=[r"\b(north|south|east|west|central)\b", r"\bis performing best\b(?!\.?$)"],
        max_chars=120, one_paragraph=True,
    ),
    Case(
        "manager_message", "short, instruction and content, two layers",
        "pls write a short message to my manager neha saying the client report will be ready on thursday instead "
        "of tuesday because the vendor data came late and ask if thursday morning is ok for her review",
        must=[r"write", r"message", r"short|brief", r"neha", r"client report", r"thursday", r"tuesday",
              r"vendor", r"review"],
        # The output is the request for the message, not the message itself.
        must_not=[r"^\s*(hi|hello|dear)\b", r"regards"],
    ),
    Case(
        "release_correction", "very short, self-correction",
        "draft a checklist for the release on friday, no sorry i mean tuesday, mainly testing and docs",
        must=[r"checklist", r"release", r"tuesday", r"testing", r"doc"],
        must_not=[r"friday", r"no sorry"],
        max_ratio=1.4, one_paragraph=True,
    ),
    # Sentence type: "right now" starts a statement; it is not a "right?" tag on the sentence before.
    Case(
        "right_now_statement", "medium, technical, statements stay statements",
        "the staging server is already on node 18 and that is a different setup, right now i want to upgrade "
        "only the worker service to node 20 so the main app is not affected. what should i check before i do it",
        must=[r"staging", r"node 18", r"different", r"worker service", r"node 20", r"main app", r"check"],
        must_not=[r"right\?", r"correct\?", r"isn'?t it\?", r"\bI (believe|think|assume|guess)\b",
                  r"\b(is|does) (the )?staging server\b"],
    ),
    Case(
        "genuine_right_question", "short, a real question stays a question",
        "the free plan only allows 3 projects, right? if yes i want to know whether archived projects also count "
        "toward that limit",
        must=[r"free plan", r"(3|three) projects", r"archived", r"limit"],
        # The user is unsure about the limit, so it must still be asked, not stated as fact.
        must_not=[r"^\s*the free plan only allows (3|three) projects\.", r"since the free plan only allows"],
        order=[r"(3|three) projects[^.!]*\?", r"archived"],
    ),
    # Technically significant tokens are copied exactly: no expansion or re-casing.
    Case(
        "technical_wording", "medium, technical, abbreviations, commands, identifiers",
        "our k8s pods restart every few hours and the gh actions deploy job also fails sometimes. i already ran "
        "kubectl rollout restart deploy/api-gateway and set MAX_RETRIES=5 in config.yaml but nothing changed. "
        "can you explain what could cause both",
        must=[r"pods", r"restart", r"deploy job", r"already", r"nothing changed|did not change|no change|didn't"],
        must_not=[r"kubernetes", r"github actions"],
        exact=["k8s", "gh actions", "kubectl rollout restart deploy/api-gateway", "MAX_RETRIES=5", "config.yaml"],
    ),
    # Brand names get normal proofreading: misspelling and capitalization are corrected.
    Case(
        "brand_names_proofread", "short, brand names corrected",
        "i deploy my side project on vercel and use claude code with my antropic account. how can i see how much "
        "of my monthly usage is left",
        must=[r"side project", r"monthly usage", r"left|remaining"],
        must_not=[r"\bantropic\b"],
        exact=["Vercel", "Claude Code", "Anthropic"],
    ),
    # Both sides at once: brand names may be proofread, technical tokens stay exact even right next to them.
    Case(
        "brand_names_with_exact_tokens", "medium, technical, brand names and exact tokens together",
        "my team uses claude code for local testing and the app is deployed on vercel. i want the local setup to use "
        "my own antropic key instead of the shared one. should ANTHROPIC_API_KEY go in .env.local or in "
        "backend/.env, and does vercel read either of those files",
        # Correcting "antropic" is allowed but not required here; it must never be renamed or expanded.
        must=[r"local", r"shared", r"own", r"read", r"\b(anthropic|antropic)\b"],
        exact=["Claude Code", "Vercel", "ANTHROPIC_API_KEY", ".env.local", "backend/.env"],
    ),
]

CASES_BY_ID = {case.id: case for case in CASES}
