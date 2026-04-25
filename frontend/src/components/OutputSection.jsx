import { useState } from "react";
import { Copy, Check, RefreshCw, CheckCircle, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

function copyToClipboard(text, onSuccess) {
  const doCopy = () => {
    toast.success("Copied to clipboard");
    onSuccess();
  };
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(doCopy).catch(() => {
      const el = document.createElement("textarea");
      el.value = text;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
      doCopy();
    });
  } else {
    const el = document.createElement("textarea");
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
    doCopy();
  }
}

function CopyBtn({ text, testId }) {
  const [copied, setCopied] = useState(false);
  const handle = () =>
    copyToClipboard(text, () => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  return (
    <Button
      data-testid={testId || "copy-btn"}
      variant="outline"
      size="sm"
      onClick={handle}
      className="copy-btn"
    >
      {copied ? (
        <><Check size={13} strokeWidth={1.5} />Copied</>
      ) : (
        <><Copy size={13} strokeWidth={1.5} />Copy</>
      )}
    </Button>
  );
}

function OutputCard({ label, text, testId, accent }) {
  return (
    <div className="output-block">
      <div className="output-header">
        <div className={`output-block-label ${accent ? "label-accent" : ""}`}>{label}</div>
        <CopyBtn text={text} testId={testId} />
      </div>
      <Card className="output-card">
        <CardContent className="output-content">
          <pre className="output-text">{text}</pre>
        </CardContent>
      </Card>
    </div>
  );
}

function ScoreBar({ label, score }) {
  const pct = Math.min(Math.max(score, 0), 10) * 10;
  return (
    <div className="score-item" data-testid={`score-${label.toLowerCase()}`}>
      <div className="score-header">
        <span className="score-label">{label}</span>
        <span className="score-value">
          {score}<span className="score-max">/10</span>
        </span>
      </div>
      <div className="score-bar-bg">
        <div className="score-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function OutputSection({ result, onRegenerate, loading }) {
  const { output, variations, detected_mode, why_good_fit, evaluation } = result;

  return (
    <section className="output-section" data-testid="output-section">
      {/* Auto-detected mode badge */}
      {detected_mode && (
        <div className="detected-badge" data-testid="detected-mode">
          <Zap size={11} strokeWidth={1.5} />
          Auto-detected: <strong>{detected_mode}</strong> mode
        </div>
      )}

      {/* Single output */}
      {output && !variations && (
        <div className="output-single" data-testid="single-output">
          <div className="output-header">
            <div className="input-label">Result</div>
            <div className="output-actions">
              <Button
                data-testid="regenerate-btn"
                variant="outline"
                size="sm"
                onClick={onRegenerate}
                disabled={loading}
                className="copy-btn"
              >
                <RefreshCw size={13} strokeWidth={1.5} />
                Regenerate
              </Button>
              <CopyBtn text={output} testId="copy-btn" />
            </div>
          </div>
          <Card className="output-card" data-testid="output-card">
            <CardContent className="output-content">
              <pre className="output-text">{output}</pre>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Variations */}
      {variations && variations.length > 0 && (
        <div className="variations-section" data-testid="variations-section">
          <div className="section-header-row">
            <div className="input-label">3 Variations</div>
            <Button
              data-testid="regenerate-btn"
              variant="outline"
              size="sm"
              onClick={onRegenerate}
              disabled={loading}
              className="copy-btn"
            >
              <RefreshCw size={13} strokeWidth={1.5} />
              Regenerate
            </Button>
          </div>
          <div className="variations-list">
            {variations.map((v, i) => (
              <OutputCard
                key={i}
                label={v.label}
                text={v.output}
                testId={`copy-btn-${v.label.toLowerCase()}`}
                accent={i === 0}
              />
            ))}
          </div>
        </div>
      )}

      {/* Why Good Fit */}
      {why_good_fit && why_good_fit.length > 0 && (
        <div className="why-fit-section" data-testid="why-good-fit">
          <div className="input-label">Why you're a strong fit</div>
          <div className="why-fit-card">
            {why_good_fit.map((bullet, i) => (
              <div key={i} className="why-fit-bullet">
                <CheckCircle size={14} strokeWidth={1.5} className="bullet-icon" />
                <span>{bullet}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evaluation */}
      {evaluation && (
        <div className="evaluation-section" data-testid="evaluation-section">
          <div className="input-label">Output evaluation</div>
          <div className="scores-grid">
            <ScoreBar label="Clarity" score={evaluation.clarity} />
            <ScoreBar label="Professionalism" score={evaluation.professionalism} />
            <ScoreBar label="Personalization" score={evaluation.personalization} />
          </div>
          {evaluation.suggestion && (
            <p className="eval-suggestion" data-testid="eval-suggestion">
              {evaluation.suggestion}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
