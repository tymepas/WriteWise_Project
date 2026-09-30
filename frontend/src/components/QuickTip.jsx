import { Lightbulb } from "lucide-react";

// Static guidance about how each existing mode works; not generated or analysed text.
// Auto has no tip: its description under the mode navigation already explains it.
const TIPS = {
  grammar:       "Grammar fixes spelling and grammar while keeping your own wording and voice.",
  email:          "Add your background and job details for a more tailored email.",
  tone:           "Tone changes how your message sounds while preserving important facts.",
  rewrite:        "Choose a rewrite goal to control how your message is improved.",
  paraphrase:     "Pick a style to control how the new wording reads, from simple to creative.",
  summarize:      "Choose a short summary or bullet points, depending on how you'll use it.",
  expand_shorten: "Use Additional context to say what to expand or what must stay in.",
  humanize:       "Humanize keeps your meaning while making AI-like phrasing feel more natural.",
};

/**
 * Small mode-aware tip beside Generate on large screens (hidden by CSS on smaller
 * ones and while a result is shown).
 */
export default function QuickTip({ mode }) {
  const tip = TIPS[mode];
  if (!tip) return null;
  return (
    <aside className="quick-tip" aria-labelledby="quick-tip-title" data-testid="quick-tip">
      <span className="quick-tip-kicker">
        <Lightbulb size={14} strokeWidth={1.75} aria-hidden="true" />
        <span id="quick-tip-title">Quick tip</span>
      </span>
      {/* Keyed by mode so the new tip fades in when the mode changes */}
      <p className="quick-tip-text" key={mode}>{tip}</p>
    </aside>
  );
}
