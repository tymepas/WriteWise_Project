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

export default function LoadingCard({ mode }) {
  const label = LOADING_LABELS[mode] || "WriteWise is refining your text...";

  return (
    <div className="loading-card" data-testid="loading-card">
      <div className="loading-icon-wrap">
        <div className="loading-glow" />
        <WIcon size={56} className="loading-wicon" />
      </div>
      <p className="loading-card-text">WriteWise is refining your text...</p>
      <p className="loading-card-mode">{label}</p>
      <div className="loading-dots" aria-hidden="true">
        <span /><span /><span />
      </div>
    </div>
  );
}
