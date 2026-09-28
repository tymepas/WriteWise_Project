import { Briefcase, ArrowRight, Send, Undo2, Users } from "lucide-react";

const TEMPLATES = [
  {
    id: "job-application",
    label: "Job Application",
    description: "Create a tailored application email for a role.",
    accent: "violet",
    Icon: Briefcase,
    mode: "email",
    text: `Software Engineer (Full Stack) at TechCorp

Requirements:
- 3+ years of experience with React and Node.js
- Strong CS fundamentals and system design skills
- Experience with cloud platforms (AWS/GCP)
- Excellent written and verbal communication

About us: We are a fast-growing startup building developer tools used by 10,000+ teams. Remote-first, competitive salary and equity.`,
  },
  {
    id: "follow-up",
    label: "Follow-up Email",
    description: "Check in after an interview or application.",
    accent: "blue",
    Icon: Undo2,
    mode: "email",
    text: `I interviewed for the Product Manager role at Acme Inc last Tuesday. The conversation was engaging, especially the discussion about their 0-to-1 product roadmap. I wanted to follow up on my application and reiterate my strong interest in the position.`,
  },
  {
    id: "cold-outreach",
    label: "Cold Outreach",
    description: "Introduce yourself to a company you admire.",
    accent: "cyan",
    Icon: Send,
    mode: "email",
    text: `I came across [COMPANY] and I'm impressed by your work in [INDUSTRY]. I'm a [YOUR ROLE] with experience in [SKILLS/AREA]. I'd love to explore if there are any opportunities where I could contribute to your team, even informally.`,
  },
  {
    id: "referral",
    label: "Referral Request",
    description: "Ask a contact to refer you for a position.",
    accent: "indigo",
    Icon: Users,
    mode: "email",
    text: `I'm applying for the [POSITION] at [COMPANY] and noticed you work there. I have [X] years of experience in [FIELD] and believe my background aligns well with what the team is building. Would you be open to referring me or sharing any insights about the role or culture?`,
  },
];

export default function QuickTemplates({ onSelect }) {
  return (
    <section className="quick-templates" aria-labelledby="quick-start-title">
      <div className="panel-heading">
        <h2 id="quick-start-title" className="panel-title">Quick start</h2>
        <span className="panel-caption">Fills the editor with a starter draft</span>
      </div>
      <div className="template-grid">
        {TEMPLATES.map(({ id, label, description, accent, Icon, mode, text }) => (
          <button
            key={id}
            type="button"
            onClick={() => onSelect({ mode, text })}
            className={`template-card accent-${accent}`}
            data-testid={`template-${id}`}
          >
            <span className="template-icon" aria-hidden="true">
              <Icon size={16} strokeWidth={1.75} />
            </span>
            <span className="template-text">
              <span className="template-title">{label}</span>
              <span className="template-desc">{description}</span>
            </span>
            <ArrowRight size={15} strokeWidth={1.75} className="template-arrow" aria-hidden="true" />
          </button>
        ))}
      </div>
    </section>
  );
}
