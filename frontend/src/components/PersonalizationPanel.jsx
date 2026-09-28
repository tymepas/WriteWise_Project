import { useEffect, useState } from "react";
import { ChevronDown, UserRound } from "lucide-react";
import { Input } from "@/components/ui/input";
import CharCount, { LIMITS, warnIfPasteTooLong } from "@/components/CharCount";

function ProfileField({ id, label, value, onChange, placeholder, max, disabled, testId }) {
  const countId = `${id}-count`;
  return (
    <div className="profile-field">
      <div className="field-label-row">
        <label className="input-label" htmlFor={id}>{label}</label>
        <CharCount id={countId} value={value} max={max} />
      </div>
      <Input
        id={id}
        data-testid={testId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onPaste={(e) => warnIfPasteTooLong(e, max, label)}
        maxLength={max}
        aria-describedby={countId}
        placeholder={placeholder}
        className="context-input"
        disabled={disabled}
      />
    </div>
  );
}

export default function PersonalizationPanel({
  experience,
  targetRole,
  skills,
  onExperienceChange,
  onTargetRoleChange,
  onSkillsChange,
  recommended = false,
  disabled,
}) {
  const hasData = !!(experience || targetRole || skills);
  const [open, setOpen] = useState(recommended && !hasData);

  // Job emails can only mention background the user gives, so surface the
  // fields when they matter and are still empty.
  useEffect(() => {
    if (recommended && !hasData) setOpen(true);
  }, [recommended, hasData]);

  return (
    <div className={`personalization-panel${open ? " is-open" : ""}`}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`personalization-toggle ${hasData ? "has-data" : ""}`}
        aria-expanded={open}
        aria-controls="personalization-fields"
        data-testid="personalization-toggle"
      >
        <UserRound size={14} strokeWidth={1.75} aria-hidden="true" />
        <span>Personalize your output</span>
        {hasData && <span className="data-dot" aria-label="Profile saved" role="img" />}
        <ChevronDown size={14} strokeWidth={1.75} className="toggle-chevron" aria-hidden="true" />
      </button>

      {recommended && !hasData && (
        <p className="personalization-hint" data-testid="personalization-hint">
          Add your experience and skills so the email can describe your real background.
        </p>
      )}

      {open && (
        <div className="personalization-fields" id="personalization-fields" data-testid="personalization-fields">
          <div className="fields-grid">
            <ProfileField id="experience-input" testId="experience-input" label="Experience"
              value={experience} onChange={onExperienceChange} max={LIMITS.experience}
              placeholder="e.g. 4.5 years in market research" disabled={disabled} />
            <ProfileField id="target-role-input" testId="target-role-input" label="Target role"
              value={targetRole} onChange={onTargetRoleChange} max={LIMITS.targetRole}
              placeholder="e.g. Data Analyst" disabled={disabled} />
          </div>
          <ProfileField id="skills-input" testId="skills-input" label="Skills (comma-separated, optional)"
            value={skills} onChange={onSkillsChange} max={LIMITS.skills}
            placeholder="e.g. Python, SQL, Tableau, Excel" disabled={disabled} />
          <p className="personalization-note">Saved in this browser only.</p>
        </div>
      )}
    </div>
  );
}
