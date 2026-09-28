import { useEffect, useRef, useState } from "react";
import "@/App.css";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Loader2, Sparkles, ArrowRight, X } from "lucide-react";
import axios from "axios";
import QuickTemplates from "@/components/QuickTemplates";
import PersonalizationPanel from "@/components/PersonalizationPanel";
import OutputSection from "@/components/OutputSection";
import TabOptions from "@/components/TabOptions";
import WritewiseLogo from "@/components/WritewiseLogo";
import LoadingCard from "@/components/LoadingCard";
import ModeNav from "@/components/ModeNav";
import HumanizeSpotlight, { HUMANIZE_EXAMPLE } from "@/components/HumanizeSpotlight";
import CharCount, { LIMITS, warnIfPasteTooLong } from "@/components/CharCount";

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

// Matches the CSS breakpoint where the two panes stack.
const STACKED_LAYOUT_QUERY = "(max-width: 959px)";

const prefersReducedMotion = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

function scrollIntoViewIfNeeded(el, block = "start") {
  if (!el) return;
  const rect = el.getBoundingClientRect();
  if (rect.top < 0 || rect.top > window.innerHeight * 0.75) {
    el.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block });
  }
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

  const panelRef = useRef(null);
  // Brief visual confirmation on the Generate button when a real result arrives.
  const [justCompleted, setJustCompleted] = useState(false);

  useEffect(() => {
    if (!result) return undefined;
    setJustCompleted(true);
    // Bring the result into view if the panel is off screen (e.g. stacked layout).
    scrollIntoViewIfNeeded(panelRef.current);
    const timer = setTimeout(() => setJustCompleted(false), 900);
    return () => clearTimeout(timer);
  }, [result]);

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

  const showEditor = () => {
    setTimeout(() => scrollIntoViewIfNeeded(document.getElementById("main-input"), "center"), 50);
  };

  const handleTemplateSelect = (template) => {
    setInput(template.text);
    setMode(template.mode);
    discardResult();
    showEditor();
  };

  // The spotlight only switches to the existing Humanize mode. It fills the
  // labelled example text only when the editor is empty, never over user text.
  const handleTryHumanize = () => {
    setMode("humanize");
    discardResult();
    if (!input.trim()) setInput(HUMANIZE_EXAMPLE.before);
    showEditor();
    document.getElementById("main-input")?.focus({ preventScroll: true });
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
    // When the panes are stacked, move to the panel so the loading state is visible.
    if (window.matchMedia?.(STACKED_LAYOUT_QUERY).matches) {
      setTimeout(() => scrollIntoViewIfNeeded(panelRef.current), 50);
    }
    await runGenerate();
  };

  const handleTryExample = () => {
    setInput(EXAMPLE_TEXT);
    setMode("email");
    discardResult();
    showEditor();
  };

  const btnLabel = getButtonLabel(mode, expandShortenMode);
  const loadingMsg = getLoadingMsg(mode, expandShortenMode);
  const panelState = loading ? "loading" : result ? "result" : "empty";

  return (
    <div className="app-root">
      <div
        className="bg-texture"
        aria-hidden="true"
        style={{ backgroundImage: `url(${process.env.PUBLIC_URL}/images/bg-texture.png)` }}
      />
      <div className="bg-atmosphere" aria-hidden="true">
        <span className="bg-grid" />
        <span className="bg-glow bg-glow-a" />
        <span className="bg-glow bg-glow-b" />
      </div>

      <div className="shell">
        <header className="site-header">
          <WritewiseLogo iconSize={24} />
          <span className={`ai-status${loading ? " is-working" : ""}`} data-testid="ai-status">
            <span className="ai-status-dot" aria-hidden="true" />
            {loading ? "WriteWise is working..." : "Ready to write"}
          </span>
        </header>

        {/* state-* lets the desktop layout give a result more room */}
        <main className={`workspace state-${panelState}`} aria-labelledby="page-title">
          {/* Spans both panes so all nine modes fit on one row on desktop */}
          <div className="workspace-top">
            <div className="hero">
              <h1 className="heading-1" id="page-title">
                Write better. <span className="heading-accent">Get noticed.</span>
              </h1>
              <p className="subheading">
                Paste your text, draft, email, or job post, and let WriteWise help you make it better.{" "}
                <button type="button" className="inline-action" onClick={handleTryExample} data-testid="cta-try-example">
                  Try an example
                </button>
              </p>
            </div>

            <ModeNav
              modes={MODES}
              value={mode}
              onChange={handleModeChange}
              description={currentMode.description}
            />
          </div>

          <section className="workspace-main" aria-label="Editor">
            {/* Editor */}
            <div className="editor-card">
              <div className="field-label-row">
                <label className="input-label" htmlFor="main-input">Your text</label>
                <div className="editor-meta">
                  <CharCount id="main-input-count" value={input} max={LIMITS.input} />
                  <button
                    type="button"
                    className="input-clear-btn"
                    onClick={handleClear}
                    disabled={!input && !context && !result && !loading}
                    data-testid="clear-input-btn"
                    title="Clear the text and start over"
                  >
                    <X size={12} strokeWidth={1.75} aria-hidden="true" />
                    Clear
                  </button>
                </div>
              </div>
              <Textarea
                id="main-input"
                data-testid="main-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onPaste={(e) => warnIfPasteTooLong(e, LIMITS.input, "Your text")}
                maxLength={LIMITS.input}
                aria-describedby="main-input-count"
                placeholder={PLACEHOLDERS[mode]}
                className="main-textarea"
                disabled={loading}
              />
            </div>

            {/* Mode options and extra instructions */}
            <div className="options-card">
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
              <div className="option-field">
                <div className="field-label-row">
                  <label className="input-label" htmlFor="context-input">Additional context (optional)</label>
                  <CharCount id="context-input-count" value={context} max={LIMITS.context} />
                </div>
                <Input
                  id="context-input"
                  data-testid="context-input"
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  onPaste={(e) => warnIfPasteTooLong(e, LIMITS.context, "Additional context")}
                  maxLength={LIMITS.context}
                  aria-describedby="context-input-count"
                  placeholder={CONTEXT_PLACEHOLDERS[mode]}
                  className="context-input"
                  disabled={loading}
                />
              </div>
            </div>

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

            <div className="controls-row">
              <Button
                data-testid="generate-btn"
                onClick={handleGenerate}
                disabled={loading}
                aria-busy={loading}
                className={`generate-btn${loading ? " is-loading" : ""}${justCompleted ? " is-complete" : ""}`}
              >
                <span className="generate-sheen" aria-hidden="true" />
                {loading ? (
                  <>
                    <Loader2 size={16} className="spin" strokeWidth={1.75} aria-hidden="true" />
                    {loadingMsg}
                  </>
                ) : (
                  <>
                    <Sparkles size={16} strokeWidth={1.75} className="generate-icon" aria-hidden="true" />
                    {btnLabel}
                    <ArrowRight size={15} strokeWidth={1.75} className="generate-arrow" aria-hidden="true" />
                  </>
                )}
              </Button>

              {SHOW_VARIATIONS.includes(mode) && (
                <div className="variations-toggle" data-testid="variations-toggle-row">
                  <Switch
                    id="variations-switch"
                    data-testid="variations-switch"
                    checked={variationsEnabled}
                    onCheckedChange={setVariationsEnabled}
                    disabled={loading}
                  />
                  <label className="toggle-label" htmlFor="variations-switch">Multiple versions</label>
                </div>
              )}
            </div>
          </section>

          {/* Right panel: Quick start, then loading, then the result */}
          <aside
            ref={panelRef}
            className={`context-panel state-${panelState}`}
            aria-label={panelState === "result" ? "Result" : "Quick start"}
            data-testid="context-panel"
          >
            {panelState === "empty" && (
              <div className="panel-state" key="empty">
                <QuickTemplates onSelect={handleTemplateSelect} />
                <HumanizeSpotlight onTry={handleTryHumanize} />
              </div>
            )}
            {panelState === "loading" && (
              <div className="panel-state" key="loading">
                <LoadingCard mode={mode === "expand_shorten" ? expandShortenMode : mode} />
              </div>
            )}
            {panelState === "result" && (
              <div className="panel-state panel-result" key="result">
                <OutputSection result={result} onRegenerate={runGenerate} loading={loading} />
              </div>
            )}
          </aside>
        </main>
      </div>

      <Toaster position="bottom-right" theme="dark" />
    </div>
  );
}
