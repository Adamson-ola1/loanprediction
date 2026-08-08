# Model Card — Loan Default Predictor

## Model details
- **Task**: Binary classification — predict whether a loan will be `Charged Off` (1) vs. `Fully Paid` (0).
- **Champion model**: Logistic Regression (`class_weight="balanced"`), selected by highest ROC AUC on a held-out test set among three candidates.
- **Candidates trained**: Logistic Regression, Random Forest, XGBoost — all wrapped in a single `sklearn.Pipeline` (median/mode imputation → scaling/one-hot-encoding → classifier).
- **Version**: 1.0.0
- **Training code**: `src/train.py`; feature engineering: `src/feature_engineering.py`; inference: `src/predict.py`.
- **Training data**: LendingClub historical loan data, cleaned to 36,198 resolved loans (Fully Paid / Charged Off), 80/20 stratified train/test split.

## Intended use
- **Primary use case**: Decision-support for loan underwriting — estimate default risk *at application time*, using only information a lender would have before approving a loan (no post-issuance payment history).
- **Intended users**: Data science / risk teams evaluating or prototyping credit-risk models; not intended as a sole, automated approve/deny system.
- **Out of scope**: Should not be used as the sole basis for adverse lending decisions (e.g. automatic denial) without human review, fair-lending compliance checks, and validation against current underwriting policy and applicable regulation (e.g. ECOA, Regulation B, local fair-lending law).

## Training data & features
23 numeric + 8 categorical features, all knowable at application time: loan terms (`loan_amnt`, `term`, `int_rate`, `installment`, `grade`, `sub_grade`), borrower profile (`emp_length_years`, `employment_category`, `home_ownership`, `annual_inc`, `verification_status`), loan context (`purpose`, `addr_state`, `dti`), credit history (`delinq_2yrs`, `inq_last_6mths`, `open_acc`, `pub_rec`, `revol_bal`, `revol_util`, `total_acc`, `pub_rec_bankruptcies`, `credit_history_years`, missing-value indicators), and derived ratios (`loan_income_ratio`, `monthly_income`, `income_category`, `issue_year`, `issue_month`). See `docs/technical_report.md` for full definitions.

All post-outcome / payment-history columns (e.g. `total_pymnt`, `recoveries`, `last_pymnt_d`) were deliberately excluded — see the "leakage" note in the technical report.

## Performance (held-out test set, n=7,240)

| Model | Accuracy | Precision | Recall | F1 | ROC AUC |
|---|---|---|---|---|---|
| **Logistic Regression (champion)** | 0.646 | 0.235 | 0.643 | 0.345 | **0.702** |
| Random Forest | 0.681 | 0.248 | 0.592 | 0.349 | 0.698 |
| XGBoost | 0.784 | 0.261 | 0.266 | 0.263 | 0.652 |

*(Regenerate exact numbers with `python main.py --stage evaluate`; see `outputs/metrics.json` for the live values and `outputs/plots/` / `charts/` for confusion matrices and ROC curves.)*

Precision for the "Charged Off" class is low (~0.24–0.26) because the target is imbalanced (~15% default rate) and class weighting is tuned to prioritize recall (catching defaulters) over precision. In practice, the **predicted probability** should be used as a continuous risk score (e.g. for risk-based pricing or tiered review) rather than the binary 0.5-threshold label.

## Limitations
- **Modest discrimination**: ROC AUC ~0.70 means the model is meaningfully better than random but far from perfect — a large share of variance in loan outcomes (e.g. macroeconomic shocks, life events) simply isn't captured in application-time data.
- **Historical data**: Trained on a historical LendingClub snapshot; underwriting standards, macroeconomic conditions, and applicant populations change over time, so periodic retraining (see the Airflow DAG) and monitoring for drift are essential.
- **Grade dependency**: `grade`/`sub_grade` are strong predictors because they already encode a prior human/automated underwriting decision — the model partially re-derives LendingClub's own risk tiering rather than discovering fully independent signal.
- **Imbalanced classes**: Low precision on the minority (default) class; threshold and class-weighting choices should be revisited for any specific deployment (e.g. cost-sensitive threshold tuning).

## Ethical considerations & fairness
- `addr_state` is included as a feature; geography can correlate with protected characteristics (e.g. race, national origin) via historical redlining patterns. Any production use should include a fair-lending disparate-impact analysis across protected classes before deployment, and should consult legal/compliance teams.
- The model does not use directly protected attributes (race, gender, age, etc.), but proxy variables (state, employment length, home ownership) can still correlate with them — bias testing is recommended before any real-world lending decision relies on this model.
- This model card and the underlying code are provided for educational / prototyping purposes and are not a certified, compliance-ready credit model.

## Maintenance
- Retrained automatically via `airflow/dags/loan_pipeline_dag.py` on a weekly schedule (configurable).
- All artifacts (models, metrics, plots) are versioned by re-running `python main.py`; consider adding a model registry (e.g. MLflow) for production use.
