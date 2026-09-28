import { useEffect, useRef, useState } from "react";
import "@/App.css";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Wand2, Loader2, ArrowDown, Sparkles, X } from "lucide-react";
import axios from "axios";
import QuickTemplates from "@/components/QuickTemplates";
import PersonalizationPanel from "@/components/PersonalizationPanel";
import OutputSection from "@/components/OutputSection";
import TabOptions from "@/components/TabOptions";
import WritewiseLogo from "@/components/WritewiseLogo";
import LoadingCard from "@/components/LoadingCard";

// Empty in production so requests go to the same origin (/api on Vercel).
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
const API = `${BACKEND_URL}/api`;

const MODES = [
  { id: "auto",          label: "Auto",             badge: "Recommended", description: "AI detects what you need and acts on it" },
  { id: "grammar",       label: "Grammar",           description: "Fix grammar and spelling without changing your voice" },
  { id: "email",         label: "Email",             description: "Draft a professional email or job application" },
  { id: "tone",          label: "Tone",              description: "Rewrite in a specific tone" },
  { id: "rewrite",       label: "Rewrite",           description: "Improve clarity, flow, and impact" },
  { id: "paraphrase",    label: "Paraphrase",        description: "Same meaning, different words and structure" },
  { id: "summarize",     label: "Summarize",         description: "Extract the key points in a concise format" },
  { id: "expand_shorten",label: "Expand / Shorten",  description: "Add depth or trim it down to what matters" },
  { id: "humanize",      label: "Humanize",          description: "Remove AI-like phrasing. Make it sound naturally written" },
];

const PLACEHOLDERS = {
  auto:           "Paste a job post, draft email, or rough text to get started...",
  grammar:        "Paste your text here to fix grammar and spelling...",
  email:          "Paste a job posting or describe the email you need...",
  tone:           "Paste the text you want to rewrite in a different tone...",
  rewrite:        "Paste your text here to improve clarity and flow...",
  paraphrase:     "Paste the text you want to paraphrase...",
  summarize:      "Paste the article, report, or document you want summarized...",
  expand_shorten: "Paste the text you want to expand or shorten...",
  humanize:       "Paste AI-generated or overly formal text to make it sound human...",
};

const CONTEXT_PLACEHOLDERS = {
  auto:           "e.g. Make it more confident, applying for a startup role...",
  grammar:        "e.g. Keep British English spelling...",
  email:          "e.g. Friendly and direct, startup culture...",
  tone:           "e.g. Keep it concise and suitable for a client-facing email...",
  rewrite:        "e.g. Make it punchier, cut anything vague...",
  paraphrase:     "e.g. Keep it under 100 words, avoid jargon...",
  summarize:      "e.g. Focus on the key statistics, skip the examples...",
  expand_shorten: "e.g. Add more context to the second paragraph...",
  humanize:       "e.g. Keep it conversational, target a general audience...",
};

const LOADING_MSGS = {
  auto:           "Analyzing...",
  grammar:        "Fixing grammar...",
  email:          "Drafting email...",
  tone:           "Adjusting tone...",
  rewrite:        "Rewriting...",
  paraphrase:     "Paraphrasing...",
  summarize:      "Summarizing...",
  humanize:       "Humanizing...",
};

const DEFAULT_OPTIONS = {
  paraphraseMode: "standard",
  summaryType: "short",
  expandShortenMode: "shorten",
  tone: "professional",
  rewriteGoal: null,
};

// Personalization is kept in this browser only (no accounts or database).
const PROFILE_STORAGE_KEY = "writewise.profile";

function loadProfile() {
  try {
    const saved = JSON.parse(window.localStorage.getItem(PROFILE_STORAGE_KEY) || "{}");
    const text = (value) => (typeof value === "string" ? value : "");
    return { experience: text(saved.experience), targetRole: text(saved.targetRole), skills: text(saved.skills) };
  } catch {
    return { experience: "", targetRole: "", skills: "" };
  }
}

function saveProfile(profile) {
  try {
    if (profile.experience || profile.targetRole || profile.skills) {
      window.localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
    } else {
      window.localStorage.removeItem(PROFILE_STORAGE_KEY);
    }
  } catch {
    // Storage can be unavailable (private mode, blocked site data); the app still works.
  }
}

const SHOW_VARIATIONS = ["auto", "email", "rewrite", "tone", "paraphrase"];
const SHOW_PERSONALIZATION = ["auto", "email", "rewrite", "tone", "humanize"];

const EXAMPLE_TEXT = `Senior Product Designer at DesignCo

We're looking for a Senior Product Designer to join our team. Requirements:
- 4+ years of UX/UI design experience
- Strong proficiency in Figma and design systems
- Experience working closely with engineering and product teams
- Good communication skills and ability to handle feedback

We offer remote work, competitive salary, and equity. Fast-growing team of 40 people building tools used by 50,000+ designers.`;

function getLoadingMsg(mode, expandShortenMode) {
  if (mode === "expand_shorten") {
    return expandShortenMode === "expand" ? "Expanding..." : "Shortening...";
  }
  return LOADING_MSGS[mode] || "Generating...";
}

function getButtonLabel(mode, expandShortenMode) {
  if (mode === "expand_shorten") {
    return expandShortenMode === "expand" ? "Expand" : "Shorten";
  }
  return "Generate";
}

export default function App() {
  const [mode, setMode] = useState("auto");
  const [input, setInput] = useState("");
  const [context, setContext] = useState("");
  const [experience, setExperience] = useState(() => loadProfile().experience);
  const [targetRole, setTargetRole] = useState(() => loadProfile().targetRole);
  const [skills, setSkills] = useState(() => loadProfile().skills);

  useEffect(() => {
    saveProfile({ experience, targetRole, skills });
  }, [experience, targetRole, skills]);
  const [variationsEnabled, setVariationsEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Tab sub-options
  const [paraphraseMode, setParaphraseMode] = useState(DEFAULT_OPTIONS.paraphraseMode);
  const [summaryType, setSummaryType] = useState(DEFAULT_OPTIONS.summaryType);
  const [expandShortenMode, setExpandShortenMode] = useState(DEFAULT_OPTIONS.expandShortenMode);
  const [tone, setTone] = useState(DEFAULT_OPTIONS.tone);
  const [rewriteGoal, setRewriteGoal] = useState(DEFAULT_OPTIONS.rewriteGoal);

  // Incremented whenever the current result is discarded, so a response
  // from an older request can't appear under a different feature.
  const requestIdRef = useRef(0);

  const currentMode = MODES.find((m) => m.id === mode);

  const discardResult = () => {
    requestIdRef.current += 1;
    setLoading(false);
    setResult(null);
  };

  const resetOptions = () => {
    setParaphraseMode(DEFAULT_OPTIONS.paraphraseMode);
    setSummaryType(DEFAULT_OPTIONS.summaryType);
    setExpandShortenMode(DEFAULT_OPTIONS.expandShortenMode);
    setTone(DEFAULT_OPTIONS.tone);
    setRewriteGoal(DEFAULT_OPTIONS.rewriteGoal);
  };

  // Switching features keeps the input text but drops the previous result.
  const handleModeChange = (newMode) => {
    setMode(newMode);
    discardResult();
  };

  const handleClear = () => {
    const snapshot = {
      mode, input, context, result,
      options: { paraphraseMode, summaryType, expandShortenMode, tone, rewriteGoal },
    };
    setInput("");
    setContext("");
    discardResult();
    resetOptions();
    if (snapshot.input.trim()) {
      toast("Text cleared", {
        action: {
          label: "Undo",
          onClick: () => {
            discardResult();
            setMode(snapshot.mode);
            setInput(snapshot.input);
            setContext(snapshot.context);
            setResult(snapshot.result);
            setParaphraseMode(snapshot.options.paraphraseMode);
            setSummaryType(snapshot.options.summaryType);
            setExpandShortenMode(snapshot.options.expandShortenMode);
            setTone(snapshot.options.tone);
            setRewriteGoal(snapshot.options.rewriteGoal);
          },
        },
      });
    }
    document.getElementById("main-input")?.focus();
  };

  const handleTemplateSelect = (template) => {
    setInput(template.text);
    setMode(template.mode);
    discardResult();
    setTimeout(() => window.scrollTo({ top: 300, behavior: "smooth" }), 50);
  };

  const buildPayload = () => {
    const actualMode = mode === "expand_shorten" ? expandShortenMode : mode;
    return {
      mode: actualMode,
      input: input.trim(),
      context: context.trim() || null,
      experience: experience.trim() || null,
      target_role: targetRole.trim() || null,
      skills: skills.trim() || null,
      variations: SHOW_VARIATIONS.includes(mode) ? variationsEnabled : false,
      paraphrase_mode: mode === "paraphrase" ? paraphraseMode : null,
      summary_type: mode === "summarize" ? summaryType : null,
      tone: mode === "tone" ? tone : null,
      rewrite_goal: mode === "rewrite" ? rewriteGoal : null,
    };
  };

  const runGenerate = async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setResult(null);
    try {
      const { data } = await axios.post(`${API}/generate`, buildPayload());
      if (requestId === requestIdRef.current) setResult(data);
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      // Only show server messages that are plain text (not HTML error pages or objects).
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string" && detail) {
        toast.error(detail);
      } else if (err?.response?.status === 429) {
        // Rate limited before reaching the API (e.g. by the Vercel Firewall).
        toast.error("Too many requests. Please wait a minute and try again.");
      } else {
        toast.error("Something went wrong. Please try again.");
      }
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!input.trim()) {
      toast.error("Please enter some text first.");
      return;
    }
    await runGenerate();
  };

  const handleStartWriting = () => {
    document.getElementById("main-input")?.focus();
    document.getElementById("main-input")?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  const handleTryExample = () => {
    setInput(EXAMPLE_TEXT);
    setMode("email");
    discardResult();
    setTimeout(() => {
      document.getElementById("main-input")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 80);
  };

  const btnLabel = getButtonLabel(mode, expandShortenMode);
  const loadingMsg = getLoadingMsg(mode, expandShortenMode);

  return (
    <div className="app-root">
      <div
        className="bg-texture"
        aria-hidden="true"
        style={{ backgroundImage: `url(${process.env.PUBLIC_URL}/images/bg-texture.png)` }}
      />

      <main className="container">
        {/* Header */}
        <header className="header">
          <div className="header-logo-row">
            <WritewiseLogo iconSize={26} />
          </div>

          <h1 className="heading-1">
            Write better.<br />Get noticed.
          </h1>

          <p className="subheading">
            From fixing grammar to crafting job-winning emails, everything you need to write with confidence.
          </p>

          <div className="hero-cta-row">
            <button
              className="hero-cta-primary"
              onClick={handleStartWriting}
              data-testid="cta-start-writing"
            >
              <Sparkles size={14} strokeWidth={1.5} />
              Start Writing Smarter
            </button>
            <button
              className="hero-cta-secondary"
              onClick={handleTryExample}
              data-testid="cta-try-example"
            >
              Try with Example
              <ArrowDown size={13} strokeWidth={1.5} />
            </button>
          </div>

          <p className="hero-helper-text">
            Paste your text or job post to begin
          </p>
        </header>

        {/* Quick Templates */}
        <QuickTemplates onSelect={handleTemplateSelect} />

        {/* Mode Tabs */}
        <Tabs value={mode} onValueChange={handleModeChange} className="modes-tabs">
          <TabsList className="modes-list" data-testid="mode-tabs">
            {MODES.map((m) => (
              <TabsTrigger
                key={m.id}
                value={m.id}
                className={`mode-trigger${m.id === "auto" ? " mode-trigger-auto" : ""}`}
                data-testid={`mode-tab-${m.id}`}
              >
                {m.label}
                {m.badge && <span className="tab-badge">{m.badge}</span>}
              </TabsTrigger>
            ))}
          </TabsList>
          <p className="mode-description">{currentMode.description}</p>
        </Tabs>

        {/* Tab-specific sub-options */}
        <TabOptions
          mode={mode}
          paraphraseMode={paraphraseMode}
          onParaphraseMode={setParaphraseMode}
          summaryType={summaryType}
          onSummaryType={setSummaryType}
          expandShortenMode={expandShortenMode}
          onExpandShortenMode={setExpandShortenMode}
          tone={tone}
          onTone={setTone}
          rewriteGoal={rewriteGoal}
          onRewriteGoal={setRewriteGoal}
          disabled={loading}
        />

        {/* Input Section */}
        <section className="input-section">
          <div className="input-label-row">
            <div className="input-label">Your text</div>
            <button
              type="button"
              className="input-clear-btn"
              onClick={handleClear}
              disabled={!input && !context && !result && !loading}
              data-testid="clear-input-btn"
              title="Clear the text and start over"
            >
              <X size={11} strokeWidth={1.5} />
              Clear
            </button>
          </div>
          <Textarea
            id="main-input"
            data-testid="main-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={PLACEHOLDERS[mode]}
            className="main-textarea"
            disabled={loading}
          />

          {/* Personalization Panel */}
          {SHOW_PERSONALIZATION.includes(mode) && (
            <PersonalizationPanel
              experience={experience}
              targetRole={targetRole}
              skills={skills}
              onExperienceChange={setExperience}
              onTargetRoleChange={setTargetRole}
              onSkillsChange={setSkills}
              recommended={mode === "email"}
              disabled={loading}
            />
          )}

          {/* Context */}
          <div>
            <div className="input-label">Additional context (optional)</div>
            <Input
              data-testid="context-input"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder={CONTEXT_PLACEHOLDERS[mode]}
              className="context-input"
              disabled={loading}
            />
          </div>

          {/* Controls Row */}
          <div className="controls-row">
            <Button
              data-testid="generate-btn"
              onClick={handleGenerate}
              disabled={loading}
              className="generate-btn"
            >
              {loading ? (
                <>
                  <Loader2 size={15} className="spin" strokeWidth={1.5} />
                  {loadingMsg}
                </>
              ) : (
                <>
                  <Wand2 size={15} strokeWidth={1.5} />
                  {btnLabel}
                </>
              )}
            </Button>

            {SHOW_VARIATIONS.includes(mode) && (
              <div className="variations-toggle" data-testid="variations-toggle-row">
                <Switch
                  data-testid="variations-switch"
                  checked={variationsEnabled}
                  onCheckedChange={setVariationsEnabled}
                  disabled={loading}
                />
                <span className="toggle-label">Multiple versions</span>
              </div>
            )}
          </div>
        </section>

        {/* Loading Card */}
        {loading && (
          <LoadingCard mode={mode === "expand_shorten" ? expandShortenMode : mode} />
        )}

        {/* Output */}
        {result && !loading && (
          <OutputSection
            result={result}
            onRegenerate={runGenerate}
            loading={loading}
          />
        )}
      </main>

      <Toaster position="bottom-right" theme="dark" />
    </div>
  );
}
