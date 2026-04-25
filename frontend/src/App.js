import { useState } from "react";
import "@/App.css";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Wand2, Loader2 } from "lucide-react";
import axios from "axios";
import QuickTemplates from "@/components/QuickTemplates";
import PersonalizationPanel from "@/components/PersonalizationPanel";
import OutputSection from "@/components/OutputSection";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MODES = [
  { id: "auto", label: "Auto", description: "AI detects what you need and acts on it" },
  { id: "grammar", label: "Grammar", description: "Fix grammar & spelling without changing your voice" },
  { id: "email", label: "Email", description: "Draft a professional email or job application" },
  { id: "tone", label: "Tone", description: "Rewrite in a specific tone" },
  { id: "rewrite", label: "Rewrite", description: "Improve clarity, flow, and impact" },
];

const PLACEHOLDERS = {
  auto: "Type or paste anything — grammar fix, email draft, tone rewrite, or clarity improvement...",
  grammar: "Paste your text here to fix grammar and spelling...",
  email: "Paste a job posting or describe the email you need...",
  tone: "Paste the text you want to rewrite in a different tone...",
  rewrite: "Paste your text here to improve clarity and flow...",
};

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

  const currentMode = MODES.find((m) => m.id === mode);

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setResult(null);
  };

  const handleTemplateSelect = (template) => {
    setInput(template.text);
    setMode(template.mode);
    setResult(null);
    window.scrollTo({ top: 280, behavior: "smooth" });
  };

  const buildPayload = () => ({
    mode,
    input: input.trim(),
    context: context.trim() || null,
    experience: experience.trim() || null,
    target_role: targetRole.trim() || null,
    skills: skills.trim() || null,
    variations: variationsEnabled,
  });

  const handleGenerate = async () => {
    if (!input.trim()) {
      toast.error("Please enter some text first.");
      return;
    }
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

  const handleRegenerate = async () => {
    if (!input.trim()) return;
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

  return (
    <div className="app-root">
      <div className="bg-texture" aria-hidden="true" />

      <main className="container">
        {/* Header */}
        <header className="header">
          <div className="header-badge">
            <Wand2 size={13} strokeWidth={1.5} />
            <span>AI Writing Assistant</span>
          </div>
          <h1 className="heading-1">Write smarter,<br />land the role.</h1>
          <p className="subheading">
            Grammar fixes, job emails, tone rewrites — powered by Claude AI.
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
                className="mode-trigger"
                data-testid={`mode-tab-${m.id}`}
              >
                {m.label}
              </TabsTrigger>
            ))}
          </TabsList>
          <p className="mode-description">{currentMode.description}</p>
        </Tabs>

        {/* Input Section */}
        <section className="input-section">
          <div className="input-label">Your text</div>
          <Textarea
            data-testid="main-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={PLACEHOLDERS[mode]}
            className="main-textarea"
            disabled={loading}
          />

          {/* Personalization Panel */}
          <PersonalizationPanel
            experience={experience}
            targetRole={targetRole}
            skills={skills}
            onExperienceChange={setExperience}
            onTargetRoleChange={setTargetRole}
            onSkillsChange={setSkills}
            disabled={loading}
          />

          {/* Context */}
          <div>
            <div className="input-label">Additional context (optional)</div>
            <Input
              data-testid="context-input"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder={
                mode === "tone"
                  ? "e.g. friendly, confident, formal, polite..."
                  : "e.g. Make it more confident, applying for a startup role..."
              }
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
                  Generating…
                </>
              ) : (
                <>
                  <Wand2 size={15} strokeWidth={1.5} />
                  Generate
                </>
              )}
            </Button>

            <div className="variations-toggle" data-testid="variations-toggle-row">
              <Switch
                data-testid="variations-switch"
                checked={variationsEnabled}
                onCheckedChange={setVariationsEnabled}
                disabled={loading}
              />
              <span className="toggle-label">Multiple versions</span>
            </div>
          </div>
        </section>

        {/* Output */}
        {result && (
          <OutputSection
            result={result}
            onRegenerate={handleRegenerate}
            loading={loading}
          />
        )}
      </main>

      <Toaster position="bottom-right" theme="dark" />
    </div>
  );
}
