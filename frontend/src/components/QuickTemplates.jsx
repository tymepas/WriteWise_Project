import { Briefcase, ArrowRight, Send, Users } from "lucide-react";

const TEMPLATES = [
  {
    id: "job-application",
    label: "Job Application",
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
    Icon: ArrowRight,
    mode: "email",
    text: `I interviewed for the Product Manager role at Acme Inc last Tuesday. The conversation was engaging, especially the discussion about their 0-to-1 product roadmap. I wanted to follow up on my application and reiterate my strong interest in the position.`,
  },
  {
    id: "cold-outreach",
    label: "Cold Outreach",
    Icon: Send,
    mode: "email",
    text: `I came across [COMPANY] and I'm impressed by your work in [INDUSTRY]. I'm a [YOUR ROLE] with experience in [SKILLS/AREA]. I'd love to explore if there are any opportunities where I could contribute to your team, even informally.`,
  },
  {
    id: "referral",
    label: "Referral Request",
    Icon: Users,
    mode: "email",
    text: `I'm applying for the [POSITION] at [COMPANY] and noticed you work there. I have [X] years of experience in [FIELD] and believe my background aligns well with what the team is building. Would you be open to referring me or sharing any insights about the role or culture?`,
  },
];

export default function QuickTemplates({ onSelect }) {
  return (
    <div className="quick-templates">
      <div className="input-label">Quick start templates</div>
      <div className="templates-row">
        {TEMPLATES.map(({ id, label, Icon, mode, text }) => (
          <button
            key={id}
            onClick={() => onSelect({ mode, text })}
            className="template-chip"
            data-testid={`template-${id}`}
          >
            <Icon size={12} strokeWidth={1.5} />
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
