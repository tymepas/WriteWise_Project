const STEPS = [
  { id: "paste",   number: "01", title: "Paste",   text: "Add your draft, email or job post." },
  { id: "choose",  number: "02", title: "Choose",  text: "Pick a mode, or let Auto decide." },
  { id: "improve", number: "03", title: "Improve", text: "Generate, then copy or regenerate." },
];

/**
 * Static three-step guide shown beside the hero on large screens (hidden by CSS on
 * smaller ones). It fades out once a result is on screen so it never competes with it.
 */
export default function HowItWorks({ hidden = false }) {
  return (
    <section
      className={`how-it-works${hidden ? " is-hidden" : ""}`}
      aria-labelledby="how-it-works-title"
      aria-hidden={hidden || undefined}
      data-testid="how-it-works"
    >
      <h2 id="how-it-works-title" className="how-title">How WriteWise works</h2>
      <ol className="how-steps">
        {STEPS.map((step) => (
          <li key={step.id} className="how-step">
            <span className="how-number" aria-hidden="true">{step.number}</span>
            <span className="how-step-title">{step.title}</span>
            <span className="how-step-text">{step.text}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
