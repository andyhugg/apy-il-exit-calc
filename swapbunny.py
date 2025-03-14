import streamlit as st
import pandas as pd
import numpy as np

st.title("Altcoin vs. Bitcoin Drawdown Decision Tool")

# Inputs
st.header("Your Position")
initial_investment = st.number_input("Initial Altcoin Investment ($)", min_value=0.01, value=1000.0, step=10.0)
current_value = st.number_input("Current Altcoin Value ($)", min_value=0.0, value=200.0, step=10.0)
current_btc_price = st.number_input("Current Bitcoin Price ($)", min_value=0.01, value=60000.0, step=100.0)
total_fees = st.number_input("Total Swap Fees ($)", min_value=0.0, value=5.0, step=1.0, help="Swap + network fees")

st.header("Risk Tolerance")
risk_tolerance = st.slider("Max Additional Loss Willing to Take (%)", 0.0, 100.0, 20.0, step=1.0, help="From current value") / 100
max_loss = current_value * (1 - risk_tolerance)

st.header("Scenarios")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Altcoin Outcomes")
    altcoin_worst = st.number_input("Worst Case ($)", min_value=0.0, value=0.0, step=10.0)
    altcoin_base = st.number_input("Base Case ($)", min_value=0.0, value=400.0, step=10.0)
    altcoin_best = st.number_input("Best Case ($)", min_value=0.0, value=1000.0, step=10.0)
with col2:
    st.subheader("Bitcoin Outcomes (%)")
    btc_worst = st.number_input("Worst Case BTC (%)", value=-20.0, step=1.0) / 100
    btc_base = st.number_input("Base Case BTC (%)", value=20.0, step=1.0) / 100
    btc_best = st.number_input("Best Case BTC (%)", value=50.0, step=1.0) / 100

# Calculations
drawdown = (current_value - initial_investment) / initial_investment
net_swap_value = current_value - total_fees
btc_amount = net_swap_value / current_btc_price

btc_worst_value = btc_amount * current_btc_price * (1 + btc_worst)
btc_base_value = btc_amount * current_btc_price * (1 + btc_base)
btc_best_value = btc_amount * current_btc_price * (1 + btc_best)

# Decision Logic
altcoin_upside = (altcoin_best - current_value) / current_value
btc_upside = (btc_best_value - net_swap_value) / net_swap_value
risk_exposure = (current_value - altcoin_worst) / current_value  # Potential further loss

if risk_exposure > risk_tolerance and btc_worst_value > altcoin_worst:
    recommendation = "Swap to BTC: Protects against total loss and fits your risk tolerance."
elif altcoin_base > btc_base_value and altcoin_upside > btc_upside:
    recommendation = "Stay with Altcoin: Higher upside potential if recovery happens."
else:
    recommendation = "Neutral: Depends on your confidence in altcoin recovery vs. BTC stability."

# Results
st.header("Results")
st.write(f"**Initial Investment**: ${initial_investment:.2f}")
st.write(f"**Current Value**: ${current_value:.2f} (Drawdown: {drawdown:.2%})")
st.write(f"**Max Acceptable Loss**: ${max_loss:.2f} (based on {risk_tolerance:.0%} tolerance)")

st.subheader("Scenario Outcomes")
data = {
    "Scenario": ["Worst", "Base", "Best"],
    "Stay with Altcoin": [altcoin_worst, altcoin_base, altcoin_best],
    "Swap to BTC": [btc_worst_value, btc_base_value, btc_best_value]
}
df = pd.DataFrame(data)
st.table(df.style.format({"Stay with Altcoin": "${:.2f}", "Swap to BTC": "${:.2f}"}))

st.subheader("Recommendation")
st.write(recommendation)

# Sidebar
st.sidebar.header("How It Works")
st.sidebar.write("""
- Input your current loss and scenario estimates.
- Set your risk tolerance (max further loss you can handle).
- The tool compares outcomes and suggests staying or swapping based on risk and upside.
- Use realistic scenarios: altcoin could go to $0; BTC is more stable.
""")
