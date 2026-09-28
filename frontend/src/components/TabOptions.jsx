import { ChevronDown } from "lucide-react";

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

// Sent as rewrite_goal: null, which uses the standard rewrite.
const STANDARD_REWRITE = "";

const SUMMARY_TYPES = [
  { id: "short",   label: "Short Summary" },
  { id: "bullets", label: "Bullet Points" },
];

const EXPAND_SHORTEN = [
  { id: "shorten", label: "Make it shorter" },
  { id: "expand",  label: "Expand this" },
];

function SelectField({ id, label, value, onChange, options, disabled, testId }) {
  return (
    <div className="option-field">
      <label className="input-label" htmlFor={id}>{label}</label>
      <div className="select-wrap">
        <select
          id={id}
          className="option-select"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          data-testid={testId}
        >
          {options.map((o) => (
            <option key={o.id} value={o.id}>{o.label}</option>
          ))}
        </select>
        <ChevronDown size={15} strokeWidth={1.75} className="select-chevron" aria-hidden="true" />
      </div>
    </div>
  );
}

function PillGroup({ label, options, value, onChange, disabled, testIdPrefix, testId }) {
  return (
    <div className="option-field" data-testid={testId}>
      <div className="input-label" id={`${testId}-label`}>{label}</div>
      <div className="option-pills" role="group" aria-labelledby={`${testId}-label`}>
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            aria-pressed={value === o.id}
            onClick={() => onChange(o.id)}
            className={`option-pill${value === o.id ? " active" : ""}`}
            data-testid={`${testIdPrefix}${o.id}`}
            disabled={disabled}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Controls for the selected mode only; each one maps to a real request field. */
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
        <SelectField
          id="tone-select"
          label="Tone"
          value={tone}
          onChange={onTone}
          options={TONES}
          disabled={disabled}
          testId="tone-select"
        />
      </div>
    );
  }

  if (mode === "rewrite") {
    return (
      <div className="tab-options" data-testid="tab-options-rewrite">
        <SelectField
          id="rewrite-goal-select"
          label="Rewrite goal"
          value={rewriteGoal ?? STANDARD_REWRITE}
          onChange={(v) => onRewriteGoal(v === STANDARD_REWRITE ? null : v)}
          options={[{ id: STANDARD_REWRITE, label: "Standard rewrite" }, ...REWRITE_GOALS]}
          disabled={disabled}
          testId="rewrite-goal-select"
        />
      </div>
    );
  }

  if (mode === "paraphrase") {
    return (
      <div className="tab-options">
        <PillGroup label="Paraphrase style" options={PARAPHRASE_STYLES} value={paraphraseMode}
          onChange={onParaphraseMode} disabled={disabled}
          testIdPrefix="paraphrase-style-" testId="tab-options-paraphrase" />
      </div>
    );
  }

  if (mode === "summarize") {
    return (
      <div className="tab-options">
        <PillGroup label="Output format" options={SUMMARY_TYPES} value={summaryType}
          onChange={onSummaryType} disabled={disabled}
          testIdPrefix="summary-type-" testId="tab-options-summarize" />
      </div>
    );
  }

  if (mode === "expand_shorten") {
    return (
      <div className="tab-options">
        <PillGroup label="Action" options={EXPAND_SHORTEN} value={expandShortenMode}
          onChange={onExpandShortenMode} disabled={disabled}
          testIdPrefix="action-" testId="tab-options-expand-shorten" />
      </div>
    );
  }

  return null;
}
