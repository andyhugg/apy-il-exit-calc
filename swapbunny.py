import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit UI
st.title("Altcoin vs. Bitcoin Swap Calculator")

# Layout with columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Position")
    initial_altcoin_price = st.number_input("Initial Altcoin Price ($)", min_value=0.01, value=100.0, step=0.1)
    current_altcoin_price = st.number_input("Current Altcoin Price ($)", min_value=0.01, value=60.0, step=0.1)
    current_btc_price = st.number_input("Current Bitcoin Price ($)", min_value=0.01, value=60000.0, step=100.0)
    altcoin_amount = st.number_input("Amount of Altcoin Owned", min_value=0.01, value=10.0, step=0.1)

with col2:
    st.subheader("Future Expectations")
    time_period = st.number_input("Time Period (months)", min_value=1, value=6, step=1)
    altcoin_return = st.number_input("Estimated Altcoin Return (%)", value=30.0, step=1.0, help="Expected growth/loss") / 100
    btc_return = st.number_input("Estimated Bitcoin Return (%)", value=20.0, step=1.0, help="Expected growth/loss") / 100

# Transaction Fees Section
st.subheader("Transaction Fees")
swap_fee_pct = st.number_input("Swap Fee (%)", min_value=0.0, max_value=10.0, value=0.5, step=0.1, help="Exchange fee for swapping") / 100
altcoin_network_fee = st.number_input("Altcoin Network Fee ($)", min_value=0.0, value=1.0, step=0.1, help="Fee to send altcoin to swap")
btc_network_fee = st.number_input("Bitcoin Network Fee ($)", min_value=0.0, value=3.0, step=0.1, help="Fee to withdraw BTC")

# Calculations
initial_value = altcoin_amount * initial_altcoin_price
current_value = altcoin_amount * current_altcoin_price
drawdown = (current_value - initial_value) / initial_value

# Future value if holding altcoin (subtract network fee for fairness)
future_altcoin_value = current_value * (1 + altcoin_return) - altcoin_network_fee

# Future value if swapping to Bitcoin (with fees)
swap_fee = current_value * swap_fee_pct
net_swap_value = current_value - swap_fee - altcoin_network_fee  # Subtract altcoin fee to send to swap
btc_amount = net_swap_value / current_btc_price
future_btc_value = (btc_amount * current_btc_price * (1 + btc_return)) - btc_network_fee  # Subtract BTC withdrawal fee

# Break-even altcoin return
break_even_altcoin_return = ((future_btc_value + altcoin_network_fee) / current_value) - 1

# Decision logic
threshold = st.slider("Outperformance Threshold (%)", 0.0, 20.0, 5.0, step=0.1, help="Minimum advantage to justify swapping") / 100
difference = future_altcoin_value - future_btc_value
relative_diff = difference / current_value
recommendation = "Hold Altcoin" if relative_diff > threshold else "Swap to Bitcoin"

# Results
st.header("Results")
st.write(f"**Current Portfolio Value**: ${current_value:.2f} (Drawdown: {drawdown:.2%})")
st.write(f"**Future Value (Hold Altcoin, after ${altcoin_network_fee:.2f} fee)**: ${future_altcoin_value:.2f}")
st.write(f"**Future Value (Swap to BTC, after ${swap_fee:.2f} swap + ${altcoin_network_fee + btc_network_fee:.2f} fees)**: ${future_btc_value:.2f}")
st.write(f"**Difference (Altcoin - BTC)**: ${difference:.2f} ({relative_diff:.2%})")
st.write(f"**Break-Even Altcoin Return**: {break_even_altcoin_return:.2%} (to match BTC outcome)")
st.subheader(f"Recommendation: {recommendation}")

# Visualization
st.subheader("Portfolio Value Over Time")
time_points = np.linspace(0, time_period, 100)
altcoin_growth = [current_value * (1 + altcoin_return * (t / time_period)) - altcoin_network_fee for t in time_points]
btc_growth = [(net_swap_value * (1 + btc_return * (t / time_period)) / (1 + btc_return)) - btc_network_fee for t in time_points]  # Adjust for fee timing

df = pd.DataFrame({
    "Time (Months)": time_points,
    "Hold Altcoin": altcoin_growth,
    "Swap to BTC": btc_growth
})
st.line_chart(df.set_index("Time (Months)"))

# Sidebar
st.sidebar.header("How It Works")
st.sidebar.write("""
- Enter your position, expected returns, and estimated fees.
- Fees include swap cost (%), altcoin send fee, and BTC withdrawal fee.
- The app compares net future values and recommends holding or swapping.
- Check your wallet/exchange for current fee estimates.
""")
