import { useCallback, useLayoutEffect, useRef, useState } from "react";
import {
  Sparkles, SpellCheck, Mail, AudioLines, PenLine, Repeat2, AlignLeft, ChevronsUpDown, Fingerprint,
  MessageSquareText,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const MODE_ICONS = {
  auto: Sparkles,
  grammar: SpellCheck,
  email: Mail,
  tone: AudioLines,
  rewrite: PenLine,
  paraphrase: Repeat2,
  summarize: AlignLeft,
  expand_shorten: ChevronsUpDown,
  humanize: Fingerprint,
  prompt: MessageSquareText,
};

/**
 * The single mode navigation. Wraps the existing Radix tabs (keyboard support included)
 * and adds a sliding active indicator. On narrow screens the row scrolls horizontally
 * and keeps the active mode in view.
 */
export default function ModeNav({ modes, value, onChange, description }) {
  const listRef = useRef(null);
  const [indicator, setIndicator] = useState(null);
  // Edge fades show only where more modes are hidden off-screen.
  const [fade, setFade] = useState({ left: false, right: false });

  const updateFade = useCallback(() => {
    const list = listRef.current;
    if (!list) return;
    const left = list.scrollLeft > 2;
    const right = list.scrollLeft + list.clientWidth < list.scrollWidth - 2;
    setFade((prev) => (prev.left === left && prev.right === right ? prev : { left, right }));
  }, []);

  useLayoutEffect(() => {
    const list = listRef.current;
    if (!list) return undefined;

    const update = () => {
      updateFade();
      const active = list.querySelector('[data-state="active"]');
      if (!active) return;
      setIndicator({ left: active.offsetLeft, width: active.offsetWidth });

      // Scroll only the tab row (never the page) so the active mode is visible.
      const behavior = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
      const start = active.offsetLeft - 16;
      const end = active.offsetLeft + active.offsetWidth + 16;
      if (start < list.scrollLeft) {
        list.scrollTo({ left: start, behavior });
      } else if (end > list.scrollLeft + list.clientWidth) {
        list.scrollTo({ left: end - list.clientWidth, behavior });
      }
    };

    update();
    const observer = new ResizeObserver(update);
    observer.observe(list);
    return () => observer.disconnect();
  }, [value, updateFade]);

  return (
    <Tabs value={value} onValueChange={onChange} className="mode-nav">
      <div className={`mode-nav-track${fade.left ? " fade-left" : ""}${fade.right ? " fade-right" : ""}`}>
        <TabsList
          ref={listRef}
          className="modes-list"
          data-testid="mode-tabs"
          aria-label="Writing mode"
          onScroll={updateFade}
        >
          {indicator && (
            <span
              className="mode-indicator"
              aria-hidden="true"
              style={{ transform: `translateX(${indicator.left}px)`, width: indicator.width }}
            />
          )}
          {modes.map((m) => {
            const Icon = MODE_ICONS[m.id];
            return (
              <TabsTrigger
                key={m.id}
                value={m.id}
                className="mode-trigger"
                data-testid={`mode-tab-${m.id}`}
              >
                {Icon && <Icon size={14} strokeWidth={1.75} className="mode-icon" aria-hidden="true" />}
                <span className="mode-label">
                  {m.label}
                  {m.badge && <span className="tab-badge">{m.badge}</span>}
                </span>
              </TabsTrigger>
            );
          })}
        </TabsList>
      </div>
      <p className="mode-description">{description}</p>
    </Tabs>
  );
}
