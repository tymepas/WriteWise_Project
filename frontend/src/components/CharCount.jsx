import { toast } from "sonner";

// Field limits enforced by the backend (backend/server.py).
export const LIMITS = {
  input: 12000,
  context: 2000,
  experience: 1000,
  targetRole: 300,
  skills: 1000,
};

const formatNumber = (n) => n.toLocaleString("en-US");

/** "0 / 12,000" counter that gets gradually more prominent near the limit. */
export default function CharCount({ id, value, max }) {
  const length = value.length;
  const ratio = length / max;
  const level = ratio >= 0.95 ? "danger" : ratio >= 0.8 ? "warn" : "normal";
  return (
    <span id={id} className={`char-count char-count-${level}`} data-testid={id}>
      {formatNumber(length)} / {formatNumber(max)}
    </span>
  );
}

/**
 * The fields use maxLength, which makes the browser cut an oversized paste.
 * Tell the user when that happens instead of truncating silently.
 */
export function warnIfPasteTooLong(event, max, label) {
  const el = event.currentTarget;
  const pasted = event.clipboardData?.getData("text") ?? "";
  const selected = (el.selectionEnd ?? 0) - (el.selectionStart ?? 0);
  const resulting = el.value.length - selected + pasted.length;
  if (resulting > max) {
    toast.warning(`${label} is limited to ${formatNumber(max)} characters.`, {
      description: "The pasted text did not fully fit, so it was cut off at the limit. Check the end of your text and shorten it if something important is missing.",
    });
  }
}
