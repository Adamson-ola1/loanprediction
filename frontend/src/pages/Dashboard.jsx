import { useState } from "react";
import { usePrediction } from "../hooks/usePrediction";
import Loader from "../components/Loader";

const DEFAULT_FORM = {
  loan_amnt: 12000,
  term: "18 months",
  int_rate: "13.5",
  installment: 407.5,
  annual_inc: 55000,
  dti: 18.2,
  delinq_2yrs: 0,
  inq_last_6mths: 1,
  open_acc: 9,
  pub_rec: 0,
  revol_bal: 8000,
  revol_util: "45",
  total_acc: 22,
  pub_rec_bankruptcies: 0,
  emp_length: "5 years",
  grade: "C",
  sub_grade: "C2",
  home_ownership: "RENT",
  verification_status: "Verified",
  purpose: "debt_consolidation",
  addr_state: "CA",
  issue_d: "Dec-11",
  earliest_cr_line: "Jan-01",
};

const NUMERIC_FIELDS = new Set([
  "loan_amnt", "installment", "annual_inc", "dti", "delinq_2yrs",
  "inq_last_6mths", "open_acc", "pub_rec", "revol_bal", "total_acc",
  "pub_rec_bankruptcies",
]);

function RiskDial({ probability }) {
  // probability in [0,1] -> needle angle across a 180deg arc (-90 to +90)
  const angle = -90 + probability * 180;
  const isRisk = probability >= 0.5;

  return (
    <div className="risk-dial">
      <div className="risk-dial__figure">
        <svg viewBox="0 0 220 130" width="220" height="130">
          <path
            d="M 10 110 A 100 100 0 0 1 210 110"
            fill="none"
            stroke="var(--ink-600)"
            strokeWidth="14"
            strokeLinecap="round"
          />
          <path
            d="M 10 110 A 100 100 0 0 1 210 110"
            fill="none"
            stroke="url(#riskGradient)"
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={`${probability * 314} 314`}
          />
          <defs>
            <linearGradient id="riskGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--teal-400)" />
              <stop offset="60%" stopColor="var(--brass-400)" />
              <stop offset="100%" stopColor="var(--clay-400)" />
            </linearGradient>
          </defs>
          <g className="risk-dial__needle" style={{ transform: `rotate(${angle}deg)` }}>
            <line x1="110" y1="110" x2="110" y2="30" stroke="var(--paper-50)" strokeWidth="3" strokeLinecap="round" />
            <circle cx="110" cy="110" r="6" fill="var(--paper-50)" />
          </g>
        </svg>
        <div className="risk-dial__reading">{Math.round(probability * 100)}%</div>
      </div>
      <div className={`risk-dial__verdict ${isRisk ? "risk" : "safe"}`}>
        {isRisk ? "Elevated default risk" : "Likely to repay in full"}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const { result, error, loading, submit } = usePrediction();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      int_rate: `${form.int_rate}%`,
      revol_util: `${form.revol_util}%`,
    };
    // coerce numeric fields
    for (const key of NUMERIC_FIELDS) {
      payload[key] = Number(payload[key]);
    }
    submit(payload);
  };

  const handleReset = () => setForm(DEFAULT_FORM);

  return (
    <>
      <div className="page-header">
        <p className="page-header__eyebrow">Underwriting desk</p>
        <h1 className="page-header__title">Risk Assessment</h1>
        <p className="page-header__desc">
          Enter the details of a loan application known at the time of
          submission to estimate the probability of default before a
          decision is made.
        </p>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1.6fr 1fr", alignItems: "start" }}>
        <form className="form-card" onSubmit={handleSubmit}>
          {error && <div className="form-error">{error}</div>}

          <div className="form-grid">
            <div className="field">
              <label>Loan amount ($)</label>
              <input type="number" name="loan_amnt" value={form.loan_amnt} onChange={handleChange} min="0" step="100" />
            </div>
            <div className="field">
              <label>Term</label>
              <select name="term" value={form.term} onChange={handleChange}>
                <option value="6 months">6 months</option>
                <option value="12 months">12 months</option>
                <option value="18 months">18 months</option>
                <option value="24 months">24 months</option>
                <option value="30 months">30 months</option>
                <option value="36 months">36 months</option>
                <option value="42 months">42 months</option>
                <option value="48 months">48 months</option>
                <option value="54 months">54 months</option>
                <option value="60 months">60 months</option>
              </select>
            </div>
            <div className="field">
              <label>Interest rate (%)</label>
              <input type="number" name="int_rate" value={form.int_rate} onChange={handleChange} step="0.1" />
            </div>

            <div className="field">
              <label>Monthly installment ($)</label>
              <input type="number" name="installment" value={form.installment} onChange={handleChange} step="0.01" />
            </div>
            <div className="field">
              <label>Annual income ($)</label>
              <input type="number" name="annual_inc" value={form.annual_inc} onChange={handleChange} step="500" />
            </div>
            <div className="field">
              <label>Debt-to-income ratio</label>
              <input type="number" name="dti" value={form.dti} onChange={handleChange} step="0.1" />
            </div>

            <div className="field">
              <label>Loan grade</label>
              <select name="grade" value={form.grade} onChange={handleChange}>
                {["A", "B", "C", "D", "E", "F", "G"].map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Sub-grade</label>
              <input type="text" name="sub_grade" value={form.sub_grade} onChange={handleChange} placeholder="C2" />
            </div>
            <div className="field">
              <label>Employment length</label>
              <select name="emp_length" value={form.emp_length} onChange={handleChange}>
                {["< 1 year", "1 year", "2 years", "3 years", "4 years", "5 years", "6 years", "7 years", "8 years", "9 years", "10+ years"].map((e) => (
                  <option key={e} value={e}>{e}</option>
                ))}
              </select>
            </div>

            <div className="field">
              <label>Home ownership</label>
              <select name="home_ownership" value={form.home_ownership} onChange={handleChange}>
                {["RENT", "OWN", "MORTGAGE", "OTHER"].map((h) => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Verification status</label>
              <select name="verification_status" value={form.verification_status} onChange={handleChange}>
                {["Verified", "Source Verified", "Not Verified"].map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>State</label>
              <input type="text" name="addr_state" value={form.addr_state} onChange={handleChange} maxLength={2} placeholder="CA" />
            </div>

            <div className="field field--span-2">
              <label>Loan purpose</label>
              <select name="purpose" value={form.purpose} onChange={handleChange}>
                {[
                  "debt_consolidation", "credit_card", "home_improvement", "major_purchase",
                  "small_business", "car", "medical", "moving", "vacation", "house", "other",
                ].map((p) => (
                  <option key={p} value={p}>{p.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Revolving utilization (%)</label>
              <input type="number" name="revol_util" value={form.revol_util} onChange={handleChange} step="1" />
            </div>

            <div className="field">
              <label>Open credit lines</label>
              <input type="number" name="open_acc" value={form.open_acc} onChange={handleChange} />
            </div>
            <div className="field">
              <label>Total credit lines</label>
              <input type="number" name="total_acc" value={form.total_acc} onChange={handleChange} />
            </div>
            <div className="field">
              <label>Revolving balance ($)</label>
              <input type="number" name="revol_bal" value={form.revol_bal} onChange={handleChange} />
            </div>

            <div className="field">
              <label>Delinquencies (2yr)</label>
              <input type="number" name="delinq_2yrs" value={form.delinq_2yrs} onChange={handleChange} />
            </div>
            <div className="field">
              <label>Inquiries (6mo)</label>
              <input type="number" name="inq_last_6mths" value={form.inq_last_6mths} onChange={handleChange} />
            </div>
            <div className="field">
              <label>Public record bankruptcies</label>
              <input type="number" name="pub_rec_bankruptcies" value={form.pub_rec_bankruptcies} onChange={handleChange} />
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn--primary" disabled={loading}>
              {loading ? "Assessing…" : "Assess risk"}
            </button>
            <button type="button" className="btn btn--ghost" onClick={handleReset}>
              Reset to sample
            </button>
          </div>
        </form>

        <div className="card">
          <p className="card__label">Prediction</p>
          {loading && <Loader label="Scoring application…" />}
          {!loading && !result && (
            <div className="empty-state" style={{ padding: "32px 8px" }}>
              <p className="empty-state__title">No assessment yet</p>
              <p>Submit the form to see a default-risk reading.</p>
            </div>
          )}
          {!loading && result && (
            <>
              <RiskDial probability={result.probability_of_default} />
              <div style={{ marginTop: 20, borderTop: "1px solid var(--ink-700)", paddingTop: 16, fontSize: 13.5, color: "var(--text-secondary)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span>Predicted outcome</span>
                  <span className="mono" style={{ color: "var(--paper-50)" }}>{result.prediction}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span>Probability of full repayment</span>
                  <span className="mono" style={{ color: "var(--paper-50)" }}>
                    {(result.probability_of_full_repayment * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Model used</span>
                  <span className="badge badge--brass">{result.model_used}</span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
