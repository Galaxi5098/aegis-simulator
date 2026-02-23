import streamlit as st
import pandas as pd
import json
import base64
from modules.engine import InputSchema, StochasticEngine
from modules.visualizer import AegisVisualizer, SensitivityOptimizer
from modules.reporter import NarrativeReporter, ReportGenerator

st.set_page_config(page_title="Project Aegis", layout="wide", page_icon="🛡️")

# --- SAVING/LOADING LOGIC ---
def get_aegis_code(inputs_dict):
    json_str = json.dumps(inputs_dict)
    return base64.b64encode(json_str.encode()).decode()

def decode_aegis_code(code):
    try:
        decoded = base64.b64decode(code).decode()
        return json.loads(decoded)
    except:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Aegis Command")
    load_code = st.text_input("Input Aegis Code to Load Strategy")
    loaded_data = decode_aegis_code(load_code) if load_code else None

    st.header("1. Core Portfolio")
    initial_cap = st.number_input("Portfolio Value ($)", value=loaded_data['initial_capital'] if loaded_data else 100000)
    curr_age = st.slider("Current Age", 18, 80, loaded_data['current_age'] if loaded_data else 48)
    retire_age = st.slider("Retirement Age", curr_age + 1, 90, loaded_data['retirement_age'] if loaded_data else 70)
    
    st.header("2. Income & Spending")
    annual_cont = st.number_input("Annual Savings ($)", value=loaded_data['annual_contribution'] if loaded_data else 25000)
    annual_draw = st.number_input("Retirement Spending ($)", value=loaded_data['annual_withdrawal'] if loaded_data else 80000)
    ss_amt = st.number_input("Full SS Benefit (Age 67)", value=loaded_data['ss_pia_amount'] if loaded_data else 35000)
    ss_age = st.select_slider("SS Start Age", options=range(62, 71), value=loaded_data['ss_take_age'] if loaded_data else 67)
    # DEFINING THIS HERE FIXES THE NAMEERROR
    side_inc = st.number_input("Additional Income ($)", value=0)
    
    st.header("3. Market Forecast")
    equity_perc = st.slider("Equity %", 0, 100, 80)
    regime = st.selectbox("Market Regime", ["Steady Path", "1970s Remix"])
    sentiment = st.selectbox("Sentiment", ["Significantly Above Average", "Above Average", "Average", "Below Average", "Significantly Below Average"], index=2)

    if st.button("Generate Aegis Code"):
        current_params = {
            "initial_capital": initial_cap, "current_age": curr_age, "retirement_age": retire_age,
            "annual_contribution": annual_cont, "annual_withdrawal": annual_draw,
            "ss_pia_amount": ss_amt, "ss_take_age": ss_age
        }
        st.code(get_aegis_code(current_params), language="text")

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
st.markdown(f'''<div style="background-color:{bg}; padding:20px; border-radius:10px; border: 2px solid {txt};"><h2 style="color:{txt}; margin:0;">Status: {lbl} ({results["success_rate"]*100:.1f}%)</h2></div>''', unsafe_allow_html=True)

# --- DASHBOARD ---
st.write("---")
c1, c2, c3 = st.columns(3)
with c1: st.metric("Wealth AT Retirement", f"${summary['median_at_retirement']/1e6:.2f}M")
with c2: st.metric("Wealth AT Age 95", f"${summary['median_ending_wealth']/1e6:.2f}M")
with c3: st.metric("Stress Test Floor", f"${summary['stress_test_wealth']/1e6:.2f}M")

st.pyplot(viz.create_confidence_fan())
st.divider()
st.write(NarrativeReporter.get_summary(results, inputs))