import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes";
import { ModelInfoProvider } from "./context/ModelInfoContext";

export default function App() {
  return (
    <BrowserRouter>
      <ModelInfoProvider>
        <AppRoutes />
      </ModelInfoProvider>
    </BrowserRouter>
  );
}
