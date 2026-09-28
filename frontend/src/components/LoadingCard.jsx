import { WIcon } from "./WritewiseLogo";

const LOADING_LABELS = {
  auto:           "Analyzing your text...",
  grammar:        "Fixing grammar...",
  email:          "Drafting your email...",
  tone:           "Adjusting tone...",
  rewrite:        "Rewriting for clarity...",
  paraphrase:     "Paraphrasing...",
  summarize:      "Summarizing...",
  expand:         "Expanding...",
  shorten:        "Shortening...",
  humanize:       "Humanizing the text...",
};

// Purely decorative words for the animation; they are not real processing steps.
const MOTION_WORDS = ["Understanding", "Refining", "Polishing"];

/** Shown only while a request is in flight, so the animation ends when the response arrives. */
export default function LoadingCard({ mode }) {
  const label = LOADING_LABELS[mode] || "WriteWise is refining your text...";

  return (
    <div className="loading-card" data-testid="loading-card" role="status" aria-live="polite">
      <div className="loading-orb" aria-hidden="true">
        <span className="loading-ring" />
        <span className="loading-glow" />
        <WIcon size={46} className="loading-wicon" />
      </div>
      <p className="loading-kicker" aria-hidden="true">✦ WriteWise AI</p>
      <p className="loading-card-text">Working on your writing...</p>
      <p className="loading-card-mode">{label}</p>
      <div className="loading-words" aria-hidden="true">
        {MOTION_WORDS.map((word, i) => (
          <span key={word} style={{ animationDelay: `${i * 0.6}s` }}>{word}</span>
        ))}
      </div>
      <div className="loading-bar" aria-hidden="true"><span /></div>
    </div>
  );
}
