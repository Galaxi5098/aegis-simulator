import streamlit as st
import pandas as pd
from modules.engine import InputSchema, StochasticEngine
from modules.visualizer import AegisVisualizer, SensitivityOptimizer
from modules.reporter import NarrativeReporter, ReportGenerator

st.set_page_config(page_title="Project Aegis", layout="wide", page_icon="🛡️")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Core Portfolio")
    initial_cap = st.number_input("Portfolio Value ($)", value=400000, step=10000, help="Your total assets today.")
    curr_age = st.slider("Current Age", 18, 80, 48)
    retire_age = st.slider("Retirement Age", curr_age + 1, 90, 70)
    
    st.header("2. Income & Spending")
    annual_cont = st.number_input("Annual Savings ($)", value=25000, help="Amount saved per year until retirement.")
    annual_draw = st.number_input("Retirement Spending ($)", value=80000, help="Annual budget in retirement.")
    ss_amt = st.number_input("Full SS Benefit (Age 67)", value=35000)
    ss_age = st.select_slider("SS Start Age", options=range(62, 71), value=67)
    side_inc = st.number_input("Additional Income ($)", value=0)
    
    st.header("3. Market Forecast")
    equity_perc = st.slider("Equity %", 0, 100, 80)
    regime = st.selectbox("Market Regime", ["Steady Path", "1970s Remix"])
    sentiment = st.selectbox("Sentiment", ["Significantly Above Average", "Above Average", "Average", "Below Average", "Significantly Below Average"], index=2)

# --- EXECUTION ---
inputs = InputSchema(
    initial_capital=initial_cap, asset_weights={"equities": equity_perc/100, "bonds": (100-equity_perc)/100},
    annual_contribution=annual_cont, annual_withdrawal=annual_draw,
    current_age=curr_age, retirement_age=retire_age,
    ss_pia_amount=ss_amt, ss_take_age=ss_age, other_side_income=side_inc, market_sentiment=sentiment
)
results = StochasticEngine(inputs).run_simulation(regime=regime)
viz = AegisVisualizer(results["balances"], inputs)
summary = viz.generate_actionable_summary()

# --- STATUS BANNER ---
status_cfg = {"GREEN": ("#d4edda", "#155724", "SECURE"), "YELLOW": ("#fff3cd", "#856404", "CAUTION"), "RED": ("#f8d7da", "#721c24", "CRITICAL")}
bg, txt, lbl = status_cfg[results['status']]
st.markdown(f'''
    <div style="background-color:{bg}; padding:20px; border-radius:10px; border: 2px solid {txt};">
        <h2 style="color:{txt}; margin:0;">Status: {lbl} ({results["success_rate"]*100:.1f}%)</h2>
    </div>
    ''', unsafe_allow_html=True)

# --- DASHBOARD ---
st.write("---")
c1, c2, c3 = st.columns(3)
with c1: st.metric("Wealth AT Retirement", f"${summary['median_at_retirement']/1e6:.2f}M")
with c2: st.metric("Wealth AT Age 95", f"${summary['median_ending_wealth']/1e6:.2f}M")
with c3: st.metric("Stress Test Floor", f"${summary['stress_test_wealth']/1e6:.2f}M")

st.pyplot(viz.create_confidence_fan())
st.divider()
st.write(NarrativeReporter.get_summary(results, inputs))

with st.expander(f"🔍 Optimization Matrix: The Path to {lbl}"):
    st.markdown("Colors represent Success Probability: **Green (>90%)**, **Yellow (75-90%)**, **Red (<75%)**.")
    grid = SensitivityOptimizer(StochasticEngine(inputs)).run_grid_search(range(retire_age, retire_age+6), [0, 5000, 10000, 15000])
    st.table(grid.style.format("{:.1%}").background_gradient(cmap="RdYlGn", axis=None))