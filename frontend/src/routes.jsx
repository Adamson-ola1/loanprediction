import { Routes, Route } from "react-router-dom";
import DashboardLayout from "./layouts/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import ModelInfo from "./pages/ModelInfo";
import NotFound from "./pages/NotFound";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="model-info" element={<ModelInfo />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
