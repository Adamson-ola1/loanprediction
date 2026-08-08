export default function Loader({ label = "Loading…" }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        color: "var(--text-secondary)",
        fontSize: 13.5,
        padding: "20px 0",
      }}
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle
          cx="8"
          cy="8"
          r="6.5"
          stroke="var(--ink-600)"
          strokeWidth="2.5"
        />
        <path
          d="M8 1.5A6.5 6.5 0 0 1 14.5 8"
          stroke="var(--brass-400)"
          strokeWidth="2.5"
          strokeLinecap="round"
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 8 8"
            to="360 8 8"
            dur="0.8s"
            repeatCount="indefinite"
          />
        </path>
      </svg>
      <span>{label}</span>
    </div>
  );
}
