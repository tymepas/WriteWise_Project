const PARAPHRASE_STYLES = [
  { id: "standard", label: "Standard" },
  { id: "fluency",  label: "Fluency" },
  { id: "formal",   label: "Formal" },
  { id: "simple",   label: "Simple" },
  { id: "creative", label: "Creative" },
];

export default function TabOptions({
  mode,
  paraphraseMode, onParaphraseMode,
  summaryType, onSummaryType,
  expandShortenMode, onExpandShortenMode,
  disabled,
}) {
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
