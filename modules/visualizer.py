import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import Any, Dict

class AegisVisualizer:
    def __init__(self, balances: np.ndarray, inputs: Any):
        self.balances = balances
        self.inputs = inputs
        self.timeline = np.linspace(inputs.current_age, inputs.longevity_horizon, balances.shape[1])
        
    def create_confidence_fan(self):
        p5, p25, p50, p75, p95 = np.percentile(self.balances, [5, 25, 50, 75, 95], axis=0)
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.fill_between(self.timeline, p5, p95, color='gray', alpha=0.15, label="Extreme (5th-95th)")
        ax.fill_between(self.timeline, p25, p75, color='skyblue', alpha=0.4, label="Likely (25th-75th)")
        ax.plot(self.timeline, p50, color='#1A237E', lw=3, label="Median Path")
        ax.axvspan(self.inputs.retirement_age - 5, self.inputs.retirement_age + 5, color='orange', alpha=0.1, label="Fragile Decade")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))
        ax.set_title("Wealth Projection: Project Aegis", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        return fig

    def generate_actionable_summary(self) -> dict:
        retire_idx = (self.inputs.retirement_age - self.inputs.current_age) * 12
        return {
            "median_at_retirement": np.percentile(self.balances[:, retire_idx], 50),
            "median_ending_wealth": np.percentile(self.balances[:, -1], 50),
            "stress_test_wealth": np.percentile(self.balances[:, -1], 5)
        }

class SensitivityOptimizer:
    def __init__(self, engine):
        self.engine = engine

    def run_grid_search(self, ages, savings_steps):
        from modules.engine import StochasticEngine
        results = []
        for age in ages:
            row = {"Retirement Age": age}
            for extra in savings_steps:
                test_in = self.engine.inputs.copy(update={"retirement_age": age, "annual_contribution": self.engine.inputs.annual_contribution + extra})
                sim = StochasticEngine(test_in).run_simulation(trials=1000)
                row[f"+${extra//1000}k"] = sim["success_rate"]
            results.append(row)
        return pd.DataFrame(results).set_index("Retirement Age")