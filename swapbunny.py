import streamlit as st
import numpy as np

# APY calculation with safety checks
def calculate_apy(prices, fees, days):
    if len(prices) < 2 or days < 1:
        return 0.0  # Return 0 if insufficient data
    daily_returns = (prices[1:] / prices[:-1]) - 1 + fees
    compounded_return = np.prod(1 + daily_returns)
    if compounded_return <= 0:
        return 0.0  # Avoid negative or invalid APY
    apy = (compounded_return ** (365 / (days - 1))) - 1
    return apy

# IL calculation with safety checks
def calculate_impermanent_loss(price_change):
    if price_change <= 0:
        return 0.0  # Invalid price change
    return 2 * np.sqrt(price_change) / (1 + price_change) - 1

# Streamlit UI
st.title("SwapBunny APY and IL Calculator")

st.header("Input Parameters")
initial_price = st.number_input("Initial Price", min_value=0.01, value=1.0, step=0.1)
final_price = st.number_input("Final Price", min_value=0.01, value=1.0, step=0.1)
daily_fee = st.number_input("Daily Fee (as decimal, e.g., 0.003 for 0.3%)", min_value=0.0, value=0.003, step=0.0001)
days = st.number_input("Number of Days", min_value=2, value=30, step=1)

# Calculate intermediate values
try:
    price_change = final_price / initial_price
    prices = np.linspace(initial_price, final_price, days)
    fees = np.full(days - 1, daily_fee)

    # Calculate APY and IL
    apy = calculate_apy(prices, fees, days)
    il = calculate_impermanent_loss(price_change)

    # Display results
    st.header("Results")
    st.write(f"APY: {apy:.2%}")
    st.write(f"Impermanent Loss: {il:.2%}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}. Please check your inputs and try again.")

# Add some helpful info
st.sidebar.header("About")
st.sidebar.write("""
This tool calculates the Annual Percentage Yield (APY) and Impermanent Loss (IL) for a liquidity pool.
- **APY**: Based on price changes and daily fees, compounded over a year.
- **IL**: Loss due to price divergence compared to holding assets.
""")
