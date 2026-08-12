import { useCallback, useState } from "react";
import { predictLoan } from "../api/client";

export function usePrediction() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = useCallback(async (application) => {
    setLoading(true);
    setError(null);

    try {
      const response = await predictLoan(application);
      setResult(response);
      return response;
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Prediction failed. Please try again.";

      setError(message);
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

  return {
    result,
    error,
    loading,
    submit,
    reset,
  };
}