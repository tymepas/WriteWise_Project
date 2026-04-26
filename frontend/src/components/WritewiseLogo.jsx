export function WIcon({ size = 32, className = "" }) {
  return (
    <svg
      width={size}
      height={Math.round(size * 0.77)}
      viewBox="0 0 56 43"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="ww-main" x1="3" y1="8" x2="49" y2="36" gradientUnits="userSpaceOnUse">
          <stop offset="0%"   stopColor="#8B5CF6" />
          <stop offset="48%"  stopColor="#6366F1" />
          <stop offset="100%" stopColor="#06B6D4" />
        </linearGradient>
      </defs>

      {/* W main shape */}
      <path
        d="M3 8 L13 36 L26 16 L39 36 L49 8"
        stroke="url(#ww-main)"
        strokeWidth="5.5"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Feather barbs on right descender */}
      <path d="M41 29 L46 25"   stroke="#38BDF8" strokeWidth="1.4" strokeLinecap="round" opacity="0.85" />
      <path d="M43.5 22 L49 18" stroke="#7DD3FC" strokeWidth="1.2" strokeLinecap="round" opacity="0.75" />
      <path d="M46 15 L51 11"   stroke="#BAE6FD" strokeWidth="1.0" strokeLinecap="round" opacity="0.60" />

      {/* Large sparkle top-right */}
      <path d="M47 1 L47.8 3.7 L50.5 4.5 L47.8 5.3 L47 8 L46.2 5.3 L43.5 4.5 L46.2 3.7Z" fill="#A5F3FC" />

      {/* Small sparkle */}
      <path d="M50.5 9.5 L51.1 11 L52.5 11.5 L51.1 12 L50.5 13.5 L49.9 12 L48.5 11.5 L49.9 11Z" fill="#DDD6FE" opacity="0.85" />
    </svg>
  );
}

export default function WritewiseLogo({ iconSize = 26 }) {
  return (
    <div className="ww-logo" aria-label="WriteWise">
      <WIcon size={iconSize} />
      <span className="ww-logo-text">
        <span className="ww-write">Write</span>
        <span className="ww-wise">Wise</span>
      </span>
    </div>
  );
}
