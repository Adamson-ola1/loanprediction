# Technical Report — Loan Default Prediction

## 1. Problem statement

Predict, at the time a loan application is submitted, the probability that
the loan will ultimately be **Charged Off** (default) rather than **Fully
Paid**. This is a binary classification problem trained on historical
LendingClub loan data (`data/raw/data.csv`, ~39.7k rows, 111 raw columns).

## 2. Data cleaning (`src/preprocess.py`)

1. **Filter to resolved loans.** Loans still `Current` have no final outcome
   and are dropped, leaving only `Fully Paid` / `Charged Off` rows (38,577 of
   39,717).
2. **Remove duplicates.** None found in this dataset.
3. **Drop irrelevant / leakage / constant columns** (89 columns dropped):
   - *Identifiers & free text*: `id`, `member_id`, `url`, `desc`, `emp_title`, `title`, `zip_code` — no predictive signal.
   - *Outcome leakage*: `funded_amnt`, `funded_amnt_inv`, `out_prncp*`, `total_pymnt*`, `total_rec_*`, `recoveries`, `collection_recovery_fee`, `last_pymnt_*`, `next_pymnt_d`, `last_credit_pull_d`, `collections_12_mths_ex_med` — only known *after* the loan is resolved, so keeping them would let the model "see the future" (this was a bug found and fixed during EDA: earlier versions scored ~1.0 AUC because of exactly this leakage).
   - *Constant columns*: 65 columns with a single unique value (e.g. `policy_code`, `application_type`) carry no signal and are dropped automatically.
4. **Missing values.**
   - `mths_since_last_delinq` / `mths_since_last_record` are missing precisely when a borrower has no recorded delinquency/public record — that absence is itself informative, so a `has_*` indicator column is created *before* imputing.
   - Columns still >50% missing after that (e.g. `mths_since_last_record`) are dropped.
   - Remaining numeric gaps → median imputation; categorical gaps → mode imputation.
5. **Type conversion.** Dates (`issue_d`, `earliest_cr_line`) parsed from `"Mon-YY"`; percentage strings (`int_rate`, `revol_util`) stripped of `%` and cast to float; `term` (`" 36 months"`) parsed to integer months.
6. **Outlier treatment (IQR method)** on `annual_inc`, `loan_amnt`, `dti`, `int_rate` — rows outside `[Q1 - 1.5·IQR, Q3 + 1.5·IQR]` removed.
7. **Standardize categorical text** — lowercase + strip whitespace.
8. **Invalid value check** — drop any rows with negative income/amount/rate/dti.

Final cleaned shape: **36,198 rows × 27 columns.**

## 3. Exploratory Data Analysis

Key findings mirrored from `notebooks/exploration.ipynb` (charts saved to `charts/` and `outputs/plots/`):

- **Class imbalance**: ~85% Fully Paid vs. ~15% Charged Off — models are trained with class weighting (`class_weight="balanced"` / `scale_pos_weight`) to compensate.
- **Annual income**: borrowers who default tend to report lower annual income.
- **Employment length**: longer employment history is loosely associated with a slightly higher repayment rate, though the effect is modest.
- **Home ownership**: renters default somewhat more often than mortgage-holders/owners.
- **Loan grade**: strongly monotonic — worse grades (E/F/G) default far more often than A/B grades, as expected since grade already encodes LendingClub's own risk assessment.
- **Interest rate**: higher rates correlate with higher default rates (rate is itself a function of grade/risk).
- **Loan purpose & state**: default rates vary by purpose (e.g. small_business is riskier than debt_consolidation) and by state, though sample sizes vary widely.

## 4. Feature engineering (`src/feature_engineering.py`)

| Feature | Description |
|---|---|
| `loan_status` (target) | `fully paid` → 0, `charged off` → 1 |
| `emp_length_years` | Employment length string mapped to 0–10 |
| `employment_category` | Bucketed: New (≤2y) / Mid (≤6y) / Experienced (≤10y) |
| `credit_history_years` | `issue_d.year − earliest_cr_line.year`, clipped ≥ 0 |
| `loan_income_ratio` | `loan_amnt / annual_inc` |
| `monthly_income` | `annual_inc / 12` |
| `income_category` | Low / Medium / High via tercile `qcut` on `annual_inc` (bin edges persisted to `models/income_bins.pkl` for consistent inference) |
| `issue_year`, `issue_month` | Extracted from `issue_d` |

Final feature set used for modeling — **23 numeric + 8 categorical = 31 features**, all knowable at application time (see `config.NUMERIC_FEATURES` / `config.CATEGORICAL_FEATURES`).

## 5. Modeling (`src/train.py`)

- **Split**: 80/20 stratified train/test split, `random_state=42`.
- **Preprocessing** (fit only on the training set, inside one `sklearn.Pipeline` per model, to prevent any leakage from test/inference data into training):
  - Numeric: median imputation → `StandardScaler`
  - Categorical: mode imputation → `OneHotEncoder(handle_unknown="ignore")`
- **Models compared**:
  - Logistic Regression (`class_weight="balanced"`)
  - Random Forest (`n_estimators=200, max_depth=12, min_samples_leaf=20, class_weight="balanced_subsample"`)
  - XGBoost (`n_estimators=300, scale_pos_weight=neg/pos`)
- **Model selection**: best model chosen by ROC AUC on the held-out test set; all three are saved individually (`models/<Model>.pkl`), and the winner is also saved as `models/trained_model.pkl`.

## 6. Evaluation (`src/evaluate.py`)

For each model: accuracy, precision, recall, F1, ROC AUC, confusion matrix, ROC curve, and a classification report are computed and saved to `outputs/` (`metrics.json`, `model_report.csv`, `*_classification_report.txt`) and charted to `outputs/plots/` + `charts/` (confusion matrices, ROC curves, and a bar-chart model comparison). Predictions on the held-out test set are saved to `outputs/predictions.csv`.

Typical held-out ROC AUC values are in the **0.65–0.70** range across the three models — modest but expected: predicting default from application-time information alone (with `grade`/`sub_grade` as by far the strongest signal, since they already encode LendingClub's own underwriting) is a genuinely hard problem once all post-outcome leakage is removed.

## 7. Inference (`src/predict.py`)

`LoanDefaultPredictor` replicates the exact feature-engineering steps above for a single raw application dict (or a batch via `--batch`), then calls the saved pipeline's `predict_proba`. This same class is used by the FastAPI backend (`backend/main.py`) so there is only one code path from raw input to prediction.

## 8. Automation

`airflow/dags/loan_pipeline_dag.py` orchestrates `check_new_data → preprocess → feature_engineering → train → evaluate → summarize` on a weekly schedule, so the model is retrained automatically as new data lands in `data/raw/data.csv`.
