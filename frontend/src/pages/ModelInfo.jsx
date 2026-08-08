import { useModelInfo } from "../context/ModelInfoContext";
import Loader from "../components/Loader";

const METRIC_KEYS = ["accuracy", "precision", "recall", "f1_score", "roc_auc"];
const METRIC_LABELS = {
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1_score: "F1",
  roc_auc: "ROC AUC",
};

export default function ModelInfo() {
  const { modelInfo, error, loading } = useModelInfo();

  return (
    <>
      <div className="page-header">
        <p className="page-header__eyebrow">Model registry</p>
        <h1 className="page-header__title">Model Info</h1>
        <p className="page-header__desc">
          Comparison of every candidate model trained on the loan dataset,
          plus the feature set the champion model relies on.
        </p>
      </div>

      {loading && <Loader label="Loading model metrics…" />}
      {error && (
        <div className="form-error">
          Could not load model info: {error}. Make sure the backend is running
          and the pipeline has been trained (<code>python main.py</code>).
        </div>
      )}

      {modelInfo && (
        <>
          <div className="grid grid--3" style={{ marginBottom: 28 }}>
            <div className="card card--safe">
              <p className="card__label">Champion model</p>
              <p className="card__value" style={{ fontSize: 22 }}>{modelInfo.best_model}</p>
              <p className="card__caption">Selected by highest ROC AUC on the held-out test set</p>
            </div>
            <div className="card">
              <p className="card__label">Total features</p>
              <p className="card__value">{modelInfo.feature_count}</p>
              <p className="card__caption">
                {modelInfo.numeric_features.length} numeric &middot; {modelInfo.categorical_features.length} categorical
              </p>
            </div>
            <div className="card">
              <p className="card__label">Candidates evaluated</p>
              <p className="card__value">{Object.keys(modelInfo.metrics).length}</p>
              <p className="card__caption">Logistic Regression &middot; Random Forest &middot; XGBoost</p>
            </div>
          </div>

          <h2 className="section-title">Model comparison</h2>
          <div className="table-wrap" style={{ marginBottom: 32 }}>
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>Model</th>
                  {METRIC_KEYS.map((k) => (
                    <th key={k}>{METRIC_LABELS[k]}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(modelInfo.metrics)
                  .sort((a, b) => b[1].roc_auc - a[1].roc_auc)
                  .map(([name, m]) => (
                    <tr key={name} className={name === modelInfo.best_model ? "champion" : ""}>
                      <td>{name}</td>
                      {METRIC_KEYS.map((k) => (
                        <td key={k}>{(m[k] * 100).toFixed(1)}%</td>
                      ))}
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid--2">
            <div className="card">
              <p className="section-title" style={{ marginBottom: 12 }}>Numeric features</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {modelInfo.numeric_features.map((f) => (
                  <span key={f} className="badge">{f}</span>
                ))}
              </div>
            </div>
            <div className="card">
              <p className="section-title" style={{ marginBottom: 12 }}>Categorical features</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {modelInfo.categorical_features.map((f) => (
                  <span key={f} className="badge">{f}</span>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
