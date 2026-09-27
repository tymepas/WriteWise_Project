const PARAPHRASE_STYLES = [
  { id: "standard", label: "Standard" },
  { id: "fluency",  label: "Fluency" },
  { id: "formal",   label: "Formal" },
  { id: "simple",   label: "Simple" },
  { id: "creative", label: "Creative" },
];

const TONES = [
  { id: "professional", label: "Professional" },
  { id: "casual",       label: "Casual" },
  { id: "friendly",     label: "Friendly" },
  { id: "diplomatic",   label: "Diplomatic" },
  { id: "formal",       label: "Formal" },
  { id: "confident",    label: "Confident" },
  { id: "persuasive",   label: "Persuasive" },
  { id: "empathetic",   label: "Empathetic" },
];

const REWRITE_GOALS = [
  { id: "clear_concise",   label: "Clear & Concise" },
  { id: "more_direct",     label: "More Direct" },
  { id: "more_polished",   label: "More Polished" },
  { id: "more_persuasive", label: "More Persuasive" },
  { id: "simplify",        label: "Simplify" },
  { id: "keep_style",      label: "Keep My Style" },
];

export default function TabOptions({
  mode,
  paraphraseMode, onParaphraseMode,
  summaryType, onSummaryType,
  expandShortenMode, onExpandShortenMode,
  tone, onTone,
  rewriteGoal, onRewriteGoal,
  disabled,
}) {
  if (mode === "tone") {
    return (
      <div className="tab-options" data-testid="tab-options-tone">
        <div className="input-label">Tone</div>
        <div className="option-pills" role="radiogroup" aria-label="Tone">
          {TONES.map((t) => (
            <button
              key={t.id}
              type="button"
              role="radio"
              aria-checked={tone === t.id}
              onClick={() => onTone(t.id)}
              className={`option-pill${tone === t.id ? " active" : ""}`}
              data-testid={`tone-${t.id}`}
              disabled={disabled}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (mode === "rewrite") {
    // Optional: clicking the selected goal again clears it.
    return (
      <div className="tab-options" data-testid="tab-options-rewrite">
        <div className="input-label">Rewrite goal (optional)</div>
        <div className="option-pills" role="radiogroup" aria-label="Rewrite goal">
          {REWRITE_GOALS.map((g) => (
            <button
              key={g.id}
              type="button"
              role="radio"
              aria-checked={rewriteGoal === g.id}
              onClick={() => onRewriteGoal(rewriteGoal === g.id ? null : g.id)}
              className={`option-pill${rewriteGoal === g.id ? " active" : ""}`}
              data-testid={`rewrite-goal-${g.id}`}
              disabled={disabled}
            >
              {g.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (mode === "paraphrase") {
    return (
      <div className="tab-options" data-testid="tab-options-paraphrase">
        <div className="input-label">Paraphrase style</div>
        <div className="option-pills">
          {PARAPHRASE_STYLES.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => onParaphraseMode(s.id)}
              className={`option-pill${paraphraseMode === s.id ? " active" : ""}`}
              data-testid={`paraphrase-style-${s.id}`}
              disabled={disabled}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (mode === "summarize") {
    return (
      <div className="tab-options" data-testid="tab-options-summarize">
        <div className="input-label">Output format</div>
        <div className="option-pills">
          <button
            type="button"
            onClick={() => onSummaryType("short")}
            className={`option-pill${summaryType === "short" ? " active" : ""}`}
            data-testid="summary-type-short"
            disabled={disabled}
          >
            Short Summary
          </button>
          <button
            type="button"
            onClick={() => onSummaryType("bullets")}
            className={`option-pill${summaryType === "bullets" ? " active" : ""}`}
            data-testid="summary-type-bullets"
            disabled={disabled}
          >
            Bullet Points
          </button>
        </div>
      </div>
    );
  }

  if (mode === "expand_shorten") {
    return (
      <div className="tab-options" data-testid="tab-options-expand-shorten">
        <div className="input-label">Action</div>
        <div className="option-pills">
          <button
            type="button"
            onClick={() => onExpandShortenMode("shorten")}
            className={`option-pill${expandShortenMode === "shorten" ? " active" : ""}`}
            data-testid="action-shorten"
            disabled={disabled}
          >
            Make it shorter
          </button>
          <button
            type="button"
            onClick={() => onExpandShortenMode("expand")}
            className={`option-pill${expandShortenMode === "expand" ? " active" : ""}`}
            data-testid="action-expand"
            disabled={disabled}
          >
            Expand this
          </button>
        </div>
      </div>
    );
  }

  return null;
}
