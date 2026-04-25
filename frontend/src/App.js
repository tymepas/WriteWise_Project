import { useState } from "react";
import "@/App.css";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { Copy, Check, Loader2, Wand2 } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MODES = [
  {
    id: "grammar",
    label: "Grammar",
    description: "Fix grammar & spelling errors",
    contextLabel: null,
    contextPlaceholder: null,
  },
  {
    id: "email",
    label: "Email",
    description: "Draft a professional email or job application",
    contextLabel: "Additional context (optional)",
    contextPlaceholder: "e.g. I have 3 years of experience in React...",
  },
  {
    id: "tone",
    label: "Tone",
    description: "Rewrite in a specific tone",
    contextLabel: "Desired tone",
    contextPlaceholder: "e.g. formal, friendly, confident, polite",
  },
  {
    id: "rewrite",
    label: "Rewrite",
    description: "Improve clarity, flow, and impact",
    contextLabel: "Additional context (optional)",
    contextPlaceholder: "e.g. make it more concise...",
  },
];

const TEXTAREA_PLACEHOLDERS = {
  grammar: "Paste your text here to fix grammar and spelling...",
  email: "Paste a job posting, or describe what email you need...",
  tone: "Paste the text you want to rewrite...",
  rewrite: "Paste your text here to improve it...",
};

export default function App() {
  const [mode, setMode] = useState("grammar");
  const [input, setInput] = useState("");
  const [context, setContext] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const currentMode = MODES.find((m) => m.id === mode);

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setOutput("");
    setContext("");
  };

  const handleGenerate = async () => {
    if (!input.trim()) {
      toast.error("Please enter some text first.");
      return;
    }
    setLoading(true);
    setOutput("");
    try {
      const { data } = await axios.post(`${API}/generate`, {
        mode,
        input: input.trim(),
        context: context.trim() || null,
      });
      setOutput(data.output);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Something went wrong. Please try again.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!output) return;
    navigator.clipboard.writeText(output).then(() => {
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    });
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
            placeholder={TEXTAREA_PLACEHOLDERS[mode]}
            className="main-textarea"
            disabled={loading}
          />

          {currentMode.contextLabel && (
            <div className="context-row">
              <div className="input-label">{currentMode.contextLabel}</div>
              <Input
                data-testid="context-input"
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder={currentMode.contextPlaceholder}
                className="context-input"
                disabled={loading}
              />
            </div>
          )}

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
        </section>

        {/* Output Section */}
        {output && (
          <section className="output-section" data-testid="output-section">
            <div className="output-header">
              <div className="input-label">Result</div>
              <Button
                data-testid="copy-btn"
                variant="outline"
                size="sm"
                onClick={handleCopy}
                className="copy-btn"
              >
                {copied ? (
                  <>
                    <Check size={13} strokeWidth={1.5} />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy size={13} strokeWidth={1.5} />
                    Copy
                  </>
                )}
              </Button>
            </div>
            <Card className="output-card" data-testid="output-card">
              <CardContent className="output-content">
                <pre className="output-text">{output}</pre>
              </CardContent>
            </Card>
          </section>
        )}
      </main>

      <Toaster position="bottom-right" theme="dark" />
    </div>
  );
}
