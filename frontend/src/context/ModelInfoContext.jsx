import { createContext, useContext, useEffect, useState } from "react";
import { getModelInfo } from "../api/client";

const ModelInfoContext = createContext(null);

export function ModelInfoProvider({ children }) {
  const [modelInfo, setModelInfo] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getModelInfo()
      .then((data) => {
        if (!cancelled) setModelInfo(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <ModelInfoContext.Provider value={{ modelInfo, error, loading }}>
      {children}
    </ModelInfoContext.Provider>
  );
}

export function useModelInfo() {
  const ctx = useContext(ModelInfoContext);
  if (!ctx) {
    throw new Error("useModelInfo must be used within a ModelInfoProvider");
  }
  return ctx;
}
