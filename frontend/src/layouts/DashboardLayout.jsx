import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Footer from "../components/Footer";

export default function DashboardLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <Navbar />
      <main className="app-main">
        <Outlet />
        <Footer />
      </main>
    </div>
  );
}
