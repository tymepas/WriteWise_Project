import { useState } from "react";
import "@/App.css";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Wand2, Loader2, ArrowDown, Sparkles } from "lucide-react";
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
  tone:           "e.g. friendly, confident, formal, polite...",
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
  const [experience, setExperience] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [skills, setSkills] = useState("");
  const [variationsEnabled, setVariationsEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Tab sub-options
  const [paraphraseMode, setParaphraseMode] = useState("standard");
  const [summaryType, setSummaryType] = useState("short");
  const [expandShortenMode, setExpandShortenMode] = useState("shorten");

  const currentMode = MODES.find((m) => m.id === mode);

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setResult(null);
  };

  const handleTemplateSelect = (template) => {
    setInput(template.text);
    setMode(template.mode);
    setResult(null);
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
    };
  };

  const runGenerate = async () => {
    setLoading(true);
    setResult(null);
    try {
      const { data } = await axios.post(`${API}/generate`, buildPayload());
      setResult(data);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Something went wrong. Please try again.";
      toast.error(msg);
    } finally {
      setLoading(false);
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
    setResult(null);
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
          disabled={loading}
        />

        {/* Input Section */}
        <section className="input-section">
          <div className="input-label">Your text</div>
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
