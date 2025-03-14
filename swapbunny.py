import streamlit as st
import pandas as pd
import numpy as np

# Session state for reset
if 'reset' not in st.session_state:
    st.session_state.reset = False

st.title("Altcoin vs. Bitcoin Drawdown Decision Tool with Portfolio Impact")

# Clear Values Button
if st.button("Clear Values"):
    st.session_state.reset = True
    for key in list(st.session_state.keys()):
        if key != 'reset':
            del st.session_state[key]
    st.session_state.reset = False
    st.rerun()

# Inputs
st.header("Your Position")
initial_investment = st.number_input("Initial Altcoin Investment ($)", min_value=0.01, value=1000.0, step=10.0)
current_value = st.number_input("Current Altcoin Value ($)", min_value=0.0, value=200.0, step=10.0)
current_btc_price = st.number_input("Current Bitcoin Price ($)", min_value=0.01, value=60000.0, step=100.0)
total_fees = st.number_input("Total Swap Fees ($)", min_value=0.0, value=5.0, step=1.0, help="Swap + network fees")

st.header("Portfolio Context")
total_portfolio_value = st.number_input("Total Portfolio Value ($)", min_value=current_value, value=10000.0, step=100.0, help="Including this altcoin")

st.header("Risk Tolerance")
risk_tolerance = st.slider("Max Additional Loss Willing to Take (%)", 0.0, 100.0, 20.0, step=1.0, help="From current value") / 100
max_loss = current_value * (1 - risk_tolerance)

st.header("Scenarios and Probabilities")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Altcoin Outcomes ($)")
    altcoin_worst = st.number_input("Worst Case ($)", min_value=0.0, value=0.0, step=10.0, key="alt_worst")
    altcoin_base = st.number_input("Base Case ($)", min_value=0.0, value=400.0, step=10.0, key="alt_base")
    altcoin_best = st.number_input("Best Case ($)", min_value=0.0, value=1000.0, step=10.0, key="alt_best")
    st.subheader("Altcoin Probabilities (%)")
    alt_prob_worst = st.slider("Worst Case Probability", 0.0, 100.0, 50.0, key="alt_prob_worst") / 100
    alt_prob_base = st.slider("Base Case Probability", 0.0, 100.0, 30.0, key="alt_prob_base") / 100
    alt_prob_best = st.slider("Best Case Probability", 0.0, 100.0, 20.0, key="alt_prob_best") / 100
    if abs(alt_prob_worst + alt_prob_base + alt_prob_best - 1.0) > 0.01:
        st.error("Altcoin probabilities must sum to 100%")

with col2:
    st.subheader("Bitcoin Outcomes ($)")
    btc_worst_pct = st.number_input("Worst Case BTC (%)", value=-20.0, step=1.0, key="btc_worst") / 100
    btc_base_pct = st.number_input("Base Case BTC (%)", value=20.0, step=1.0, key="btc_base") / 100
    btc_best_pct = st.number_input("Best Case BTC (%)", value=50.0, step=1.0, key="btc_best") / 100
    st.subheader("Bitcoin Probabilities (%)")
    btc_prob_worst = st.slider("Worst Case Probability", 0.0, 100.0, 30.0, key="btc_prob_worst") / 100
    btc_prob_base = st.slider("Base Case Probability", 0.0, 100.0, 50.0, key="btc_prob_base") / 100
    btc_prob_best = st.slider("Best Case Probability", 0.0, 100.0, 20.0, key="btc_prob_best") / 100
    if abs(btc_prob_worst + btc_prob_base + btc_prob_best - 1.0) > 0.01:
        st.error("Bitcoin probabilities must sum to 100%")

# Calculations
drawdown = (current_value - initial_investment) / initial_investment
altcoin_allocation = current_value / total_portfolio_value
net_swap_value = current_value - total_fees
btc_amount = net_swap_value / current_btc_price

# Altcoin standalone outcomes
altcoin_outcomes = [altcoin_worst, altcoin_base, altcoin_best]

# BTC standalone outcomes
btc_worst_value = btc_amount * current_btc_price * (1 + btc_worst_pct)
btc_base_value = btc_amount * current_btc_price * (1 + btc_base_pct)
btc_best_value = btc_amount * current_btc_price * (1 + btc_best_pct)
btc_outcomes = [btc_worst_value, btc_base_value, btc_best_value]

# Expected Values
altcoin_expected = (alt_prob_worst * altcoin_worst) + (alt_prob_base * altcoin_base) + (alt_prob_best * altcoin_best)
btc_expected = (btc_prob_worst * btc_worst_value) + (btc_prob_base * btc_base_value) + (btc_prob_best * btc_best_value)

# Portfolio outcomes
portfolio_minus_altcoin = total_portfolio_value - current_value
portfolio_stay = [portfolio_minus_altcoin + x for x in altcoin_outcomes]
portfolio_swap = [portfolio_minus_altcoin + x for x in btc_outcomes]
portfolio_expected_stay = portfolio_minus_altcoin + altcoin_expected
portfolio_expected_swap = portfolio_minus_altcoin + btc_expected

# Portfolio impact
portfolio_drawdown_stay = [(x - total_portfolio_value) / total_portfolio_value for x in portfolio_stay]
portfolio_drawdown_swap = [(x - total_portfolio_value) / total_portfolio_value for x in portfolio_swap]
risk_exposure = (current_value - altcoin_worst) / total_portfolio_value  # Max further portfolio loss

# Decision Logic
if risk_exposure > (risk_tolerance * altcoin_allocation) and portfolio_swap[0] > portfolio_stay[0]:
    recommendation = f"Swap to BTC: Reduces portfolio risk (expected value ${portfolio_expected_swap:.2f} vs. ${portfolio_expected_stay:.2f})."
elif portfolio_expected_stay > portfolio_expected_swap and portfolio_stay[2] - portfolio_swap[2] > total_portfolio_value * 0.05:
    recommendation = f"Stay with Altcoin: Higher expected portfolio value (${portfolio_expected_stay:.2f} vs. ${portfolio_expected_swap:.2f})."
else:
    recommendation = f"Neutral: Expected values close (${portfolio_expected_stay:.2f} vs. ${portfolio_expected_swap:.2f}); weigh confidence in altcoin."

# Results
st.header("Results")
st.write(f"**Initial Altcoin Investment**: ${initial_investment:.2f}")
st.write(f"**Current Altcoin Value**: ${current_value:.2f} (Drawdown: {drawdown:.2%})")
st.write(f"**Portfolio Allocation to Altcoin**: {altcoin_allocation:.2%}")
st.write(f"**Max Acceptable Portfolio Loss from Altcoin**: {risk_tolerance * altcoin_allocation:.2%} (${max_loss:.2f})")
st.write(f"**Expected Altcoin Value**: ${altcoin_expected:.2f}")
st.write(f"**Expected BTC Value (after swap)**: ${btc_expected:.2f}")

st.subheader("Portfolio Outcomes")
data = {
    "Scenario": ["Worst", "Base", "Best"],
    "Stay with Altcoin ($)": portfolio_stay,
    "Swap to BTC ($)": portfolio_swap,
    "Stay Impact (%)": portfolio_drawdown_stay,
    "Swap Impact (%)": portfolio_drawdown_swap
}
df = pd.DataFrame(data)
st.table(df.style.format({
    "Stay with Altcoin ($)": "${:.2f}",
    "Swap to BTC ($)": "${:.2f}",
    "Stay Impact (%)": "{:.2%}",
    "Swap Impact (%)": "{:.2%}"
}))

st.subheader("Recommendation")
st.write(recommendation)

# Sidebar
st.sidebar.header("How It Works")
st.sidebar.write("""
- Input your altcoin loss, portfolio, scenarios, and probabilities.
- Probabilities must sum to 100% for each asset.
- Expected values weigh outcomes by likelihood.
- Portfolio impact shows total wealth effects.
- Use 'Clear Values' to reset.
""")
