import numpy as np
from pydantic import BaseModel, Field, validator
from typing import Dict, Any

class InputSchema(BaseModel):
    initial_capital: float = Field(..., gt=0)
    asset_weights: Dict[str, float]
    annual_contribution: float = Field(default=0.0)
    annual_withdrawal: float = Field(default=0.0)
    current_age: int = Field(..., ge=18)
    retirement_age: int = Field(..., ge=18)
    longevity_horizon: int = Field(default=95)
    ss_pia_amount: float = Field(default=35000.0)
    ss_take_age: int = Field(default=67)
    other_side_income: float = Field(default=0.0)
    market_sentiment: str = Field(default="Average")

    @validator('asset_weights')
    def weights_must_sum_to_one(cls, v):
        if not np.isclose(sum(v.values()), 1.0):
            raise ValueError("Asset weights must sum to exactly 1.0")
        return v

class StochasticEngine:
    def __init__(self, inputs: InputSchema, nu: int = 5):
        self.inputs = inputs
        self.nu = nu
        self.months = (inputs.longevity_horizon - inputs.current_age) * 12
        self.retire_month_idx = (inputs.retirement_age - inputs.current_age) * 12

    def _get_ss_multiplier(self):
        age = self.inputs.ss_take_age
        if age <= 62: return 0.70
        if age >= 70: return 1.24
        if age < 67: return 0.70 + (age - 62) * (0.30/5)
        return 1.0 + (age - 67) * 0.08

    def run_simulation(self, regime: str = "Steady Path", trials: int = 10000):
        # Base regime data
        regimes = {
            "Steady Path": {"equities": {"mu": 0.09, "sigma": 0.18}, "bonds": {"mu": 0.04, "sigma": 0.07}},
            "1970s Remix": {"equities": {"mu": 0.06, "sigma": 0.25}, "bonds": {"mu": 0.03, "sigma": 0.12}}
        }
        data = regimes.get(regime, regimes["Steady Path"])
        
        # Sentiment adjustment
        sentiment_map = {"Significantly Above Average": 0.04, "Above Average": 0.02, "Average": 0.0, "Below Average": -0.02, "Significantly Below Average": -0.04}
        p_mu = sum(self.inputs.asset_weights[a] * data[a]["mu"] for a in self.inputs.asset_weights) + sentiment_map.get(self.inputs.market_sentiment, 0)
        p_sigma = np.sqrt(sum((self.inputs.asset_weights[a] * data[a]["sigma"])**2 for a in self.inputs.asset_weights))
        
        # Monthly conversion
        m_mu, m_sigma = p_mu / 12, p_sigma / np.sqrt(12)
        
        balances = np.zeros((trials, self.months + 1))
        balances[:, 0] = self.inputs.initial_capital
        ss_monthly = (self.inputs.ss_pia_amount * self._get_ss_multiplier()) / 12
        ss_start_m = (self.inputs.ss_take_age - self.inputs.current_age) * 12

        for t in range(self.months):
            returns = m_mu + m_sigma * np.random.standard_t(df=self.nu, size=trials)
            flow = (self.inputs.annual_contribution / 12) if t < self.retire_month_idx else -(self.inputs.annual_withdrawal / 12)
            if t >= ss_start_m: flow += ss_monthly
            flow += (self.inputs.other_side_income / 12)
            balances[:, t+1] = (balances[:, t] + flow) * (1 + returns)

        sr = np.mean(np.all(balances > 0, axis=1))
        return {"balances": balances, "success_rate": sr, "status": "GREEN" if sr > 0.9 else "YELLOW" if sr > 0.75 else "RED"}