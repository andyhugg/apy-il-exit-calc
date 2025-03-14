import streamlit as st
import matplotlib.pyplot as plt

# Title
st.title("Altcoin-to-Bitcoin Swap Calculator")

# Inputs
st.header("Inputs")
initial_price = st.number_input("Initial Purchase Price of Altcoin ($)", min_value=0.0, value=100.0)
current_price = st.number_input("Current Price of Altcoin ($)", min_value=0.0, value=60.0)
btc_return = st.number_input("Estimated Rate of Return for Bitcoin (%)", min_value=0.0, value=25.0) / 100
altcoin_return = st.number_input("Estimated Rate of Return for Altcoin (%)", min_value=0.0, value=20.0) / 100
time_period = st.number_input("Time Period (years)", min_value=0.0, value=1.0)
btc_risk = st.number_input("Risk Factor for Bitcoin (1 = low, 10 = high)", min_value=1, max_value=10, value=5)
altcoin_risk = st.number_input("Risk Factor for Altcoin (1 = low, 10 = high)", min_value=1, max_value=10, value=8)

# Calculations
# Future value of Bitcoin
future_btc_value = current_price * (1 + btc_return) ** time_period

# Future value of Altcoin
future_altcoin_value = current_price * (1 + altcoin_return) ** time_period

# Risk-adjusted returns
btc_risk_adjusted_return = (btc_return * 100) / btc_risk
altcoin_risk_adjusted_return = (altcoin_return * 100) / altcoin_risk

# Break-even return for Altcoin
break_even_return = ((future_btc_value / current_price) ** (1 / time_period) - 1) * 100

# Outputs
st.header("Results")

# Display future values
st.subheader("Future Values")
st.write(f"Future Value of Bitcoin: **${future_btc_value:.2f}**")
st.write(f"Future Value of Altcoin: **${future_altcoin_value:.2f}**")

# Display risk-adjusted returns
st.subheader("Risk-Adjusted Returns")
st.write(f"Bitcoin Risk-Adjusted Return: **{btc_risk_adjusted_return:.2f}%**")
st.write(f"Altcoin Risk-Adjusted Return: **{altcoin_risk_adjusted_return:.2f}%**")

# Break-even analysis
st.subheader("Break-Even Analysis")
st.write(f"To match Bitcoin's future value, the altcoin needs a return of **{break_even_return:.2f}%**
