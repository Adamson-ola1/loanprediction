import { useState } from "react";
import { predictLoan } from "../api/client";

export function useLoanPrediction() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const predict = async (application) => {
    setLoading(true);
    setError("");
    setResult(null);

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
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError("");
  };

  return {
    result,
    loading,
    error,
    predict,
    reset,
  };
}