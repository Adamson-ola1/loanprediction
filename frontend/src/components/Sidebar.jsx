import { NavLink } from "react-router-dom";

const links = [
  {
    to: "/",
    label: "Risk Assessment",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="sidebar__icon">
        <path
          d="M3 17l5-5 4 4 8-9"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    to: "/model-info",
    label: "Model Info",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="sidebar__icon">
        <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="2" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="2" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="2" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="2" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__brand-mark"></span>
        <span className="sidebar__brand-name">Damdana</span>
      </div>

      <div className="sidebar__eyebrow">Workspace</div>
      {links.map((l) => (
        <NavLink
          key={l.to}
          to={l.to}
          end={l.to === "/"}
          className={({ isActive }) => `sidebar__link${isActive ? " active" : ""}`}
        >
          {l.icon}
          {l.label}
        </NavLink>
      ))}
    </aside>
  );
}
