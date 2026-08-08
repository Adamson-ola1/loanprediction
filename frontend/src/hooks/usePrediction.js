import { useCallback, useState } from "react";
import { predictLoan } from "../api/client";

/**
 * Encapsulates the request lifecycle (loading / error / result) for a single
 * loan-application prediction, so pages can stay focused on layout.
 */
export function usePrediction() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = useCallback(async (application) => {
    setLoading(true);
    setError(null);
    try {
      const res = await predictLoan(application);
      setResult(res);
      return res;
    } catch (err) {
      setError(err.message || "Prediction failed");
      setResult(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, error, loading, submit, reset };
}
