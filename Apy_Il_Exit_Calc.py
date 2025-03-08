import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# APY vs IL Exit Calculator
def calculate_il(initial_price_asset1: float, initial_price_asset2: float, current_price_asset1: float, current_price_asset2: float) -> float:
    """
    Calculates Impermanent Loss (IL) based on initial and current asset prices.
    """
    price_ratio_initial = initial_price_asset1 / initial_price_asset2
    price_ratio_current = current_price_asset1 / current_price_asset2
    
    sqrt_ratio = (price_ratio_current / price_ratio_initial) ** 0.5
    il = 2 * (sqrt_ratio / (1 + sqrt_ratio)) - 1
    
    return abs(il) * 100  # Convert to percentage

def check_exit_conditions(apy: float, il: float):
    """
    Determines if IL is overtaking APY and suggests exit conditions.
    """
    apy_decimal = apy / 100
    il_decimal = il / 100
    
    net_return = (1 + apy_decimal) - (1 - il_decimal)
    apy_exit_threshold = il * 12  # IL spread over 12 months
    
    st.subheader("Results:")
    st.write(f"**Impermanent Loss:** {il:.2f}%")
    st.write(f"**Net Return:** {net_return:.2f}x")
    st.write(f"**APY Exit Threshold:** {apy_exit_threshold:.2f}%")
    
    break_even_months = float('inf')  # Default value in case APY is above the threshold
    
    if apy < apy_exit_threshold:
        break_even_months = il / (apy / 12) if apy > 0 else float('inf')
        st.warning(f"APY is below the IL threshold! Consider exiting.")
        st.write(f"**Break-even Duration:** {break_even_months:.2f} months")
    else:
        st.success("You're still in profit. No need to exit yet.")
    
    return break_even_months

# Streamlit App UI
st.title("APY vs IL Exit Calculator")

st.sidebar.header("Set Your Parameters")
initial_price_asset1 = st.sidebar.number_input("Initial Asset 1 Price", value=86000)
initial_price_asset2 = st.sidebar.number_input("Initial Asset 2 Price", value=1)  # Default to stablecoin
current_price_asset1 = st.sidebar.number_input("Current Asset 1 Price", value=180000)
current_price_asset2 = st.sidebar.number_input("Current Asset 2 Price", value=1)  # Default to stablecoin
apy = st.sidebar.number_input("Current APY (%)", value=340)

if st.sidebar.button("Calculate"):
    il = calculate_il(initial_price_asset1, initial_price_asset2, current_price_asset1, current_price_asset2)
    break_even_months = check_exit_conditions(apy, il)
    
    # Generate Break-even Duration vs. APY Chart
    st.subheader("Break-even Duration for Different APY Levels")
    apy_values = np.linspace(10, 500, 50)  # Generate APY values from 10% to 500%
    break_even_durations = [il / (apy_val / 12) if apy_val > 0 else float('inf') for apy_val in apy_values]
    
    fig, ax = plt.subplots()
    ax.plot(apy_values, break_even_durations, label="Break-even Duration (months)", color='blue')
    ax.axhline(y=break_even_months, color='red', linestyle='--', label="Current Break-even")
    ax.axvline(x=apy, color='green', linestyle='--', label="Current APY")
    ax.set_xlabel("APY (%)")
    ax.set_ylabel("Break-even Duration (Months)")
    ax.set_title("Break-even Duration vs. APY")
    ax.legend()
    st.pyplot(fig)
