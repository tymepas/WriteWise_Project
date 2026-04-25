import { useState } from "react";
import { ChevronDown, ChevronUp, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";

export default function PersonalizationPanel({
  experience,
  targetRole,
  skills,
  onExperienceChange,
  onTargetRoleChange,
  onSkillsChange,
  disabled,
}) {
  const [open, setOpen] = useState(false);
  const hasData = !!(experience || targetRole || skills);

  return (
    <div className="personalization-panel">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`personalization-toggle ${hasData ? "has-data" : ""}`}
        data-testid="personalization-toggle"
      >
        <SlidersHorizontal size={12} strokeWidth={1.5} />
        <span>Personalize your output</span>
        {hasData && <span className="data-dot" aria-hidden="true" />}
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {open && (
        <div className="personalization-fields" data-testid="personalization-fields">
          <div className="fields-grid">
            <div>
              <div className="input-label">Experience</div>
              <Input
                data-testid="experience-input"
                value={experience}
                onChange={(e) => onExperienceChange(e.target.value)}
                placeholder="e.g. 4.5 years in market research"
                className="context-input"
                disabled={disabled}
              />
            </div>
            <div>
              <div className="input-label">Target Role</div>
              <Input
                data-testid="target-role-input"
                value={targetRole}
                onChange={(e) => onTargetRoleChange(e.target.value)}
                placeholder="e.g. Data Analyst"
                className="context-input"
                disabled={disabled}
              />
            </div>
          </div>
          <div>
            <div className="input-label">Skills (comma-separated, optional)</div>
            <Input
              data-testid="skills-input"
              value={skills}
              onChange={(e) => onSkillsChange(e.target.value)}
              placeholder="e.g. Python, SQL, Tableau, Excel"
              className="context-input"
              disabled={disabled}
            />
          </div>
        </div>
      )}
    </div>
  );
}
