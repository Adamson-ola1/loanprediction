export default function Footer() {
  return (
    <footer
      style={{
        marginTop: 48,
        paddingTop: 20,
        borderTop: "1px solid var(--ink-700)",
        color: "var(--text-muted)",
        fontSize: 12.5,
        display: "flex",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 8,
      }}
    >
      <span>Loan Default Prediction &middot; internal risk-assessment tool</span>
      <span>Not a substitute for full underwriting review</span>
    </footer>
  );
}
