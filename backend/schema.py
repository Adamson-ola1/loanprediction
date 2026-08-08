"""
backend/schema.py
==================
Pydantic request/response models for the Loan Default Prediction API.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LoanApplication(BaseModel):
    """Raw loan application fields — everything known at application time."""

    loan_amnt: float = Field(..., gt=0, description="Requested loan amount", examples=[12000])
    term: str = Field("6 months", description="'6 months' or '12 months'", examples=["6 months"])
    int_rate: str | float = Field(..., description="Interest rate, e.g. '13.5%' or 13.5", examples=["13.5%"])
    installment: float = Field(..., gt=0, description="Monthly installment amount")
    annual_inc: float = Field(..., ge=0, description="Self-reported annual income")
    dti: float = Field(..., ge=0, description="Debt-to-income ratio")
    delinq_2yrs: float = Field(0, ge=0, description="Delinquencies in the last 2 years")
    inq_last_6mths: float = Field(0, ge=0, description="Credit inquiries in the last 6 months")
    open_acc: float = Field(0, ge=0, description="Number of open credit lines")
    pub_rec: float = Field(0, ge=0, description="Number of derogatory public records")
    revol_bal: float = Field(0, ge=0, description="Total revolving credit balance")
    revol_util: str | float = Field(0, description="Revolving line utilization rate, e.g. '45%' or 45")
    total_acc: float = Field(0, ge=0, description="Total number of credit lines")
    pub_rec_bankruptcies: float = Field(0, ge=0, description="Number of public record bankruptcies")
    mths_since_last_delinq: Optional[float] = Field(None, description="Months since last delinquency (blank if none)")
    mths_since_last_record: Optional[float] = Field(None, description="Months since last public record (blank if none)")
    emp_length: str = Field("5 years", description="Employment length, e.g. '< 1 year' .. '10+ years'")
    grade: str = Field("C", description="LendingClub assigned loan grade, A-G")
    sub_grade: str = Field("C2", description="LendingClub assigned loan sub-grade")
    home_ownership: str = Field("RENT", description="RENT / OWN / MORTGAGE / OTHER")
    verification_status: str = Field("Verified", description="Verified / Source Verified / Not Verified")
    purpose: str = Field("debt_consolidation", description="Loan purpose category")
    addr_state: str = Field("CA", description="Two-letter US state code")
    issue_d: Optional[str] = Field(None, description="Issue date, e.g. 'Dec-11' (defaults to today)")
    earliest_cr_line: Optional[str] = Field(None, description="Earliest credit line date, e.g. 'Jan-01'")

    @field_validator("term")
    @classmethod
    def validate_term(cls, v: str) -> str:
        digits = "".join(ch for ch in str(v) if ch.isdigit())
        if digits not in ("6", "12", "18", "24", "30", "36", "42", "48", "54", "60"):
            raise ValueError("term must contain 6, 12 ... 60 months")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "loan_amnt": 12000,
                "term": "18 months",
                "int_rate": "13.5%",
                "installment": 407.5,
                "annual_inc": 55000,
                "dti": 18.2,
                "delinq_2yrs": 0,
                "inq_last_6mths": 1,
                "open_acc": 9,
                "pub_rec": 0,
                "revol_bal": 8000,
                "revol_util": "45%",
                "total_acc": 22,
                "pub_rec_bankruptcies": 0,
                "grade": "C",
                "sub_grade": "C2",
                "home_ownership": "RENT",
                "verification_status": "Verified",
                "purpose": "debt_consolidation",
                "addr_state": "CA",
                "emp_length": "5 years",
                "issue_d": "Dec-11",
                "earliest_cr_line": "Jan-01",
            }
        }
    }


class PredictionResponse(BaseModel):
    prediction: str = Field(..., description="'Fully Paid' or 'Charged Off'")
    probability_of_default: float = Field(..., ge=0, le=1)
    probability_of_full_repayment: float = Field(..., ge=0, le=1)
    model_used: str


class BatchPredictionRequest(BaseModel):
    applications: list[LoanApplication]


class BatchPredictionResponse(BaseModel):
    results: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str


class ModelInfoResponse(BaseModel):
    best_model: str
    metrics: dict
    feature_count: int
    numeric_features: list[str]
    categorical_features: list[str]
