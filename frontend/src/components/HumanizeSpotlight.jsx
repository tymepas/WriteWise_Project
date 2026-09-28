import { ArrowRight, Fingerprint } from "lucide-react";

// Static illustration, clearly labelled "Example" in the UI; not a generated result.
export const HUMANIZE_EXAMPLE = {
  before: "It is imperative to leverage synergistic solutions to optimize stakeholder outcomes.",
  after: "We need tools that work well together so everyone gets better results.",
};

/**
 * Right-panel spotlight for the existing Humanize mode. It does not add a feature:
 * "Try Humanize" switches to the Humanize tab (see App.js).
 * The transformation animation plays when the panel appears and again on hover or focus.
 */
export default function HumanizeSpotlight({ onTry }) {
  return (
    <section className="spotlight" aria-labelledby="spotlight-title">
      <div className="spotlight-top">
        <span className="spotlight-kicker">
          <Fingerprint size={14} strokeWidth={1.75} aria-hidden="true" />
          <span id="spotlight-title">Humanize</span>
        </span>
        <span className="spotlight-badge">Featured</span>
      </div>
      <p className="spotlight-copy">Make AI-written text sound natural, personal and human.</p>

      <figure className="transform-demo">
        <figcaption className="demo-caption">Example</figcaption>
        <div className="demo-card demo-before">
          <span className="demo-tag">AI-like</span>
          <p>{HUMANIZE_EXAMPLE.before}</p>
        </div>
        <div className="demo-flow" aria-hidden="true">
          <span className="demo-line" />
          <span className="demo-beam" />
        </div>
        <div className="demo-card demo-after">
          <span className="demo-tag">Natural</span>
          <p>{HUMANIZE_EXAMPLE.after}</p>
        </div>
      </figure>

      <button type="button" className="spotlight-cta" onClick={onTry} data-testid="spotlight-try-humanize">
        Try Humanize
        <ArrowRight size={15} strokeWidth={1.75} aria-hidden="true" />
      </button>
    </section>
  );
}
