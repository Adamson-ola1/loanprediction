import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="empty-state" style={{ paddingTop: 80 }}>
      <p style={{ fontFamily: "var(--font-mono)", color: "var(--brass-400)", fontSize: 13 }}>404</p>
      <p className="empty-state__title">This ledger page doesn't exist</p>
      <p style={{ marginBottom: 20 }}>The page you're looking for was never filed.</p>
      <Link to="/" className="btn btn--primary" style={{ display: "inline-block" }}>
        Back to Risk Assessment
      </Link>
    </div>
  );
}
